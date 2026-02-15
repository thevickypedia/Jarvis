"""Initiates robinhood client to get the portfolio details."""

import math
import os
from typing import Any, Dict, List

import requests
import robin_stocks.robinhood as rh
from blockstdout import BlockPrint

from jarvis.modules.audio import speaker
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support

rh.set_output(open(os.devnull, "w"))


def get_stock_info(ticker: str) -> Dict[str, Any] | None:
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
                logger.error(error, exc_info=True)
            return raw_details
        else:
            logger.error("Unable to retrieve stock information for the ticker: %s", ticker)
    return None


def get_positions() -> List[Dict[str, Any]]:
    """Get position information from Robinhood.

    Returns:
        List[Dict[str, Any]]:
        Returns a list of key-value pairs containing traded positions.
    """
    with BlockPrint():
        rh.login(
            username=models.env.robinhood_user,
            password=models.env.robinhood_pass,
        )
        return rh.get_all_positions()


def get_portfolio() -> Dict[str, Any]:
    """Gets the information associated with the portfolios profile.

    Returns:
        Dict[str, Any]:
        Returns key-value pairs with portfolio information.
    """
    with BlockPrint():
        return rh.load_portfolio_profile()


def get_summary() -> str:
    """Fetches all necessary information about the user's investment portfolio.

    Returns:
        str:
        A string value of total purchased stocks and resultant profit/loss.
    """
    shares_total = []
    loss_total = []
    profit_total = []
    n = 0
    n_ = 0
    for data in get_positions():
        ticker = data["symbol"]
        buy = round(float(data["average_buy_price"]), 2)
        shares_count = int(data["quantity"].split(".")[0])
        if shares_count != 0:
            n = n + 1
            n_ = n_ + shares_count
        else:
            continue
        if not (raw_details := get_stock_info(ticker)):
            continue
        total = round(shares_count * float(buy), 2)
        shares_total.append(total)
        current = round(float(raw_details["last_trade_price"]), 2)
        current_total = round(shares_count * current, 2)
        # calculates difference between current and purchased total
        difference = round(float(current_total - total), 2)
        if difference < 0:
            loss_total.append(-difference)
        else:
            profit_total.append(difference)

    portfolio = get_portfolio()
    net_worth = round(float(portfolio["equity"]))
    withdrawable_amount = round(float(portfolio["withdrawable_amount"]))
    total_buy = round(math.fsum(shares_total))
    total_diff = round(net_worth - total_buy) - withdrawable_amount

    output = (
        f"You have purchased {n:,} stocks and currently own {n_:,} shares {models.env.title}. "
        f"Your total investment is ${net_worth:,} now, and it was ${total_buy:,} when you purchased. "
        f"Your current withdrawable amount is ${withdrawable_amount:,}. "
    )

    if total_diff < 0:
        output += f"Currently we are on an overall loss of ${total_diff:,} {models.env.title}."
    else:
        output += f"Currently we are on an overall profit of ${total_diff:,} {models.env.title}."

    return output


# noinspection PyUnusedLocal
def robinhood(*args) -> None:
    """Gets investment details from robinhood API."""
    if not all([models.env.robinhood_user, models.env.robinhood_pass]):
        logger.warning("Robinhood username or password.")
        support.no_env_vars()
        return

    # Tries to get information from DB from the hourly CRON job for stock report
    with models.db.connection as connection:
        cursor = connection.cursor()
        state = cursor.execute("SELECT summary FROM robinhood").fetchone()
    if state and state[0]:
        logger.info("Retrieved previously stored summary")
        speaker.speak(text=state[0])
        return
    try:
        summary = get_summary()
    except Exception as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to fetch your investment summary.")
        return
    speaker.speak(text=summary)
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM robinhood;")
        cursor.execute("INSERT or REPLACE INTO robinhood (summary) VALUES (?);", (summary,))
        connection.commit()
    logger.info("Stored summary in database.")
