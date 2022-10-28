import logging
import math
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, NoReturn, Union

import jinja2
from gmailconnector.send_email import SendEmail
from webull import webull

sys.path.insert(0, os.getcwd())

from api import squire  # noqa
from modules.logger import config  # noqa
from modules.models import models  # noqa
from modules.templates import templates  # noqa
from modules.utils import support  # noqa


class StockMonitor:
    """Initiates ``StockMonitor`` to check user entries in database and trigger notification if condition matches.

    >>> StockMonitor

    """

    def __init__(self, logger: logging.Logger):
        """Gathers user data in stock database, and groups user data by ``ticker`` and ``email``.

        Args:
            logger: Takes the class ``logging.Logger`` as an argument.
        """
        self.data = squire.get_stock_userdata()
        self.webull = webull()
        self.logger = logger
        self.ticker_grouped = defaultdict(list)
        self.email_grouped = defaultdict(list)
        self.group_data()

    def __del__(self):
        """Removes bin file created by webull client."""
        os.remove('did.bin') if os.path.isfile('did.bin') else None

    def group_data(self) -> NoReturn:
        """Groups columns in the database by ticker to check the current prices and by email to send a notification.

        See Also:
            - For ticker grouping, first value in the list is the ticker, so key will be ticker and the rest are values.
            - For email grouping, first value among the rest is the email, so key is email and the rest are values.
        """
        for k, *v in self.data:
            self.ticker_grouped[k].append(tuple(v))
            self.email_grouped[v[0]].append((k,) + tuple(v[1:]))

    def get_prices(self) -> Dict:
        """Get the price of each stock ticker along with the exchange code.

        Returns:
            dict:
            Returns a dictionary of prices for each ticker and their exchange code and key-value pairs.
        """
        prices = {}
        for ticker in self.ticker_grouped.keys():
            prices[ticker] = {}
            try:
                price_check = self.webull.get_quote(ticker)
                if current_price := round(float(price_check.get('close') or price_check.get('open')), 2):
                    prices[ticker]['price'] = float(current_price)
                else:
                    raise ValueError(price_check)
                if category := price_check.get('disExchangeCode'):
                    prices[ticker]['exchange_code'] = category
                else:
                    raise ValueError(price_check)
            except ValueError as error:
                self.logger.error(error)
                continue
        return prices

    @staticmethod
    def closest_maximum(stock_price: Union[int, float], maximum: Union[int, float], correction: int) -> bool:
        """Determines if a stock price is close to the maximum value.

        Examples:
            - Current stock price: 96
            - Maximum price after which notification has to trigger: 100
            - Correction: 15%

            - Corrected: 100 (max) - 15 (15%) = 85 (this becomes the new maximum price)
            - Notifies since stock price is more than corrected amount, even though it is less than actual stock price.

        Args:
            stock_price: Current stock price.
            maximum: Maximum price set by user.
            correction: Correction percentage.

        Returns:
            bool:
            Boolean flag to indicate whether the current stock price is less than set maximum by correction percentage.
        """
        max_corrected_amt = math.floor(maximum - (stock_price * correction / 100))
        return stock_price >= max_corrected_amt

    @staticmethod
    def closest_minimum(stock_price: Union[int, float], minimum: Union[int, float], correction: int) -> bool:
        """Determines if a stock price is close to the minimum value.

        Examples:
            - Current stock price: 225
            - Minimum price below which notification has to trigger: 220
            - Correction: 10%

            - Corrected: 220 (min) + 22 (10%) = 242 (this becomes the new minimum price)
            - Notifies since stock price is less than corrected amount, even though it is more than actual stock price.

        Args:
            stock_price: Current stock price.
            minimum: Minimum price set by user.
            correction: Correction percentage.

        Returns:
            bool:
            Boolean flag to indicate whether the current stock price is more than set maximum by correction percentage.
        """
        min_corrected_amt = math.ceil(minimum + (stock_price * correction / 100))
        return stock_price <= min_corrected_amt

    def send_notification(self) -> NoReturn:
        """Sends notification to the user when the stock price matches the requested condition."""
        subject = f"Stock Price Alert - {datetime.now().strftime('%c')}"
        email_template = templates.StockMonitor.source
        prices = self.get_prices()
        for k, v in self.email_grouped.items():
            mail_obj = SendEmail(gmail_user=models.env.alt_gmail_user or models.env.gmail_user,
                                 gmail_pass=models.env.alt_gmail_pass or models.env.gmail_pass)
            text_gathered = []
            for trigger in v:
                ticker = trigger[0]
                maximum = trigger[1]
                minimum = trigger[2]
                correction = trigger[3]
                ticker_hyperlinked = '<a href="https://www.webull.com/quote/' \
                                     f'{prices[ticker]["exchange_code"].lower()}-{ticker.lower()}">{ticker}</a>'
                if not maximum and not minimum:
                    raise ValueError("Un-processable without both min and max")
                maximum = support.format_nos(maximum)
                minimum = support.format_nos(minimum)
                email_text = ""
                if maximum and prices[ticker]['price'] >= maximum:
                    email_text += f"{ticker_hyperlinked} has increased more than the set value: ${maximum:,}"
                elif maximum and self.closest_maximum(prices[ticker]['price'], maximum, correction):
                    email_text += f"{ticker_hyperlinked} is close (within {correction}% range) to the set " \
                                  f"maximum value: ${maximum:,}"
                elif minimum and prices[ticker]['price'] <= minimum:
                    email_text += f"{ticker_hyperlinked} has decreased less than the set value: ${minimum:,}"
                elif minimum and self.closest_minimum(prices[ticker]['price'], minimum, correction):
                    email_text += f"{ticker_hyperlinked} is close (within {correction}% range) to the set " \
                                  f"minimum value: ${minimum:,}"
                if email_text:
                    email_text += f"<br>Current price of {ticker_hyperlinked} is ${prices[ticker]['price']:,}"
                    text_gathered.append(email_text)
            if not text_gathered:
                self.logger.info("Nothing to report")
                return
            template = jinja2.Template(email_template).render(CONVERTED="<br><br>".join(text_gathered))
            response = mail_obj.send_email(subject=subject, recipient=k, html_body=template, sender="Jarvis")
            if response.ok:
                self.logger.info(f'Email has been sent to {k!r}')
            else:
                self.logger.error(response.json())


if __name__ == '__main__':
    from executors.crontab import LOG_FILE
    from modules.logger.custom_logger import logger as main_logger

    filename = config.multiprocessing_logger(filename=LOG_FILE)
    StockMonitor(logger=main_logger).send_notification()

    with open(filename, 'a') as file:
        file.seek(0)
        file.write('\n')
