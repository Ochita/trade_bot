# -*- coding: utf-8 -*-
import numpy

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
from mpl_finance import candlestick2_ohlc
from talib import CDLHAMMER, CDLINVERTEDHAMMER, CDLEVENINGSTAR, CDLMORNINGSTAR, CDLSHOOTINGSTAR, \
    CDLHANGINGMAN, CDLENGULFING, SMA, EMA, RSI, MACD,OBV
from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR
from exmo_api import ExmoAPI

api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER, PERIOD)

opens, hights, lows, closes, quantities, dates = api.get_candles_data(pair=PAIR)
xdate = [datetime.fromtimestamp(item) for item in sorted(dates)]

plt.rcParams["figure.figsize"] = [22, 20]
fig, ax = plt.subplots(5, sharex='all')

ax[0].xaxis.set_major_locator(ticker.MaxNLocator(60))

ax[0].grid(color='r', linestyle='-', linewidth=0.6)
ax[0].yaxis.set_major_locator(ticker.MaxNLocator(25))

ax[1].grid(color='r', linestyle='-', linewidth=0.6)
ax[1].yaxis.set_major_locator(ticker.MaxNLocator(25))

ax[2].grid(color='r', linestyle='-', linewidth=0.6)
ax[2].yaxis.set_major_locator(ticker.MaxNLocator(25))

ax[3].grid(color='r', linestyle='-', linewidth=0.6)
ax[3].yaxis.set_major_locator(ticker.MaxNLocator(25))

ax[4].grid(color='r', linestyle='-', linewidth=0.6)
ax[4].yaxis.set_major_locator(ticker.MaxNLocator(25))

candlestick2_ohlc(ax[0], opens, hights, lows, closes, width=1)


def chart_date(x, pos):
    try:
        return xdate[int(x)]
    except IndexError:
        return ''


ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

fig.autofmt_xdate()
fig.tight_layout()

sma = SMA(closes, timeperiod=50)
ax[0].plot(sma)

ema = EMA(closes, timeperiod=20)
ax[0].plot(ema)

trend = numpy.polyfit(range(len(closes) - 10, len(closes)), closes[-10:], 1)
trendpoly = numpy.poly1d(trend)
ax[0].plot(range(len(closes) - 10, len(closes)), trendpoly(range(len(closes) - 10, len(closes))))

args = (opens, hights, lows, closes)

hammer = CDLHAMMER(*args)  # will go up
inverted_hammer = CDLINVERTEDHAMMER(*args)  # will go up
evening_star = CDLEVENINGSTAR(*args)  # will go down
morning_star = CDLMORNINGSTAR(*args)  # will go up
shooting_star = CDLSHOOTINGSTAR(*args)  # will go down
hanging_man = CDLHANGINGMAN(*args)  # will go down
engulfing = CDLENGULFING(*args)
ax[1].plot(hammer)
ax[1].plot(inverted_hammer)
ax[1].plot(evening_star)
ax[1].plot(morning_star)
ax[1].plot(shooting_star)
ax[1].plot(hanging_man)
ax[1].plot(engulfing)

rsi = RSI(closes, timeperiod=20)
ax[2].plot(rsi)
rsi_trend = numpy.polyfit(range(len(rsi) - 10, len(rsi)), rsi[-10:], 1)
rsi_trendpoly = numpy.poly1d(rsi_trend)
ax[2].plot(range(len(rsi) - 10, len(rsi)), rsi_trendpoly(range(len(rsi) - 10, len(rsi))))

obv = OBV(closes, quantities)
ax[3].plot(obv)

_, _, macdhist = MACD(closes, fastperiod=10, slowperiod=30, signalperiod=5)
ax[4].plot(macdhist)  # sell when intersects zero from top, buy when intersects zero from bottom
plt.savefig("ta_graph.png", dpi=200)
