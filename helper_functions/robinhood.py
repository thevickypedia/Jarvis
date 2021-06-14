from math import fsum


class RobinhoodGatherer:
    """Class to initiate robinhood client to get the portfolio details.

    >>> RobinhoodGatherer

    """

    @staticmethod
    def watcher(rh, result: list):
        """Fetches all necessary information about your investment portfolio.

        Returns: A string value of total purchased stocks and resultant profit/loss.

        """
        shares_total = []
        loss_total = []
        profit_total = []
        n = 0
        n_ = 0
        for data in result:
            share_id = str(data['instrument'].split('/')[-2])  # gets share_id eg: TSLA for Tesla
            buy = round(float(data['average_buy_price']), 2)  # price the stocks were purchased
            shares_count = int(data['quantity'].split('.')[0])  # number of shares owned in each stock
            if shares_count != 0:
                n = n + 1
                n_ = n_ + shares_count
            else:
                continue
            raw_details = rh.get_quote(share_id)
            total = round(shares_count * float(buy), 2)
            shares_total.append(total)
            current = (round(float(raw_details['last_trade_price']), 2))
            current_total = round(shares_count * current, 2)
            difference = round(float(current_total - total),
                               2)  # calculates difference between current and purchased total
            if difference < 0:
                loss_total.append(-difference)
            else:
                profit_total.append(difference)

        net_worth = round(rh.equity())
        total_buy = round(fsum(shares_total))
        total_diff = round(net_worth - total_buy)

        output = f'You have purchased {n} stocks and currently own {n_} shares sir. ' \
                 f'Your total investment is ${net_worth} now, and it was ${total_buy} when you purchased. '

        if total_diff < 0:
            output += f'Currently we are on an overall loss of ${total_diff} sir.'
        else:
            output += f'Currently we are on an overall profit of ${total_diff} sir.'

        return output
