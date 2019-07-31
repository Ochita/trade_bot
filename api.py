import urllib
import hashlib
import hmac
import time
import requests


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

    def query(self, api_method, params=dict()):
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


class FakeExmoAPI(ExmoAPI):
    pass
