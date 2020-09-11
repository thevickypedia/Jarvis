import math
from pyrh import Robinhood
import os

u = os.getenv('user')
p = os.getenv('pass')
q = os.getenv('qr')
rh = Robinhood()
rh.login(username=u, password=p, qr_code=q)
raw_result = rh.positions()
result = raw_result['results']


def watcher():
    shares_total = []
    loss_total = []
    profit_total = []
    n = 0
    n_ = 0
    for data in result:
        share_id = str(data['instrument'].split('/')[-2])
        buy = round(float(data['average_buy_price']), 2)
        shares_count = int(data['quantity'].split('.')[0])
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
        difference = round(float(current_total - total), 2)
        if difference < 0:
            loss_total.append(-difference)
        else:
            profit_total.append(difference)

    net_worth = round(float(rh.equity()), 2)
    output = f'You have purchased {n} stocks,\n'
    output += f'and currently own {n_} shares.\n'
    output += f'Current value of your total investment is ${net_worth}.\n'
    total_buy = round(math.fsum(shares_total), 2)
    output += f'Value of your total investment while purchase was ${total_buy}.\n'
    total_diff = round(float(net_worth - total_buy), 2)
    if total_diff < 0:
        output += f'Currently your overall loss is ${total_diff}\n'
    else:
        output += f'Currently your overall profit is ${total_diff}\n'

    return output
