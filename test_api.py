from exmo_api import ExmoAPI
from settings import *

api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER)
print(api.query('order_book', dict(pair=','.join(PAIRS), limit=10)))
print(api.query('trades', dict(pair=','.join(PAIRS), limit=10)))
