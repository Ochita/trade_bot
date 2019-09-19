import numpy
import talib

from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET, PERIOD, PAIR
from exmo_api import ExmoAPI


if __name__ == '__main__':
    # Init
    api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER)

    # Get balance for selected pairs

    # TA and make decision for selected pairs

    # Make deals for selected pairs (instant trade by market price)
