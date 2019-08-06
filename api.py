import urllib
import hashlib
import hmac
import time
import requests
import json

COMMISSION = 0.002


class API(object):
    def get_deals(self, pair, limit):
        raise NotImplementedError


class ExmoAPI(API):
    def __init__(self, API_KEY, API_SECRET, API_URL='api.exmo.com', API_VERSION='v1'):
        self.API_URL = API_URL
        self.API_VERSION = API_VERSION
        self.API_KEY = API_KEY
        self.API_SECRET = bytes(API_SECRET, encoding='utf-8')

    def sha512(self, data):
        H = hmac.new(key=self.API_SECRET, digestmod=hashlib.sha512)
        H.update(data.encode('utf-8'))
        return H.hexdigest()

    def query(self, api_method, params=None):
        params = params if params else dict()
        params['nonce'] = int(round(time.time() * 1000))
        params = urllib.parse.urlencode(params)
        sign = self.sha512(params)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Key": self.API_KEY,
            "Sign": sign
        }
        result = requests.post("https://{0}/{1}/{2}".format(self.API_URL, self.API_VERSION, api_method),
                               data=params, headers=headers)
        return result.json()

    def get_deals(self, pair, limit):
        return self.query('trades', dict(pair=pair, limit=limit))

    def make_deal(self, pair, quantity, direction):
        tp = 'market_buy' if direction > 0 else "market_sell"
        self.query('order_create', dict(pair=pair, quantity=quantity, type=tp))


class FakeExmoAPI(ExmoAPI):
    def make_deal(self, pair, quantity, direction):
        response = self.query('required_amount', dict(pair=pair, quantity=quantity))
        amount = float(response['amount'])
        p = pair.split('_')
        cur1 = p[0]
        cur2 = p[1]
        with open('balance.js') as json_file:
            data = json.load(json_file)
        if direction < 0:  #  sell
            data[cur1] -= quantity
            data[cur2] += (amount - amount * COMMISSION)
        else:      #  buy
            data[cur1] += (quantity - quantity * COMMISSION)
            data[cur2] -= amount
        with open('balance.js', 'w') as json_file:
            json.dump(data, json_file)
