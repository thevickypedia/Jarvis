from concurrent.futures import ThreadPoolExecutor, as_completed
from http import HTTPStatus
from typing import Callable, NoReturn

import pandas
from fastapi import APIRouter
from webull import paper_webull, webull

from jarvis.api.modals import settings
from jarvis.api.squire.logger import logger
from jarvis.modules.exceptions import APIResponse

router = APIRouter()


@router.get(path="/get-signals")
async def get_signals(symbol: str, bar_count: int = 100):
    """Get buy, sell and hold signals for a particular stock or all tickers supported by webull.

    Args:

        symbol: Stock ticker.
        bar_count: Number of bars from webull.
    """
    symbol = symbol.strip().upper()
    logger.info("Received request for '%s'", symbol)
    if symbol == "ALL":
        if settings.trader.stock_list:
            raise APIResponse(status_code=HTTPStatus.OK.real, detail=settings.trader.stock_list)
            # todo:
            #  repeated URL errors, no luck with traditional loop
            # thread_worker(function_to_call=get_signals_per_ticker)
            # result = {
            #     k: '\n'.join(v) for k, v in settings.trader.result.items()
            # }
            # logger.info(result)
            # raise APIResponse(status_code=HTTPStatus.OK.real, detail=result)
        else:
            raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real,
                              detail="Unable to process all tickers at the moment.")
    get_signals_per_ticker(symbol=symbol, bar_count=bar_count)


def thread_worker(function_to_call: Callable) -> NoReturn:
    """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

    Args:
        function_to_call: Takes the function/method that has to be called as an argument.
    """
    futures = {}
    executor = ThreadPoolExecutor(max_workers=len(settings.trader.stock_list))
    with executor:
        for iterator in settings.trader.stock_list:
            future = executor.submit(function_to_call, iterator)
            futures[future] = iterator

    for future in as_completed(futures):
        if future.exception():
            logger.error("Thread processing for '%s' received an exception: %s", iterator, future.exception())


def get_signals_per_ticker(symbol: str, bar_count: int = 100, all_tickers: bool = False):
    """Get buy, sell and hold signals for a particular stock.

    Args:

        symbol: Stock ticker.
        bar_count: Number of bars from webull.
        all_tickers: Boolean flag to get signals for all tickers.

    See Also:

        - A larger `bar_count` gives longer historical data for trend analysis.
        - A smaller count focuses on recent data for short-term signals.
        - Experiment and backtest to find the best fit for your approach.
        - Endpoint can be accessed via `https://vigneshrao.com/stock-analysis <https://vigneshrao.com/stock-analysis>`__

    References:

        `https://github.com/thevickypedia/trading-algorithm <https://github.com/thevickypedia/trading-algorithm>`__

    """
    # Fetch historical stock data using the 'get_bars' method from the 'webull' package
    try:
        bars = paper_webull().get_bars(stock=symbol, interval='d', count=bar_count)
    except ValueError as error:
        logger.error(f"{symbol} - {error.__str__()}")
        if all_tickers:
            return
        raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail=error.__str__())
    except Exception as error:
        logger.error(f"{symbol} - {error.__str__()}")
        logger.error(type(error))
        if all_tickers:
            return
        raise APIResponse(status_code=HTTPStatus.BAD_REQUEST.real, detail=error.__str__())

    # Create a DataFrame from the fetched data
    stock_data = pandas.DataFrame(bars)

    # Calculate short-term (e.g., 20-day) and long-term (e.g., 50-day) moving averages
    stock_data['SMA_short'] = stock_data['close'].rolling(window=20).mean()
    stock_data['SMA_long'] = stock_data['close'].rolling(window=50).mean()

    # Generate the buy, sell, and hold signals
    stock_data['buy'] = stock_data['SMA_short'] > stock_data['SMA_long']
    stock_data['sell'] = stock_data['SMA_short'] < stock_data['SMA_long']
    stock_data['hold'] = ~(stock_data['buy'] | stock_data['sell'])

    # Filter and display the buy, sell, and holds
    buy_signals = stock_data[stock_data['buy']]
    sell_signals = stock_data[stock_data['sell']]
    hold_signals = stock_data[stock_data['hold']]

    buy_signals_timestamped = {
        pandas.Timestamp(timestamp).to_pydatetime(): "Buy"
        for timestamp in buy_signals.index.values
    }
    sell_signals_timestamped = {
        pandas.Timestamp(timestamp).to_pydatetime(): "Sell"
        for timestamp in sell_signals.index.values
    }
    hold_signals_timestamped = {
        pandas.Timestamp(timestamp).to_pydatetime(): "Hold"
        for timestamp in hold_signals.index.values
    }

    all_signals = dict(sorted(
        {**buy_signals_timestamped, **sell_signals_timestamped, **hold_signals_timestamped}.items(),
        key=lambda x: x[0].timestamp()
    ))

    all_signals_ct = len(all_signals)
    assessment = {
        "Buy": round(len(buy_signals) / all_signals_ct * 100, 2),
        "Sell": round(len(sell_signals) / all_signals_ct * 100, 2),
        "Hold": round(len(hold_signals) / all_signals_ct * 100, 2)
    }

    if all_tickers:
        settings.trader.result[max(assessment, key=assessment.get).upper()].append(symbol)
        return

    extras = ""
    for key, value in assessment.items():
        logger.debug(f"{key} Signals: {value}%")
        extras += f"{key} Signals: {value}%\n"

    raw_details = webull().get_quote(symbol)
    price = raw_details.get("last_trade_price") or raw_details.get("pPrice") or \
        raw_details.get("open") or raw_details.get("close") or raw_details.get("preClose")
    quote = (round(float(price), 2))
    if settings.trader.stock_list.get(symbol):
        stock = f"{settings.trader.stock_list[symbol]} - [{symbol}] with a current price of ${quote}"
    else:
        stock = f"{symbol} with a current price of ${quote}"

    logger.info("%s is a %s", stock, max(assessment, key=assessment.get).upper())

    raise APIResponse(status_code=HTTPStatus.OK.real,
                      detail=f"{stock} is a {max(assessment, key=assessment.get).upper()}\n"
                             f"\n{extras}")
