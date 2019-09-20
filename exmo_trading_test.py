# -*- coding: utf-8 -*-
from signals import Analyser
from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR
from exmo_api import FakeExmoAPI as ExmoAPI
import time

# TRASH FILE

api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER, PERIOD)

deals = api.get_deals(pair=PAIR, limit=10000)
if deals:
    _, _, _, closes, _, dates = api.process_deals(deals)
    delta = int(10000 / len(dates))
    last_deal_price = closes[150]

    for x in range(150, len(dates)):
        tmp = list(reversed(deals))
        tmp = tmp[:x * delta]
        tmp = list(reversed(tmp))
        args = api.process_deals(tmp)
        taanal = Analyser(*args)
        signal = sum([taanal.get_candles_signal(),
                      taanal.get_sma_ema_signal(),
                      taanal.get_rsi_signal(),
                      taanal.get_macd_signal(),
                      taanal.get_obv_signal()])
        price = args[3][-1]
        cur1, cur2 = api.get_balance(PAIR)
        if signal > 0.8 and price < last_deal_price - last_deal_price * 0.006:
            # state += 1
            api.make_deal(PAIR, 0.001, 1, price)
            last_deal_price = price
        if signal < -0.8 and price > last_deal_price + last_deal_price * 0.006:
            # state += -1
            api.make_deal(PAIR, 0.001, -1, price)
            last_deal_price = price

    # api.convert_all(PAIR, price)
    api.convert_all(PAIR, price)
