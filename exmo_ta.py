# -*- coding: utf-8 -*-
import numpy
import talib
from pprint import pprint

from mpl_finance import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR
from exmo_api import ExmoAPI

api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER)

result = api.query('trades', dict(pair=PAIR, limit=7000))
if result.get(PAIR):
    chart_data = {}  # сформируем словарь с ценой закрытия по PERIOD минут

    for item in reversed(result[PAIR]):
        print(item)
        d = int(float(item['date']) / (PERIOD * 60)) * (PERIOD * 60)  # Округляем время сделки до PERIOD минут
        if not d in chart_data:
            chart_data[d] = {'open': 0, 'close': 0, 'high': 0, 'low': 0, 'quantity': 0.0}

        chart_data[d]['close'] = float(item['price'])
        chart_data[d]['quantity'] += float(item['quantity'])

        if not chart_data[d]['open']:
            chart_data[d]['open'] = float(item['price'])

        if not chart_data[d]['high'] or chart_data[d]['high'] < float(item['price']):
            chart_data[d]['high'] = float(item['price'])

        if not chart_data[d]['low'] or chart_data[d]['low'] > float(item['price']):
            chart_data[d]['low'] = float(item['price'])


    # pprint(chart_data)

    quotes = {}
    quotes['open'] = numpy.asarray([chart_data[item]['open'] for item in sorted(chart_data)])
    quotes['close'] = numpy.asarray([chart_data[item]['close'] for item in sorted(chart_data)])
    quotes['high'] = numpy.asarray([chart_data[item]['high'] for item in sorted(chart_data)])
    quotes['low'] = numpy.asarray([chart_data[item]['low'] for item in sorted(chart_data)])
    quotes['quantity'] = numpy.asarray([chart_data[item]['quantity'] for item in sorted(chart_data)])

    xdate = [datetime.fromtimestamp(item) for item in sorted(chart_data)]

    fig, ax = plt.subplots(6, sharex=True)

    candlestick2_ohlc(ax[0], quotes['open'], quotes['high'], quotes['low'], quotes['close'], width=0.6)

    ax[0].xaxis.set_major_locator(ticker.MaxNLocator(6))


    def chart_date(x, pos):
        try:
            return xdate[int(x)]
        except IndexError:
            return ''

    ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

    fig.autofmt_xdate()
    fig.tight_layout()

    sma = talib.SMA(quotes['close'], timeperiod=50)
    # pprint(sma)
    ax[0].plot(sma)

    ema = talib.EMA(quotes['close'], timeperiod=20)
    ax[0].plot(ema)

    hammer = talib.CDLHAMMER(quotes['open'], quotes['high'], quotes['low'], quotes['close'])
    inverted_hammer = talib.CDLINVERTEDHAMMER(quotes['open'], quotes['high'], quotes['low'], quotes['close'])
    evening_star = talib.CDLEVENINGSTAR(quotes['open'], quotes['high'], quotes['low'], quotes['close'])
    morning_star = talib.CDLMORNINGSTAR(quotes['open'], quotes['high'], quotes['low'], quotes['close'])
    shooting_star = talib.CDLSHOOTINGSTAR(quotes['open'], quotes['high'], quotes['low'], quotes['close'])
    hanging_man = talib.CDLHANGINGMAN(quotes['open'], quotes['high'], quotes['low'], quotes['close'])
    ax[1].plot(hammer)
    ax[1].plot(inverted_hammer)
    ax[1].plot(evening_star)
    ax[1].plot(morning_star)
    ax[1].plot(shooting_star)
    ax[1].plot(hanging_man)

    rsi = talib.RSI(quotes['close'], timeperiod=20)
    ax[2].plot(rsi)

    obv = talib.OBV(quotes['close'], quotes['quantity'])
    ax[3].plot(obv)

    macd, macdsignal, macdhist = talib.MACD(quotes['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    ax[4].plot(macd, color="y")
    ax[4].plot(macdsignal)

    hist_data = []
    for elem in macdhist:
        if not numpy.isnan(elem):
            v = 0 if numpy.isnan(elem) else elem
            hist_data.append(v * 100)
    ax[5].fill_between([x for x in range(len(macdhist))], 0, macdhist)

    plt.savefig("graph.png", dpi=300)

