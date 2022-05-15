"""Runs once during API startup and continues to run in a cron scheduler as per market hours."""

import inspect
import logging.config
import math
import os
import sys
import time
import warnings
from datetime import datetime

import jinja2
import requests
from pyrh import Robinhood

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
if parent_dir != os.getcwd():
    warnings.warn('Parent directory does not match the current working directory.\n'
                  f'Parent: {parent_dir}\n'
                  f'CWD: {os.getcwd()}')
sys.path.insert(0, parent_dir)

from api.rh_helper import CustomTemplate  # noqa
from modules.models import config, models  # noqa

env = models.env
fileio = models.FileIO()


class Investment:
    """Initiates ``Investment`` which gathers portfolio information.

    >>> Investment

    """

    def __init__(self, logger: logging.Logger):
        """Authenticates Robinhood object and gathers the portfolio information to store it in a variable.

        Args:
            logger: Takes the class ``logging.Logger`` as an argument.
        """
        rh = Robinhood()
        rh.login(username=env.robinhood_user, password=env.robinhood_pass, qr_code=env.robinhood_qr)
        raw_result = rh.positions()
        self.logger = logger
        self.result = raw_result['results']
        self.rh = rh

    def watcher(self) -> tuple:
        """Gathers all the information and wraps into parts of strings to create an HTML file.

        Returns:
            tuple:
            Returns a tuple of portfolio header, profit stat, loss stat, and current profit/loss compared to purchased.
        """
        shares_total, loss_dict, profit_dict = [], {}, {}
        n, n_ = 0, 0
        self.logger.info('Gathering portfolio.')
        for data in self.result:
            shares_count = int(data['quantity'].split('.')[0])
            if not shares_count:
                continue
            n += 1
            n_ += shares_count
            share_id = str(data['instrument'].split('/')[-2])
            raw_details = self.rh.get_quote(share_id)
            ticker = (raw_details['symbol'])
            stock_name = requests.get(raw_details['instrument']).json()['simple_name']
            buy = round(float(data['average_buy_price']), 2)
            total = round(shares_count * float(buy), 2)
            shares_total.append(total)
            current = round(float(raw_details['last_trade_price']), 2)
            current_total = round(shares_count * current, 2)
            difference = round(float(current_total - total), 2)
            if difference < 0:
                loss_dict[ticker] = [
                    -difference,
                    f'\n{stock_name}:\n{shares_count:,} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy:,} Currently: ${current:,}\n '
                    f'Total bought: ${total:,} Current Total: ${current_total:,}'
                    f'\nLOST ${-difference:,}\n'
                ]
            else:
                profit_dict[ticker] = [
                    difference,
                    f'\n{stock_name}:\n{shares_count:,} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy:,} Currently: ${current:,}\n'
                    f'Total bought: ${total:,} Current Total: ${current_total:,}'
                    f'\nGained ${difference:,}\n'
                ]

        profit_output, profit_total, loss_output, loss_total = "", [], "", []
        for key, value in sorted(profit_dict.items(), reverse=True, key=lambda item: item[1]):
            profit_output += value[1]
            profit_total.append(value[0])
        for key, value in sorted(loss_dict.items(), reverse=True, key=lambda item: item[1]):
            loss_output += value[1]
            loss_total.append(value[0])

        port_msg = f'\nTotal Profit: ${round(math.fsum(profit_total), 2):,}\n' \
                   f'Total Loss: ${round(math.fsum(loss_total), 2):,}\n\n' \
                   'The above values might differ from overall profit/loss if multiple shares ' \
                   'of the stock were purchased at different prices.'
        net_worth = round(float(self.rh.equity()), 2)
        output = f'Total number of stocks purchased: {n:,}\n'
        output += f'Total number of shares owned: {n_:,}\n'
        output += f'\nCurrent value of your total investment is: ${net_worth:,}'
        total_buy = round(math.fsum(shares_total), 2)
        output += f'\nValue of your total investment while purchase is: ${total_buy:,}'
        total_diff = round(float(net_worth - total_buy), 2)
        if total_diff < 0:
            output += f'\n\nOverall Loss: ${total_diff:,}'
        else:
            output += f'\n\nOverall Profit: ${total_diff:,}'
        yesterday_close = round(float(self.rh.equity_previous_close()), 2)
        two_day_diff = round(float(net_worth - yesterday_close), 2)
        output += f"\n\nYesterday's closing value: ${yesterday_close:,}"
        if two_day_diff < 0:
            output += f"\nCurrent Dip: ${two_day_diff:,}"
        else:
            output += f"\nCurrent Spike: ${two_day_diff:,}"
        return port_msg, profit_output, loss_output, output

    def watchlist(self, interval: str = 'hour', strict: bool = False) -> tuple:
        """Sweeps all watchlist stocks and compares current price with historical data (24h ago) to wrap as a string.

        Args:
            interval: Takes interval for historic data. Defaults to ``hour``. Options are ``hour`` or ``10minute``
            strict: Flag to ignore the watchlist items if the stocks were purchased already.

        Returns:
            tuple:
            Returns a tuple of each watch list item and a unicode character to indicate if the price went up or down.
        """
        r1, r2 = '', ''
        self.logger.info('Gathering watchlist.')
        watchlist = [self.rh.get_url(item['instrument'])
                     for item in self.rh.get_url(url='https://api.robinhood.com/watchlists/Default').get('results', [])]
        if not watchlist:
            return r1, r2
        instruments = [data['instrument'] for data in self.result] if strict else []
        for item in watchlist:
            if strict and item['url'] in instruments:
                continue
            stock = item['symbol']
            if interval == 'hour':
                historic_data = self.rh.get_historical_quotes(stock, 'hour', 'day')
            else:
                historic_data = self.rh.get_historical_quotes(stock, '10minute', 'day')
            historic_results = historic_data['results']
            numbers = [round(float(close_price['close_price']), 2) for each_item in historic_results
                       for close_price in each_item['historicals']]
            if not numbers:
                return r1, r2
            raw_details = self.rh.get_quote(stock)
            stock_name = requests.get(raw_details['instrument']).json()['simple_name']
            price = round(float(raw_details['last_trade_price']), 2)
            difference = round(float(price - numbers[-1]), 2)
            if price < numbers[-1]:
                r1 += f'{stock_name}\t<a href="https://robinhood.com/stocks/{stock}" target="_bottom">{stock}</a>: ' \
                      f'{price:,} &#8595 {difference}\n'
            else:
                r2 += f'{stock_name}\t<a href="https://robinhood.com/stocks/{stock}" target="_bottom">{stock}</a>: ' \
                      f'{price:,} &#8593 {difference}\n'
        return r1, r2

    def report_gatherer(self) -> None:
        """Gathers all the necessary information and creates an ``index.html`` using a ``Jinja`` template."""
        current_time = datetime.now()

        port_head, profit, loss, overall_result = self.watcher()
        s1, s2 = self.watchlist()
        self.logger.info('Generating HTMl file.')

        title = f'Investment Summary as of {current_time.strftime("%A, %B %d, %Y %I:%M %p")}'
        web_text = f'\n{overall_result}\n{port_head}\n'
        profit_web = f'\n{profit}\n'
        loss_web = f'\n{loss}\n'
        title = title.replace('\n', '\n\t\t\t')
        web_text = web_text.replace('\n', '\n\t\t\t')
        profit_web = profit_web.replace('\n', '\n\t\t\t\t')
        loss_web = loss_web.replace('\n', '\n\t\t\t\t')
        s2 = s2.replace('\n', '\n\t\t\t')
        s1 = s1.replace('\n', '\n\t\t\t')

        template = CustomTemplate.source.strip()
        rendered = jinja2.Template(template).render(TITLE=title, SUMMARY=web_text, PROFIT=profit_web, LOSS=loss_web,
                                                    WATCHLIST_UP=s2, WATCHLIST_DOWN=s1)
        with open(fileio.robinhood, 'w') as static_file:
            static_file.write(rendered)

        self.logger.info(f'Static file generated in {round(float(time.perf_counter()), 2)}s')


if __name__ == '__main__':
    logging.config.dictConfig(config.CronConfig().dict())

    if not os.path.isdir('logs'):
        os.mkdir('logs')

    Investment(logger=logging.getLogger('investment')).report_gatherer()

    with open(config.CronConfig().LOG_FILE, 'a') as file:
        file.seek(0)
        file.write('\n')
