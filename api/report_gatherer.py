from datetime import date, datetime
from logging import Logger, config, getLogger
import math
import os
from time import perf_counter

import requests
import jinja2
from pyrh import Robinhood


def market_status() -> bool:
    """Checks if the stock market is open today.

    Returns:
        bool:
        True if the current date is ``NOT`` in trading calendar or fails to fetch results from the URL.
    """
    today = date.today().strftime("%B %d, %Y")
    url = requests.get(url='https://www.nasdaqtrader.com/trader.aspx?id=Calendar')

    if not url.ok:
        return True

    if today not in url.text:
        return True


class Investment:
    """Initiates ``Investment`` which gathers portfolio information.

    >>> Investment

    """

    def __init__(self, logger: Logger):
        """Authenticates Robinhood object and gathers the portfolio information to store it in a variable.

        Args:
            logger: Takes the class ``logging.Logger`` as an argument.
        """
        rh = Robinhood()
        rh.login(username=os.environ.get('robinhood_user'), password=os.environ.get('robinhood_pass'),
                 qr_code=os.environ.get('robinhood_qr'))
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
        shares_total, loss_total, profit_total = [], [], []
        loss_output, profit_output = '', ''
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
                loss_output += (
                    f'\n{stock_name}:\n{shares_count:,} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy:,} Currently: ${current:,}\n '
                    f'Total bought: ${total:,} Current Total: ${current_total:,}'
                    f'\nLOST ${-difference:,}\n')
                loss_total.append(-difference)
            else:
                profit_output += (
                    f'\n{stock_name}:\n{shares_count:,} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy:,} Currently: ${current:,}\n'
                    f'Total bought: ${total:,} Current Total: ${current_total:,}'
                    f'\nGained ${difference:,}\n')
                profit_total.append(difference)

        lost = round(math.fsum(loss_total), 2)
        gained = round(math.fsum(profit_total), 2)
        port_msg = f'\nTotal Profit: ${gained:,}\nTotal Loss: ${lost:,}\n\n' \
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

    def watchlist(self, interval: str = 'hour') -> tuple:
        """Sweeps all watchlist stocks and compares current price with historical data (24h ago) to wrap as a string.

        Args:
            interval: Takes interval for historic data. Defaults to ``hour``. Options are ``hour`` or ``10minute``

        Returns:
            tuple:
            Returns a tuple of each watch list item and a unicode character to indicate if the price went up or down.
        """
        self.logger.info('Gathering watchlist.')
        watchlist_items = self.rh.get_url(url="https://api.robinhood.com/watchlists/")
        watchlist = [self.rh.get_url(item['instrument'])
                     for item in self.rh.get_url(url=watchlist_items["results"][0]["url"])["results"]
                     if watchlist_items and 'results' in watchlist_items]
        r1, r2 = '', ''
        instruments = [data['instrument'] for data in self.result]
        for item in watchlist:
            if item['url'] in instruments:  # ignores the watchlist items if the stocks were purchased already
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
        if not market_status():
            self.logger.warning(f'{current_time.strftime("%B %d, %Y")}: The markets are closed today.')
            return

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

        from rh_helper import CustomTemplate
        template = CustomTemplate.source.strip()
        rendered = jinja2.Template(template).render(TITLE=title, SUMMARY=web_text, PROFIT=profit_web, LOSS=loss_web,
                                                    WATCHLIST_UP=s2, WATCHLIST_DOWN=s1)
        with open('robinhood.html', 'w') as static_file:
            static_file.write(rendered)

        self.logger.info(f'Static file generated in {round(float(perf_counter()), 2)}s')


if __name__ == '__main__':
    from dotenv import load_dotenv
    from models import LogConfig

    config.dictConfig(LogConfig().dict())

    if not os.path.isdir('logs'):
        os.system('mkdir logs')

    if os.path.isfile('../.env'):
        load_dotenv(dotenv_path='../.env')

    Investment(logger=getLogger('investment')).report_gatherer()

    with open(LogConfig().FILE_LOG, 'a') as file:
        file.seek(0)
        file.write('\n')
