# -*- coding: utf-8 -*-
import talib
import numpy
import time
import datetime

class TAAnalyser(object):

    def __init__(self, opens, hights, lows, closes, quantities, dates):
        self.candle_args = (opens, hights, lows, closes)
        self.closes_arg = closes
        self.quantities_arg = quantities
        self.dates = dates

    def get_candles_signal(self):
        # - 100 if sell 100 if by
        hammer = talib.CDLHAMMER(*self.candle_args)
        inverted_hammer = talib.CDLINVERTEDHAMMER(*self.candle_args)
        evening_star = talib.CDLEVENINGSTAR(*self.candle_args)
        morning_star = talib.CDLMORNINGSTAR(*self.candle_args)
        shooting_star = talib.CDLSHOOTINGSTAR(*self.candle_args)
        hanging_man = talib.CDLHANGINGMAN(*self.candle_args)
        engulfing = talib.CDLENGULFING(*self.candle_args)

        now = time.time()
        scaler = lambda x: (x - now + 60 * 60)/(60 * 60)  # 1 hour minutes gap
        vectorized_scaler = numpy.vectorize(scaler)
        dates_scale = vectorized_scaler(self.dates).clip(0, 1)

        m = numpy.array([hammer, inverted_hammer, evening_star, morning_star, shooting_star, hanging_man, engulfing])
        signals = numpy.sum(m, 0)
        scaled_signals = numpy.multiply(signals, dates_scale)
        m_sig = numpy.max(numpy.abs(scaled_signals))
        if m_sig > 0:
            normalized_signals = numpy.true_divide(scaled_signals, m_sig)
            return numpy.sum(normalized_signals, 0)
        else:
            return 0.0

    def get_sma_ema_signal(self):
        pass

    def get_rsi_signal(self):
        rsi = talib.RSI(self.closes_arg, timeperiod=20)
        meaning_rsi = rsi[-10:]
        rsi_avg = numpy.average(meaning_rsi)
        signal_part1 = 0
        if rsi_avg < 30:
            signal_part1 = rsi_avg / 60
        elif rsi_avg > 70:
            signal_part1 = - (100 - rsi_avg / 60)

        meaning_closes = self.closes_arg[-10:]
        rsi_trend = numpy.polyfit(range(10), meaning_rsi, 1)
        price_trend = numpy.polyfit(range(10), meaning_closes, 1)
        print(rsi_trend)
        print(price_trend)

        return signal_part1
