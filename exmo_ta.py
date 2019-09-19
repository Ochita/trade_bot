# -*- coding: utf-8 -*-
import numpy
import talib

from mpl_finance import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR
from exmo_api import ExmoAPI

api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER, PERIOD)

deals = api.get_deals(pair=PAIR, limit=10000)
if deals:
    opens, hights, lows, closes, quantities, dates = api.process_deals(deals)

    xdate = [datetime.fromtimestamp(item) for item in sorted(dates)]

    fig, ax = plt.subplots(4, sharex=True)

    candlestick2_ohlc(ax[0], opens, hights, lows, closes, width=0.6)

    ax[0].xaxis.set_major_locator(ticker.MaxNLocator(20))


    def chart_date(x, pos):
        try:
            return xdate[int(x)]
        except IndexError:
            return ''

    ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

    fig.autofmt_xdate()
    fig.tight_layout()

    sma = talib.SMA(closes, timeperiod=50)
    ax[0].plot(sma)

    ema = talib.EMA(closes, timeperiod=20)
    ax[0].plot(ema)

    trend = numpy.polyfit(range(len(closes) - 10, len(closes)), closes[-10:], 1)
    trendpoly = numpy.poly1d(trend)
    ax[0].plot(range(len(closes) - 10, len(closes)), trendpoly(range(len(closes) - 10, len(closes))))

    args = (opens, hights, lows, closes)

    hammer = talib.CDLHAMMER(*args)  # will go up
    inverted_hammer = talib.CDLINVERTEDHAMMER(*args)  # will go up
    evening_star = talib.CDLEVENINGSTAR(*args)  # will go down
    morning_star = talib.CDLMORNINGSTAR(*args)  # will go up
    shooting_star = talib.CDLSHOOTINGSTAR(*args)  # will go down
    hanging_man = talib.CDLHANGINGMAN(*args)  # will go down
    engulfing = talib.CDLENGULFING(*args)
    ax[1].plot(hammer)
    ax[1].plot(inverted_hammer)
    ax[1].plot(evening_star)
    ax[1].plot(morning_star)
    ax[1].plot(shooting_star)
    ax[1].plot(hanging_man)
    ax[1].plot(engulfing)

    from utils import TAAnalyser

    taanal = TAAnalyser(opens, hights, lows, closes, quantities, dates)
    print(taanal.get_rsi_signal())

    rsi = talib.RSI(closes, timeperiod=20)
    ax[2].plot(rsi)
    rsi_trend = numpy.polyfit(range(len(rsi) - 10, len(rsi)), rsi[-10:], 1)
    rsi_trendpoly = numpy.poly1d(rsi_trend)
    ax[2].plot(range(len(rsi) - 10, len(rsi)), rsi_trendpoly(range(len(rsi) - 10, len(rsi))))
    #
    # obv = talib.OBV(closes, quantities)
    # ax[3].plot(obv)

    _, _, macdhist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
    ax[3].plot(macdhist)  # sell when intersects zero from top, buy when intersects zero from bottom
    plt.savefig("graph.png", dpi=400)

