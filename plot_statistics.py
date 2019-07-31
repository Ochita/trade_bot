from pymongo import MongoClient
from settings import DB_URL, DB_NAME
from settings import PAIRS
import matplotlib.pyplot as plt


def get_point_type(start, avg, end, key):
    if start[key] < avg[key] > end[key]:
        return -1
    if start[key] < avg[key] < end[key]:
        return 2
    if start[key] > avg[key] > end[key]:
        return -2
    if start[key] > avg[key] < end[key]:
        return 1
    return 0


def normalize(points, max_x):
    for pair in PAIRS:
        for point in points[pair]:
            point["value"] = point["value"] / max_x[pair]


def draw(points, pair, color):
    for point in points[pair]:
        if point["type"] == 2:
            marker = "^"
        if point["type"] == 1:
            marker = "2"
        if point["type"] == 0:
            marker = "o"
        if point["type"] == -1:
            marker = "1"
        if point["type"] == -2:
            marker = "v"
        plt.scatter(point["date"], point["value"], c=color, marker=marker)


def draw_delta(up, bot, pair):
    for x in range(len(up[pair])):
        plt.scatter(up[pair][x]["date"], up[pair][x]["value"] - bot[pair][x]["value"]+0.79, c="m")


if __name__ == "__main__":
    db = MongoClient(DB_URL)[DB_NAME]
    sq_points = dict()
    bq_points = dict()
    sp_points = dict()
    bp_points = dict()
    max_sq = dict()
    max_bq = dict()
    max_sp = dict()
    max_bp = dict()
    for pair in PAIRS:
        sq_points[pair] = list()
        bq_points[pair] = list()
        sp_points[pair] = list()
        bp_points[pair] = list()
        max_sq[pair] = 0
        max_bq[pair] = 0
        max_sp[pair] = 0
        max_bp[pair] = 0
    for point in db.statistics.find({"current": False}):
        for pair in PAIRS:
            pair_point_start = point[pair]["start"]
            pair_point_avg = point[pair]["avg"]
            pair_point_end = point[pair]["end"]
            if max_sq[pair] < pair_point_start["sell_quantity"]:
                max_sq[pair] = pair_point_start["sell_quantity"]
            if max_bq[pair] < pair_point_start["buy_quantity"]:
                max_bq[pair] = pair_point_start["buy_quantity"]
            if max_sp[pair] < pair_point_start["sell_price"]:
                max_sp[pair] = pair_point_start["sell_price"]
            if max_bp[pair] < pair_point_start["buy_price"]:
                max_bp[pair] = pair_point_start["buy_price"]
            sq_point = dict(date=point["date"], value=pair_point_avg["sell_quantity"],
                            type=get_point_type(pair_point_start, pair_point_avg, pair_point_end, "sell_quantity"))
            bq_point = dict(date=point["date"], value=pair_point_avg["buy_quantity"],
                            type=get_point_type(pair_point_start, pair_point_avg, pair_point_end, "buy_quantity"))
            sp_point = dict(date=point["date"], value=pair_point_avg["sell_price"],
                            type=get_point_type(pair_point_start, pair_point_avg, pair_point_end, "sell_price"))
            bp_point = dict(date=point["date"], value=pair_point_avg["buy_price"],
                            type=get_point_type(pair_point_start, pair_point_avg, pair_point_end, "buy_price"))
            sq_points[pair].append(sq_point)
            bq_points[pair].append(bq_point)
            sp_points[pair].append(sp_point)
            bp_points[pair].append(bp_point)
    max_q = dict()
    max_p = dict()
    for pair in PAIRS:
        if max_sq[pair] > max_bq[pair]:
            max_q[pair] = max_sq[pair]
        else:
            max_q[pair] = max_bq[pair]
        if max_sp[pair] > max_bp[pair]:
            max_p[pair] = max_sp[pair]
        else:
            max_p[pair] = max_bp[pair]
    normalize(sq_points, max_q)
    normalize(bq_points, max_q)
    normalize(sp_points, max_p)
    normalize(bp_points, max_p)
    fig = plt.figure()
    draw(sq_points, "ZEC_BTC", "b")
    draw(bq_points, "ZEC_BTC", "c")
    draw(sp_points, "ZEC_BTC", "g")
    draw(bp_points, "ZEC_BTC", "r")
    draw_delta(sq_points, bq_points, "ZEC_BTC")
    plt.show()
