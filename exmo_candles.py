# -*- coding: utf-8 -*-
import numpy
import talib
import requests
import json
import time

from matplotlib.finance import candlestick2_ohlc
import matplotlib.animation as animation

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

BEAR_PERC = 70
BULL_PERC = 30

PERIOD = 5  # Период в минутах для построения свечей

PAIR = 'BTC_USD'

SHOW_BOT_CHART = False

fig, ax = plt.subplots(3, sharex=True)
fig.comment = plt.figtext(.7, .05, '')


def update_graph(interval):
    resource = requests.get('https://api.exmo.com/v1/trades/?pair=%s&limit=10000' % PAIR)
    print(resource.text[:100])
    # return
    data = json.loads(resource.text)

    chart_data = {}  # сформируем словарь с ценой закрытия по PERIOD минут

    for item in reversed(data[PAIR]):
        d = int(float(item['date']) / (PERIOD * 60)) * (PERIOD * 60)  # Округляем время сделки до PERIOD минут
        if not d in chart_data:
            chart_data[d] = {'open': 0, 'close': 0, 'high': 0, 'low': 0}

        chart_data[d]['close'] = float(item['price'])

        if not chart_data[d]['open']:
            chart_data[d]['open'] = float(item['price'])

        if not chart_data[d]['high'] or chart_data[d]['high'] < float(item['price']):
            chart_data[d]['high'] = float(item['price'])

        if not chart_data[d]['low'] or chart_data[d]['low'] > float(item['price']):
            chart_data[d]['low'] = float(item['price'])

    quotes = {}
    quotes['open'] = numpy.asarray([chart_data[item]['open'] for item in sorted(chart_data)])
    quotes['close'] = numpy.asarray([chart_data[item]['close'] for item in sorted(chart_data)])
    quotes['high'] = numpy.asarray([chart_data[item]['high'] for item in sorted(chart_data)])
    quotes['low'] = numpy.asarray([chart_data[item]['low'] for item in sorted(chart_data)])

    xdate = [datetime.fromtimestamp(item) for item in sorted(chart_data)]

    ax[0].xaxis.set_major_locator(ticker.MaxNLocator(6))

    def chart_date(x, pos):
        try:
            return xdate[int(x)]
        except IndexError:
            return ''

    ax[0].clear()
    ax[0].xaxis.set_major_formatter(ticker.FuncFormatter(chart_date))

    candlestick2_ohlc(ax[0], quotes['open'], quotes['high'], quotes['low'], quotes['close'], width=0.6)

    fig.autofmt_xdate()
    fig.tight_layout()

    macd, macdsignal, macdhist = talib.MACD(quotes['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    ax[1].clear()
    ax[1].plot(macd, color="y")
    ax[1].plot(macdsignal)

    idx = numpy.argwhere(numpy.diff(numpy.sign(macd - macdsignal)) != 0).reshape(-1) + 0

    inters = []

    for offset, elem in enumerate(macd):
        if offset in idx:
            inters.append(elem)
        else:
            inters.append(numpy.nan)
    ax[1].plot(inters, 'ro')

    max_v = 0
    hist_data = []

    for offset, elem in enumerate(macdhist):
        activity_time = False
        curr_v = macd[offset] - macdsignal[offset]
        if abs(curr_v) > abs(max_v):
            max_v = curr_v
        perc = curr_v / max_v

        if ((macd[offset] > macdsignal[offset] and perc * 100 > BULL_PERC)  # восходящий тренд
            or (
                            macd[offset] < macdsignal[offset] and perc * 100 < (100 - BEAR_PERC)
            )

            ):
            v = 1
            activity_time = True
        else:
            v = 0

        if offset in idx and not numpy.isnan(elem):
            # тренд изменился
            max_v = curr_v = 0  # обнуляем пик спреда между линиями

        hist_data.append(v * 1000)

    ax[2].fill_between([x for x in range(len(macdhist))], 0, hist_data if SHOW_BOT_CHART else macdhist,
                       facecolor='gray', interpolate=True)
    plt.gcf().texts.remove(fig.comment)
    fig.comment = plt.figtext(.6, .05, '%s %s%s' % (PAIR, time.ctime(), ' ТОРГУЕМ!!!! ' if activity_time else ''),
                              style='italic',
                              bbox={'facecolor': 'red' if activity_time else 'green', 'alpha': 0.5, 'pad': 10})


ani = animation.FuncAnimation(fig, update_graph, interval=1000)
plt.show()