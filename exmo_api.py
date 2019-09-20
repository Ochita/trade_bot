import hashlib
import hmac
import time
import requests
import json
import numpy
from urllib.parse import urlencode

COMMISSION = 0.002


class ExmoAPI(object):
    def __init__(self, api_key, api_secret, api_url='api.exmo.com', api_version='v1', period=5):
        self.api_url = api_url
        self.api_version = api_version
        self.api_key = api_key
        self.api_secret = bytes(api_secret, encoding='utf-8')
        self.period = period

    def sha512(self, data):
        h = hmac.new(key=self.api_secret, digestmod=hashlib.sha512)
        h.update(data.encode('utf-8'))
        return h.hexdigest()

    def query(self, api_method, params=None):
        params = params if params else dict()
        params['nonce'] = int(round(time.time() * 1000))
        params = urlencode(params)
        sign = self.sha512(params)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Key": self.api_key,
            "Sign": sign
        }
        result = requests.post("https://{0}/{1}/{2}".format(self.api_url, self.api_version, api_method),
                               data=params, headers=headers)
        return result.json()

    def get_deals(self, pair, limit):
        result = self.query('trades', dict(pair=pair, limit=limit))
        return result.get(pair, [])

    def process_deals(self, items):
        dates_acc = {}
        for item in reversed(items):
            price = float(item['price'])
            quantity = float(item['quantity'])
            d = int(float(item['date']) / (self.period * 60)) * (self.period * 60)  # Round to PERIOD minutes

            if d not in dates_acc:
                dates_acc[d] = {'open': 0, 'close': 0, 'high': 0, 'low': 2147483647, 'quantity': 0.0}

            dates_acc[d]['close'] = price

            dates_acc[d]['quantity'] += quantity

            if not dates_acc[d]['open']:
                dates_acc[d]['open'] = price

            if dates_acc[d]['high'] < price:
                dates_acc[d]['high'] = price

            if dates_acc[d]['low'] > price:
                dates_acc[d]['low'] = price

        after_sort = sorted(dates_acc)
        opens = numpy.asarray([dates_acc[item]['open'] for item in after_sort])
        closes = numpy.asarray([dates_acc[item]['close'] for item in after_sort])
        hights = numpy.asarray([dates_acc[item]['high'] for item in after_sort])
        lows = numpy.asarray([dates_acc[item]['low'] for item in after_sort])
        quantities = numpy.asarray([dates_acc[item]['quantity'] for item in after_sort])
        dates = [item for item in after_sort]

        return opens, hights, lows, closes, quantities, dates

    def get_candles_data(self, pair):
        return self.process_deals(self.get_deals(pair, 10000))

    def get_balance(self, pair):
        resp = self.query('user_info')
        balances = resp['balances']
        p = pair.split('_')
        cur1 = p[0]
        cur2 = p[1]
        return balances[cur1], balances[cur2]

    def get_last_deal_price(self, pair):
        resp = self.query('user_trades', dict(pair=pair, offset=0, limit=3))
        deals = resp[pair]
        if not deals:
            return self.get_current_price(pair)
        else:
            return deals[0]['price']

    def get_current_price(self, pair):
        resp = self.query('required_amount', dict(pair=pair, quantity=1))
        return float(resp['avg_price'])

    def get_deal_amount(self, pair, quantity):
        resp = self.query('required_amount', dict(pair=pair, quantity=quantity))
        return float(resp['amount'])

    def make_deal(self, pair, quantity, direction):
        if direction == 1:
            tp = 'market_buy'
        elif direction == -1:
            tp = "market_sell"
        else:
            return False
        resp = self.query('order_create', dict(pair=pair, quantity=quantity, type=tp))
        return resp.get('result', False)


# UNCOMPLETED TRASH
class FakeExmoAPI(ExmoAPI):
    def make_deal(self, pair, quantity, direction, price=None):
        if not price:
            response = self.query('required_amount', dict(pair=pair, quantity=quantity))
            amount = float(response['amount'])
        else:
            amount = quantity * price
        p = pair.split('_')
        cur1 = p[0]
        cur2 = p[1]
        with open('balance.js') as json_file:
            data = json.load(json_file)
        # print(data)
        print(price)
        print(direction)
        if direction < 0:  #  sell
            # if data[cur1] < quantity:
            #     return False
            data[cur1] -= quantity
            data[cur2] += (amount - amount * COMMISSION)
        else:      #  buy
            # if data[cur2] < amount:
            #     return False
            data[cur1] += (quantity - quantity * COMMISSION)
            data[cur2] -= amount
        with open('balance.js', 'w') as json_file:
            json.dump(data, json_file)

    def convert_all(self, pair, price=None):
        with open('balance.js') as json_file:
            data = json.load(json_file)
        p = pair.split('_')
        cur1 = p[0]
        cur2 = p[1]
        # if not price:
        #     response = self.query('required_amount', dict(pair=pair, quantity=data[cur1]))
        #     amount = float(response['amount'])
        # else:
        #     amount = data[cur1] * price
        # # sell
        # data[cur1] -= data[cur1]
        # data[cur2] += (amount - amount *
        data[cur1] += data[cur2] / price
        data[cur2] = 0
        with open('balance.js', 'w') as json_file:
            json.dump(data, json_file)

    def get_balance(self, pair):
        with open('balance.js') as json_file:
            data = json.load(json_file)
        p = pair.split('_')
        cur1 = p[0]
        cur2 = p[1]
        return (data[cur1], data[cur2])
