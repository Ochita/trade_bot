# -*- coding: utf-8 -*-
import numpy
import talib
import requests
import json
import time

from matplotlib.finance import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import datetime as datetime

start_time = time.time() - 24*60*60
resource = requests.get("https://poloniex.com/public?command=returnChartData&currencyPair=BTC_ETH&start=%s&end=9999999999&period=300" % start_time)
data = json.loads(resource.text)

quotes = {}
quotes['open']=numpy.asarray([item['open'] for item in data])
quotes['close']=numpy.asarray([item['close'] for item in data])
quotes['high']=numpy.asarray([item['high'] for item in data])
quotes['low']=numpy.asarray([item['low'] for item in data])

xdate=[datetime.datetime.fromtimestamp(item['date']) for item in data]

fig, ax = plt.subplots(3, sharex=True)

candlestick2_ohlc(ax[0], quotes['open'],quotes['high'],quotes['low'],quotes['close'],width=0.6)

ax[0].xaxis.set_major_locator(ticker.MaxNLocator(6))

def chart_date(x,pos):
    try:
        return xdate[int(x)]
    except IndexError:
        return ''

ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

fig.autofmt_xdate()
fig.tight_layout()

sma = talib.SMA(quotes['close'], timeperiod=50)
ax[0].plot(sma)

ema = talib.EMA(quotes['close'], timeperiod=20)
ax[0].plot(ema)

macd, macdsignal, macdhist = talib.MACD(quotes['close'], fastperiod=12, slowperiod=26, signalperiod=9)
ax[1].plot(macd, color="y")
ax[1].plot(macdsignal)

hist_data = []
for elem in macdhist:
    if not numpy.isnan(elem):
        v = 0 if numpy.isnan(elem) else elem
        hist_data.append(v*100)
ax[2].fill_between([x for x in range(len(macdhist))], 0,macdhist)

plt.show()
