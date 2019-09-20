# -*- coding: utf-8 -*-
import numpy

from mpl_finance import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
from signals import Analyser

from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR
from exmo_api import ExmoAPI

api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER, PERIOD)

opens, hights, lows, closes, quantities, dates = api.get_candles_data(pair=PAIR)
xdate = [datetime.fromtimestamp(item) for item in sorted(dates)]

plt.rcParams["figure.figsize"] = [22, 16]

fig, ax = plt.subplots(3, sharex='all')

ax[0].xaxis.set_major_locator(ticker.MaxNLocator(60))

ax[0].grid(color='r', linestyle='-', linewidth=0.6)
ax[0].yaxis.set_major_locator(ticker.MaxNLocator(25))

candlestick2_ohlc(ax[0], opens, hights, lows, closes, width=1)

ax[1].grid(color='r', linestyle='-', linewidth=0.6)
ax[1].yaxis.set_major_locator(ticker.MaxNLocator(25))

ax[2].grid(color='r', linestyle='-', linewidth=0.6)
ax[2].yaxis.set_major_locator(ticker.MaxNLocator(25))


def chart_date(x, pos):
    try:
        return xdate[int(x)]
    except IndexError:
        return ''


ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

fig.autofmt_xdate()
fig.tight_layout()

candles_signal = list()
sma_ema_signal = list()
rsi_signal = list()
macd_signal = list()
obv_signal = list()

for x in range(101):
    candles_signal.append(0)
    sma_ema_signal.append(0)
    rsi_signal.append(0)
    macd_signal.append(0)
    obv_signal.append(0)

taanal = Analyser()

for x in range(101, len(xdate)):
    candles_signal.append(taanal.get_candles_signal(opens[:x], hights[:x], lows[:x], closes[:x], dates[:x]))
    sma_ema_signal.append(taanal.get_sma_ema_signal(closes[:x]))
    rsi_signal.append(taanal.get_rsi_signal(closes[:x]))
    macd_signal.append(taanal.get_macd_signal(closes[:x]))
    obv_signal.append(taanal.get_obv_signal(closes[:x], quantities[:x]))

ax[1].plot(candles_signal)  # blue
ax[1].plot(sma_ema_signal)  # orange
ax[1].plot(rsi_signal)  # green
ax[1].plot(macd_signal)  # red
ax[1].plot(obv_signal)  # purple

signal = numpy.sum([candles_signal, sma_ema_signal, rsi_signal, macd_signal, obv_signal], 0)

ax[2].plot(signal)


def get_command(sig):
    if sig > 0.80:
        return 1
    if sig < -0.80:
        return -1
    return 0


buy_sell = list(map(get_command, signal))

ax[2].plot(buy_sell)

plt.savefig("signals_graph.png", dpi=200)

