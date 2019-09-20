from signals import Analyser
from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR, DEAL_SIZE, COMMISSION
from exmo_api import ExmoAPI


class TradeBot(object):
    def __init__(self, api, analyser, period, pair, deal_size, commission):
        self.pair = pair
        self.api = api
        self.analyser = analyser
        self.last_deal_price = self.api.get_last_deal_price(self.pair)
        self.balance = self.api.get_balance(self.pair)
        self.period = period
        self.deal_size = deal_size
        self.commission = commission

    def get_signals_deal_direction(self):
        deals = self.api.get_deals(pair=self.pair, limit=10000)
        args = self.api.process_deals(deals)
        signal = self.analyser.get_signal(*args)
        if signal > 0.8:
            return 1
        if signal < -0.8:
            return -1
        return 0

    def check_deal_possibility(self, direction):
        if direction == -1:
            return self.balance[0] > self.deal_size
        elif direction == 1:
            amount = self.api.get_deal_amount(self.pair, self.deal_size)
            return self.balance[1] > amount
        return False

    def check_deal_profitability(self, direction):
        price = self.api.get_current_price(self.pair)
        if direction == -1:
            if price > self.last_deal_price:
                return price - 2 * price * self.commission > self.last_deal_price
        elif direction == 1:
            if price < self.last_deal_price:
                return self.last_deal_price - 2 * price * self.commission > price
        return False

    def run(self):
        direction = self.get_signals_deal_direction()
        if direction != 0 and self.check_deal_possibility(direction) and self.check_deal_profitability(direction):
            if self.api.make_deal(self.pair, self.deal_size, direction):
                self.last_deal_price = self.api.get_last_deal_price()


if __name__ == '__main__':
    # Init
    api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER)
    analyser = Analyser()
    tb = TradeBot(api, analyser, PERIOD, PAIR, DEAL_SIZE, COMMISSION)
