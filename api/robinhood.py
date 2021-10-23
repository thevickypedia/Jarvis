from datetime import date, datetime
from json import loads
from math import fsum
from os import environ
from time import perf_counter

from pyrh import Robinhood
from requests import get


def market_status() -> bool:
    """Checks if the stock market is open today.

    Returns:
        bool:
        True if the current date is ``NOT`` in trading calendar or fails to fetch results from the URL.
    """
    today = date.today().strftime("%B %d, %Y")
    url = get(url='https://www.nasdaqtrader.com/trader.aspx?id=Calendar')

    if not url.ok:
        return True

    if today not in url.text:
        return True


class Investment:
    """Initiates Investment object to gather portfolio information.

    >>> Investment

    """

    def __init__(self, logger):
        """Authenticates Robinhood object and gathers the portfolio information and stores in the var ``raw_result``.

        Args:
            logger: Takes the class ``logging.Logger`` as an argument.
        """
        rh = Robinhood()
        rh.login(username=environ.get('robinhood_user'), password=environ.get('robinhood_pass'),
                 qr_code=environ.get('robinhood_qr'))
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
        shares_total = []
        port_msg = 'Your portfolio:\n'
        loss_output = ''
        profit_output = ''
        loss_total = []
        profit_total = []
        n = 0
        n_ = 0
        self.logger.info('Gathering portfolio.')
        for data in self.result:
            share_id = str(data['instrument'].split('/')[-2])
            buy = round(float(data['average_buy_price']), 2)
            shares_count = int(data['quantity'].split('.')[0])
            if shares_count != 0:
                n = n + 1
                n_ = n_ + shares_count
            else:
                continue
            raw_details = self.rh.get_quote(share_id)
            ticker = (raw_details['symbol'])
            call = raw_details['instrument']
            r = get(call)
            response = r.text
            json_load = loads(response)
            stock_name = json_load['simple_name']
            total = round(shares_count * float(buy), 2)
            shares_total.append(total)
            current = (round(float(raw_details['last_trade_price']), 2))
            current_total = round(shares_count * current, 2)
            difference = round(float(current_total - total), 2)
            if difference < 0:
                loss_output += (
                    f'\n{stock_name}:\n{shares_count} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy} Currently: ${current}\n '
                    f'Total bought: ${total} Current Total: ${current_total}'
                    f'\nLOST ${-difference}\n')
                loss_total.append(-difference)
            else:
                profit_output += (
                    f'\n{stock_name}:\n{shares_count} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy} Currently: ${current}\n'
                    f'Total bought: ${total} Current Total: ${current_total}'
                    f'\nGained ${difference}\n')
                profit_total.append(difference)

        lost = round(fsum(loss_total), 2)
        gained = round(fsum(profit_total), 2)
        port_msg += f'The below values will differ from overall profit/loss if shares were purchased ' \
                    f'with different price values.\nTotal Profit: ${gained}\nTotal Loss: ${lost}\n'
        net_worth = round(float(self.rh.equity()), 2)
        output = f'Total number of stocks purchased: {n}\n'
        output += f'Total number of shares owned: {n_}\n'
        output += f'\nCurrent value of your total investment is: ${net_worth}'
        total_buy = round(fsum(shares_total), 2)
        output += f'\nValue of your total investment while purchase is: ${total_buy}'
        total_diff = round(float(net_worth - total_buy), 2)
        if total_diff < 0:
            output += f'\nOverall Loss: ${total_diff}'
        else:
            output += f'\nOverall Profit: ${total_diff}'
        yesterday_close = round(float(self.rh.equity_previous_close()), 2)
        two_day_diff = round(float(net_worth - yesterday_close), 2)
        output += f"\n\nYesterday's closing value: ${yesterday_close}"
        if two_day_diff < 0:
            output += f"\nCurrent Dip: ${two_day_diff}"
        else:
            output += f"\nCurrent Spike: ${two_day_diff}"
        return port_msg, profit_output, loss_output, output

    def watchlist(self, interval: str = 'hour') -> tuple:
        """Sweeps all watchlist stocks and compares current price with historical data (24h ago) to wrap as a string.

        Args:
            interval: Takes interval for historic data. Options are ``hour`` or ``10minute``

        Returns:
            tuple:
            Returns a tuple of each watch list item and a unicode character to indicate if the price went up or down.
        """
        self.logger.info('Gathering watchlist.')
        watchlist = (self.rh.get_watchlists())
        r1, r2 = '', ''
        instruments = []
        for data in self.result:
            instruments.append(data['instrument'])
        for item in watchlist:
            instrument = item['url']
            if instrument not in instruments:
                stock = item['symbol']
                raw_details = self.rh.get_quote(stock)
                call = raw_details['instrument']
                if interval == 'hour':
                    historic_data = self.rh.get_historical_quotes(stock, 'hour', 'day')
                else:
                    historic_data = self.rh.get_historical_quotes(stock, '10minute', 'day')
                historic_results = historic_data['results']
                numbers = []
                for each_item in historic_results:
                    historical_values = each_item['historicals']
                    for close_price in historical_values:
                        numbers.append(round(float(close_price['close_price']), 2))
                r = get(call)
                response = r.text
                json_load = loads(response)
                stock_name = json_load['simple_name']
                price = round(float(raw_details['last_trade_price']), 2)
                difference = round(float(price - numbers[-1]), 2)
                if price < numbers[-1]:
                    r1 += f'{stock_name}({stock}) - {price} &#8595 {difference}\n'
                else:
                    r2 += f'{stock_name}({stock}) - {price} &#8593 {difference}\n'
        return r1, r2

    def report_gatherer(self) -> None:
        """Gathers all the necessary information and creates an ``index.html`` using the template ``static.html``."""
        current_time = datetime.now()
        if not market_status():
            self.logger.warning(f'{current_time.strftime("%B %d, %Y")}: The markets are closed today.')
            return

        port_head, profit, loss, overall_result = self.watcher()
        try:
            s1, s2 = self.watchlist()
        except IndexError:
            self.logger.error('Unable to gather watchlist information.')
            s1, s2 = '', 'Watchlist feature is currently unstable.'

        self.logger.info('Generating HTMl file.')
        title = f'Investment Summary as of {current_time.strftime("%A, %B %d, %Y %I:%M %p")}'
        web_text = f'\n{overall_result}\n{port_head}\n'
        profit_web = f'\n{profit}\n'
        loss_web = f'\n{loss}\n'
        # todo: Consider using Jinja template
        with open('static.html') as template:
            data = template.read()
        data = data.strip()\
            .replace('TITLE_HERE', title.replace('\n', '\n\t\t\t'))\
            .replace('WEB_TEXT_HERE', web_text.replace('\n', '\n\t\t\t'))\
            .replace('PROFIT_WEB_HERE', profit_web.replace('\n', '\n\t\t\t'))\
            .replace('LOSS_WEB_HERE', loss_web.replace('\n', '\n\t\t\t'))\
            .replace('S2_HERE', s2.replace('\n', '\n\t\t\t'))\
            .replace('S1_HERE', s1.replace('\n', '\n\t\t\t'))
        with open('robinhood.html', 'w') as file:
            file.write(data)
        self.logger.info(f'Static file generated in {round(float(perf_counter()), 2)}s')


if __name__ == '__main__':
    from logging import DEBUG, getLogger

    module_logger = getLogger(__name__)
    module_logger.setLevel(DEBUG)

    Investment(logger=module_logger).report_gatherer()
