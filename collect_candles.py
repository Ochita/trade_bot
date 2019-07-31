# -*- coding: utf-8 -*-
from exmo_api import ExmoAPI
from pymongo import MongoClient
from settings import *
import datetime
from operator import itemgetter

collection_prefix = "candles_{0}"


def process_trade(trade):
    trade["price"] = float(trade["price"])
    trade["amount"] = float(trade["amount"])
    trade["quantity"] = float(trade["quantity"])
    return trade


def get_current_candle(timestamp, candles_cache, db, pair):
    new_candle = False
    period = timestamp // 1800
    candle = candles_cache.get(period)
    if not candle:
        candle = db[collection_prefix.format(pair)].find_one({"period": period})
    if not candle:
        dt = datetime.datetime.fromtimestamp(timestamp)
        dt = dt.replace(minute=15 if dt.minute < 30 else 45, second=0, microsecond=0)
        candle = dict(datetime=dt, period=period, high=0, low=2147483647, open=0, close=0, volume=0, last_tmstmp=0)
        new_candle = True
        db[collection_prefix.format(pair)].insert(candle)
    candles_cache[period] = candle
    return candle, new_candle


def fill_candle(candle, is_new, trade):
    if trade["date"] > candle["last_tmstmp"]:
        if candle["high"] < trade["price"]:
            candle["high"] = trade["price"]
        if candle["low"] > trade["price"]:
            candle["low"] = trade["price"]
        if is_new:
            candle["open"] = trade["price"]
        candle["close"] = trade["price"]
        candle["volume"] += trade["quantity"]
        candle["last_tmstmp"] = trade["date"]


if __name__ == "__main__":
    api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER)
    db = MongoClient(DB_URL)[DB_NAME]
    result = api.query('trades', dict(pair=','.join(PAIRS), limit=10000))
    print(len(result["ZEC_BTC"]))
    for pair in PAIRS:
        trades = result[pair]
        trades = sorted(trades, key=itemgetter("date"))
        candles_cache = dict()
        for trade in trades:
            trade = process_trade(trade)
            candle, is_new = get_current_candle(trade["date"], candles_cache, db, pair)
            fill_candle(candle, is_new, trade)
        for key in candles_cache.keys():
            db[collection_prefix.format(pair)].update({"period": key}, {"$set": candles_cache[key]})
