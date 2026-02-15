"""Runs once during API startup and continues to run in a cron scheduler as per market hours."""

import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, Tuple

import jinja2
import requests
import robin_stocks.robinhood as rh
from blockstdout import BlockPrint

from jarvis.modules.exceptions import EgressErrors

rh.set_output(open(os.devnull, "w"))


class Investment:
    """Initiates ``Investment`` which gathers portfolio information.

    >>> Investment

    Args:
        logger: Takes the class ``logging.Logger`` as an argument.
    """

    def __init__(self, logger: logging.Logger):
        """Authenticates Robinhood object and gathers the portfolio information to store it in a variable."""
        self.logger = logger
        with BlockPrint():
            rh.login(
                username=models.env.robinhood_user,
                password=models.env.robinhood_pass,
            )
            self.result = rh.get_all_positions()

    def get_stock_info(self, ticker: str) -> Dict[str, Any] | None:
        """Get raw stock information from Robinhood for a particular ticker.

        Args:
            ticker: Stock ticker.

        Returns:
            Dict[str, Any]:
            Returns a dictionary of stock information from Robinhood.
        """
        with BlockPrint():
            if raw_details := rh.get_quotes(ticker)[0]:
                raw_details["simple_name"] = "N/A"
                try:
                    if simple_name := requests.get(url=raw_details["instrument"]).json()["simple_name"]:
                        raw_details["simple_name"] = simple_name
                        return raw_details
                except EgressErrors as error:
                    self.logger.error(error, exc_info=True)
                return raw_details
            else:
                self.logger.error("Unable to retrieve stock information for the ticker: %s", ticker)
        return None

    def watcher(self) -> Tuple[str, str, str, str, str]:
        """Gathers all the information and wraps into parts of strings to create an HTML file.

        Returns:
            Tuple[str, str, str, str, str]:
            Returns a tuple of portfolio header, profit, loss, and current profit/loss compared from purchased.
        """
        shares_total, loss_dict, profit_dict = [], {}, {}
        num_stocks, num_shares = 0, 0
        self.logger.info("Gathering portfolio.")

        for data in self.result:
            shares_count = int(data["quantity"].split(".")[0])
            if not shares_count:
                continue
            num_stocks += 1
            num_shares += shares_count
            ticker = data["symbol"]
            if not (raw_details := self.get_stock_info(ticker)):
                continue
            stock_name = raw_details["simple_name"]
            buy = round(float(data["average_buy_price"]), 2)
            total = round(shares_count * float(buy), 2)
            shares_total.append(total)
            current = round(float(raw_details["last_trade_price"]), 2)
            current_total = round(shares_count * current, 2)
            difference = round(float(current_total - total), 2)
            if difference < 0:
                loss_dict[ticker] = [
                    -difference,
                    f'\n{stock_name}:\n{shares_count:,} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy:,} Currently: ${current:,}\n '
                    f"Total bought: ${total:,} Current Total: ${current_total:,}"
                    f"\nLOST ${-difference:,}\n",
                ]
            else:
                profit_dict[ticker] = [
                    difference,
                    f'\n{stock_name}:\n{shares_count:,} shares of <a href="https://robinhood.com/stocks/{ticker}" '
                    f'target="_bottom">{ticker}</a> at ${buy:,} Currently: ${current:,}\n'
                    f"Total bought: ${total:,} Current Total: ${current_total:,}"
                    f"\nGained ${difference:,}\n",
                ]

        profit_output, profit_total, loss_output, loss_total = "", [], "", []
        for key, value in sorted(profit_dict.items(), reverse=True, key=lambda item: item[1]):
            profit_output += value[1]
            profit_total.append(value[0])
        for key, value in sorted(loss_dict.items(), reverse=True, key=lambda item: item[1]):
            loss_output += value[1]
            loss_total.append(value[0])

        with BlockPrint():
            portfolio = rh.load_portfolio_profile()
        port_msg = (
            f"\nTotal Profit: ${round(math.fsum(profit_total), 2):,}\n"
            f"Total Loss: ${round(math.fsum(loss_total), 2):,}\n\n"
            "The above values might differ from overall profit/loss if multiple shares "
            "of the stock were purchased at different prices."
        )
        net_worth = round(float(portfolio["equity"]), 2)
        withdrawable_amount = round(float(portfolio["withdrawable_amount"]))
        output = f"Total number of stocks purchased: {num_stocks:,}\n"
        output += f"Total number of shares owned: {num_shares:,}\n"
        output += f"\nCurrent value of your total investment is: ${net_worth:,}"
        total_buy = round(math.fsum(shares_total), 2)
        output += f"\nValue of your total investment while purchase is: ${total_buy:,}"
        total_diff = round(float(net_worth - total_buy), 2) - withdrawable_amount
        rh_text = (
            f"You have purchased {num_stocks:,} stocks and currently own {num_shares:,} shares {models.env.title}. "
            f"Your total investment is ${round(net_worth):,}, and it was ${round(total_buy):,} when you purchased. "
            f"Your current withdrawable amount is ${withdrawable_amount:,}. "
            f"Currently we are on an overall "
        )
        if total_diff < 0:
            rh_text += f"loss of ${round(total_diff):,} {models.env.title}"
            output += f"\n\nOverall Loss: ${total_diff:,}"
        else:
            rh_text += f"profit of ${round(total_diff):,} {models.env.title}"
            output += f"\n\nOverall Profit: ${total_diff:,}"
        yesterday_close = round(float(portfolio["equity_previous_close"]), 2)
        two_day_diff = round(float(net_worth - yesterday_close), 2)
        output += f"\n\nYesterday's closing value: ${yesterday_close:,}"
        if two_day_diff < 0:
            output += f"\nCurrent Dip: ${two_day_diff:,}"
        else:
            output += f"\nCurrent Spike: ${two_day_diff:,}"
        output += f"\n\nWithdrawable Amount: ${withdrawable_amount:,}"
        return port_msg, profit_output, loss_output, output, rh_text

    def watchlist(self, interval: str = "hour", strict: bool = False) -> Tuple[str, str]:
        """Sweeps all watchlist stocks and compares current price with historical data (24h ago) to wrap as a string.

        Args:
            interval: Takes interval for historic data. Defaults to ``hour``. Options are ``hour`` or ``10minute``
            strict: Flag to ignore the watchlist items if the stocks were purchased already.

        Returns:
            Tuple[str, str]:
            Returns a tuple of each watch list item and a Unicode character to indicate if the price went up or down.
        """
        r1, r2 = "", ""
        self.logger.info("Gathering watchlist.")
        with BlockPrint():
            if watchlist := rh.get_watchlist_by_name(models.env.robinhood_watchlist):
                watchlist_results = watchlist["results"]
            else:
                return r1, r2
        instruments = [data["instrument"] for data in self.result] if strict else []
        for item in watchlist_results:
            if strict and item["url"] in instruments:
                continue
            ticker = item["symbol"]
            with BlockPrint():
                if interval == "hour":
                    historic_data = rh.get_stock_historicals(ticker, "hour", "day")
                else:
                    historic_data = rh.get_stock_historicals(ticker, "10minute", "day")
            if not (numbers := [round(float(each_item["close_price"]), 2) for each_item in historic_data]):
                return r1, r2
            if not (raw_details := self.get_stock_info(ticker)):
                continue
            stock_name = raw_details["simple_name"]
            price = round(float(raw_details["last_trade_price"]), 2)
            difference = round(float(price - numbers[-1]), 2)
            if price < numbers[-1]:
                r1 += (
                    f'{stock_name}\t<a href="https://robinhood.com/stocks/{ticker}" target="_bottom">{ticker}</a>: '
                    f"{price:,} &#8595 {difference}\n"
                )
            else:
                r2 += (
                    f'{stock_name}\t<a href="https://robinhood.com/stocks/{ticker}" target="_bottom">{ticker}</a>: '
                    f"{price:,} &#8593 {difference}\n"
                )
        return r1, r2

    def gatherer(self) -> None:
        """Gathers all the necessary information and creates an ``index.html`` using a ``Jinja`` template."""
        if not self.result:
            return
        current_time = datetime.now()
        port_head, profit, loss, overall_result, summary = self.watcher()
        s1, s2 = self.watchlist()
        self.logger.info("Generating HTMl file.")

        title = f'Investment Summary as of {current_time.strftime("%A, %B %d, %Y %I:%M %p")}'
        web_text = f"\n{overall_result}\n{port_head}\n"
        profit_web = f"\n{profit}\n"
        loss_web = f"\n{loss}\n"
        title = title.replace("\n", "\n\t\t\t")
        web_text = web_text.replace("\n", "\n\t\t\t")
        profit_web = profit_web.replace("\n", "\n\t\t\t\t")
        loss_web = loss_web.replace("\n", "\n\t\t\t\t")
        s2 = s2.replace("\n", "\n\t\t\t")
        s1 = s1.replace("\n", "\n\t\t\t")

        rendered = jinja2.Template(templates.endpoint.robinhood).render(
            TITLE=title,
            SUMMARY=web_text,
            PROFIT=profit_web,
            LOSS=loss_web,
            WATCHLIST_UP=s2,
            WATCHLIST_DOWN=s1,
        )
        with open(models.fileio.robinhood, "w") as static_file:
            static_file.write(rendered)
        self.logger.info("Static file '%s' has been generated.", models.fileio.robinhood)
        with models.db.connection as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM robinhood;")
            cursor.execute("INSERT or REPLACE INTO robinhood (summary) VALUES (?);", (summary,))
            connection.commit()
        self.logger.info("Stored summary in database.")

    def report_gatherer(self) -> None:
        """Runs gatherer to call other dependent methods."""
        try:
            self.gatherer()
        except Exception as error:
            self.logger.error(error)


if __name__ == "__main__":
    # imports within __main__ to avoid potential/future path error and circular import
    # override 'current_process().name' to avoid being set as 'MainProcess'
    # importing at top level requires setting current_process().name at top level which will in turn override any import
    from multiprocessing import current_process

    current_process().name = "StockReport"
    from jarvis.executors import crontab
    from jarvis.modules.logger import logger as main_logger
    from jarvis.modules.logger import multiprocessing_logger
    from jarvis.modules.models import models
    from jarvis.modules.templates import templates

    multiprocessing_logger(filename=crontab.LOG_FILE)
    # Remove process name filter
    for log_filter in main_logger.filters:
        main_logger.removeFilter(filter=log_filter)

    Investment(logger=main_logger).report_gatherer()
