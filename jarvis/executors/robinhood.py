"""Initiates robinhood client to get the portfolio details."""

import math

from pyrh import Robinhood
from pyrh.exceptions import InvalidInstrumentId, InvalidTickerSymbol

from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support


def watcher(rh, result: list) -> str:
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
        except (InvalidTickerSymbol, InvalidInstrumentId) as error:
            logger.error(error)
            continue
        total = round(shares_count * float(buy), 2)
        shares_total.append(total)
        current = (round(float(raw_details["last_trade_price"]), 2))
        current_total = round(shares_count * current, 2)
        difference = round(float(current_total - total), 2)  # calculates difference between current and purchased total
        if difference < 0:
            loss_total.append(-difference)
        else:
            profit_total.append(difference)

    net_worth = round(rh.equity())
    total_buy = round(math.fsum(shares_total))
    total_diff = round(net_worth - total_buy)

    output = f"You have purchased {n:,} stocks and currently own {n_:,} shares {models.env.title}. " \
             f"Your total investment is ${net_worth:,} now, and it was ${total_buy:,} when you purchased. "

    if total_diff < 0:
        output += f"Currently we are on an overall loss of ${total_diff:,} {models.env.title}."
    else:
        output += f"Currently we are on an overall profit of ${total_diff:,} {models.env.title}."

    return output


def robinhood() -> None:
    """Gets investment details from robinhood API."""
    if not all([models.env.robinhood_user, models.env.robinhood_pass, models.env.robinhood_qr]):
        logger.warning("Robinhood username, password or QR code not found.")
        support.no_env_vars()
        return

    rh = Robinhood()
    rh.login(username=models.env.robinhood_user, password=models.env.robinhood_pass, qr_code=models.env.robinhood_qr)
    raw_result = rh.positions()
    result = raw_result["results"]
    stock_value = watcher(rh, result)
    speaker.speak(text=stock_value)
