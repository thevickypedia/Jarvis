"""Initiates robinhood client to get the portfolio details."""

import math

from pyrh import Robinhood
from pyrh.exceptions import AuthenticationError, PyrhException

from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support


def get_summary() -> str:
    """Fetches all necessary information about the user's investment portfolio.

    Returns:
        str:
        A string value of total purchased stocks and resultant profit/loss.
    """
    rh = Robinhood(
        username=models.env.robinhood_user,
        password=models.env.robinhood_pass,
        mfa=models.env.robinhood_qr,
    )
    rh.login()
    raw_result = rh.positions()
    result = raw_result["results"]
    shares_total = []
    loss_total = []
    profit_total = []
    n = 0
    n_ = 0
    for data in result:
        share_id = str(data["instrument"].split("/")[-2])
        buy = round(float(data["average_buy_price"]), 2)
        shares_count = int(data["quantity"].split(".")[0])
        if shares_count != 0:
            n = n + 1
            n_ = n_ + shares_count
        else:
            continue
        try:
            raw_details = rh.get_quote(share_id)
        except PyrhException as error:
            logger.error(error)
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

    portfolio = rh.portfolio()
    net_worth = round(float(portfolio.equity))
    withdrawable_amount = round(float(portfolio.withdrawable_amount))
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


def robinhood(*args) -> None:
    """Gets investment details from robinhood API."""
    if not all(
        [models.env.robinhood_user, models.env.robinhood_pass, models.env.robinhood_qr]
    ):
        logger.warning("Robinhood username, password or QR code not found.")
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
    except AuthenticationError as error:
        logger.error(error)
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I ran into an authentication error."
        )
        return
    except PyrhException as error:
        logger.error(error)
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to fetch your investment summary."
        )
        return
    speaker.speak(text=summary)
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM robinhood;")
        cursor.execute(
            "INSERT or REPLACE INTO robinhood (summary) VALUES (?);", (summary,)
        )
        connection.commit()
    logger.info("Stored summary in database.")
