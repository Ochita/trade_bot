# -*- coding: utf-8 -*-
from pymongo import MongoClient
from settings import *
import pandas as pd
from stockstats import StockDataFrame

from bokeh.plotting import figure, show, output_file


collection_prefix = "candles_{0}"
candlestick_width = 0.25 * 60 * 60 * 1000

if __name__ == "__main__":
    db = MongoClient(DB_URL)[DB_NAME]
    pair = "ZEC_BTC"
    candles = list(db[collection_prefix.format(pair)].find())
    df_candles = pd.DataFrame(candles)
    print(df_candles.head())
    df = StockDataFrame.retype(df_candles)
    df['macd'] = df.get('macd')  # calculate MACD
    p = figure(x_axis_type="datetime",  sizing_mode="stretch_both", title=pair)
    p.line(df.datetime, df.close, color='black')

    # plot macd strategy
    p.line(df.datetime, 0, color='black')
    p.line(df.datetime, df.macd, color='blue')
    p.line(df.datetime, df.macds, color='orange')
    p.vbar(x=df.datetime, bottom=[0 for _ in df.datetime], top=df.macdh, width=4, color="purple")

    inc = df.close > df.open
    dec = df.open > df.close

    # plot candlesticks
    p.segment(df.datetime[inc], df.high[inc],
              df.datetime[inc], df.low[inc], color="blue", line_width=3)
    p.vbar(df.datetime[inc], candlestick_width, df.open[inc],
           df.close[inc], fill_color="blue", line_color="blue")
    p.segment(df.datetime[dec], df.high[dec],
              df.datetime[dec], df.low[dec], color="red", line_width=3)
    p.vbar(df.datetime[dec], candlestick_width, df.open[dec],
           df.close[dec], fill_color="red", line_color="red")

    output_file("visualizing_trading_strategy.html", title="visualizing trading strategy")
    show(p)
