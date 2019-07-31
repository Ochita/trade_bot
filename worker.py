import asyncio
import logging
from api import ExmoAPI
from settings import EXMO_API_VER, EXMO_URL, EXMO_API_KEY, EXMO_API_SECRET
from motor.motor_asyncio import AsyncIOMotorClient
from settings import DB_URL, DB_NAME
from settings import PAIRS
import datetime


def avg_counter(count, current, new_val):
    return (count * current + new_val) / (count + 1)


async def collect_data(api, db):
    state = await db.statistics.find_one({"current": True})
    result = await api.query('order_book', dict(pair=','.join(PAIRS), limit=10))
    if result:
        reinit = not state or (datetime.datetime.now() - state['date'] > datetime.timedelta(minutes=1))
        data = dict()
        for pair in result.keys():
            data[pair] = dict()
            sell_quantity = float(result[pair]['ask_quantity'])
            buy_quantity = float(result[pair]['bid_quantity'])
            sell_price = float(result[pair]["ask_top"])
            buy_price = float(result[pair]["bid_top"])
            if reinit:
                data[pair]['start'] = dict(sell_quantity=sell_quantity,
                                           buy_quantity=buy_quantity,
                                           sell_price=sell_price,
                                           buy_price=buy_price)
                data[pair]['avg'] = dict(sell_quantity=sell_quantity,
                                         buy_quantity=buy_quantity,
                                         sell_price=sell_price,
                                         buy_price=buy_price)
            else:
                data[pair]['start'] = state[pair]['start']
                avg = state[pair]['avg']
                data[pair]['avg'] = dict(
                    sell_quantity=avg_counter(state["counter"], avg['sell_quantity'], sell_quantity),
                    buy_quantity=avg_counter(state["counter"], avg['buy_quantity'], buy_quantity),
                    sell_price=avg_counter(state["counter"], avg['sell_price'], sell_price),
                    buy_price=avg_counter(state["counter"], avg['buy_price'], buy_price))
            data[pair]['end'] = dict(sell_quantity=sell_quantity,
                                     buy_quantity=buy_quantity,
                                     sell_price=sell_price,
                                     buy_price=buy_price)
        if reinit:
            data["counter"] = 1
            data['date'] = datetime.datetime.now()
            data["current"] = True
            if state:
                await db.statistics.update_one({"current": True}, {"$set": {"current": False}})
        else:
            data["counter"] = state["counter"] + 1
        await db.statistics.update_one({"current": True}, {"$set": data}, upsert=True)


async def run():
    api = ExmoAPI(EXMO_API_KEY, EXMO_API_SECRET, EXMO_URL, EXMO_API_VER)
    db = AsyncIOMotorClient(DB_URL)[DB_NAME]
    while True:
        await collect_data(api, db)
        await asyncio.sleep(5, loop=loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    logging.basicConfig(level=logging.INFO)
    task = loop.create_task(run())
    loop.run_forever()
