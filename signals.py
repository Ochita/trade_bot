# -*- coding: utf-8 -*-
import numpy
from talib import CDLHAMMER, CDLINVERTEDHAMMER, CDLEVENINGSTAR, CDLMORNINGSTAR, CDLSHOOTINGSTAR, \
    CDLHANGINGMAN, CDLENGULFING, SMA, EMA, RSI, MACD,OBV


class Analyser(object):

    def __init__(self, hyper_options=None):
        if not hyper_options:
            hyper_options = dict()
        self.candle_scaler_lifetime = hyper_options.get('candle_scaler_lifetime', 60)  # in minutes
        self.last_periods = hyper_options.get('last_periods', 10)
        self.obv_delay = hyper_options.get('obv_delay', 20)
        self.obv_long_trend_periods = hyper_options.get('obv_long_trend_periods', 100)

    def get_candles_signal(self, opens, hights, lows, closes, dates):
        candle_args = (opens, hights, lows, closes)
        # - 100 if sell 100 if by
        hammer = CDLHAMMER(*candle_args)  # 0 ; 100
        inverted_hammer = CDLINVERTEDHAMMER(*candle_args)  # 0 ; 100
        morning_star = CDLMORNINGSTAR(*candle_args)  # 0 ; 100
        evening_star = CDLEVENINGSTAR(*candle_args)  # -100 ; 0
        shooting_star = CDLSHOOTINGSTAR(*candle_args)  # -100 ; 0
        hanging_man = CDLHANGINGMAN(*candle_args)  # -100 ; 0
        engulfing = CDLENGULFING(*candle_args)  # -100 ; 100

        last_date = dates[-1]

        def scaler(x):
            cslt = self.candle_scaler_lifetime * 60  # get seconds
            return (x - last_date + cslt) / cslt  # reduce meaning of old pattern

        vectorized_scaler = numpy.vectorize(scaler)
        dates_scale = vectorized_scaler(dates).clip(0, 1)  # scale positives and drop negatives

        m = numpy.array([hammer, inverted_hammer, evening_star, morning_star, shooting_star, hanging_man, engulfing])
        signals = numpy.true_divide(numpy.sum(m, 0), 300)  # half candle up and half candle down and one up-down
        scaled_signals = numpy.multiply(signals, dates_scale)
        return numpy.sum(scaled_signals, 0)

    def get_sma_ema_signal(self, closes):
        sma = SMA(closes, timeperiod=50)
        ema = EMA(closes, timeperiod=20)

        last_sma = sma[-self.last_periods:]
        last_ema = ema[-self.last_periods:]

        sma_trend = numpy.polyfit(range(self.last_periods), last_sma, 1)
        ema_trend = numpy.polyfit(range(self.last_periods), last_ema, 1)

        sma_rad = numpy.arctan(sma_trend[0])
        ema_rad = numpy.arctan(ema_trend[0])

        diff = numpy.subtract(last_ema, last_sma)

        sma_crossings = numpy.where(numpy.diff(numpy.sign(diff)))[0]

        if len(sma_crossings) > 1:
            return 0
        else:
            rad = ema_rad - sma_rad
            if len(sma_crossings) == 1:
                signal = rad * 1.6
            else:
                signal = rad * 1.4
            if signal > 1:
                signal = 1
            elif signal < -1:
                signal = -1
            return signal

    def get_rsi_signal(self, closes):
        rsi = RSI(closes, timeperiod=20)
        last_rsi = rsi[-self.last_periods:]
        rsi_avg = numpy.average(last_rsi)
        signal_part1 = 0
        if rsi_avg < 30:
            signal_part1 = rsi_avg / 60
        elif rsi_avg > 70:
            signal_part1 = - ((100 - rsi_avg) / 60)

        last_closes = closes[-self.last_periods:]
        rsi_trend = numpy.polyfit(range(self.last_periods), last_rsi, 1)
        price_trend = numpy.polyfit(range(self.last_periods), last_closes, 1)
        rsi_rad = numpy.arctan(rsi_trend[0])
        price_rad = numpy.arctan(price_trend[0])
        signal_part2 = 0
        if rsi_rad < 0 < price_rad:
            signal_part2 = -(price_rad - rsi_rad) / 2.5

        if price_rad < 0 < rsi_rad:
            signal_part2 = (rsi_rad - price_rad) / 2.5

        return signal_part1 + signal_part2

    def get_macd_signal(self, closes):
        _, _, macdhist = MACD(closes, fastperiod=10, slowperiod=30, signalperiod=5)
        last_macdhist = macdhist[-self.last_periods:]
        if last_macdhist[0] < 0 < numpy.average(last_macdhist) < last_macdhist[-1]:
            return 1
        elif last_macdhist[-1] < numpy.average(last_macdhist) < 0 < last_macdhist[0]:
            return -1
        else:
            return 0

    def get_obv_signal(self, closes, quantities):
        obv = OBV(closes, quantities)
        # delay price changing cause obv slower
        last_closes = closes[-(self.last_periods + self.obv_delay):-self.obv_delay]
        lst_obv = obv[-self.last_periods:]

        price_trend = numpy.polyfit(range(self.last_periods), last_closes, 1)
        obv_trend = numpy.polyfit(range(self.last_periods), lst_obv, 1)

        price_rad = numpy.arctan(price_trend[0])
        obv_rad = numpy.arctan(obv_trend[0])

        long_obv_trend = numpy.polyfit(range(self.obv_long_trend_periods), obv[-self.obv_long_trend_periods:], 1)
        long_obv_rad = numpy.arctan(long_obv_trend[0])
        if long_obv_rad < -0.2:
            return -long_obv_rad - 0.1
        elif 0 < obv_rad < price_rad:
            return (obv_rad - price_rad) * 0.6
        return 0

    def get_signal(self, opens, hights, lows, closes, quantities, dates):
        signal = sum([self.get_candles_signal(opens, hights, lows, closes, dates),
                      self.get_sma_ema_signal(closes),
                      self.get_rsi_signal(closes),
                      self.get_macd_signal(closes),
                      self.get_obv_signal(closes, quantities)])
        return signal
