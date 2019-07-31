import time
import json
import requests
import urllib, http.client
import hmac, hashlib

# Если нет нужных пакетов - читаем тут: https://bablofil.ru/python-indicators/
import numpy
import talib

from datetime import datetime

# ключи API, которые предоставила exmo
API_KEY = 'K-            кей'
# обратите внимание, что добавлена 'b' перед строкой
API_SECRET = b'S-секрет'

# Список пар, на которые торгуем
MARKETS = [
    'BCH_USD', 'ETC_USD', 'ETH_USD',
    'ZEC_USD', 'DASH_USD'
]

CAN_SPEND = 20  # Сколько USD готовы вложить в бай
MARKUP = 0.001  # 0.001 = 0.1% - Какой навар со сделки хотим получать

STOCK_FEE = 0.002  # Какую комиссию берет биржа
PERIOD = 5  # Период в минутах для построения свечей
ORDER_LIFE_TIME = 0.5  # Через сколько минут отменять неисполненный ордер на покупку 0.5 = 30 сек.

USE_MACD = True  # True - оценивать тренд по MACD, False - покупать и продавать невзирая ни на что

BEAR_PERC = 70  # % что считаем поворотом при медведе (подробности - https://bablofil.ru/macd-python-stock-bot/
BULL_PERC = 99.9  # % что считаем поворотом при быке

# BEAR_PERC = 70  # % что считаем поворотом при медведе
# BULL_PERC = 100  # Так он будет продавать по минималке, как только курс пойдет вверх

API_URL = 'api.exmo.me'
API_VERSION = 'v1'

USE_LOG = False
DEBUG = False  # True - выводить отладочную информацию, False - писать как можно меньше

numpy.seterr(all='ignore')

curr_pair = None


# Свой класс исключений
class ScriptError(Exception):
    pass


class ScriptQuitCondition(Exception):
    pass


# все обращения к API проходят через эту функцию
def call_api(api_method, http_method="POST", **kwargs):
    payload = {'nonce': int(round(time.time() * 1000))}

    if kwargs:
        payload.update(kwargs)
    payload = urllib.parse.urlencode(payload)

    H = hmac.new(key=API_SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": API_KEY,
               "Sign": sign}
    conn = http.client.HTTPSConnection(API_URL, timeout=90)
    conn.request(http_method, "/" + API_VERSION + "/" + api_method, payload, headers)
    response = conn.getresponse().read()

    conn.close()

    try:
        obj = json.loads(response.decode('utf-8'))

        if 'error' in obj and obj['error']:
            raise ScriptError(obj['error'])
        return obj
    except json.decoder.JSONDecodeError:
        raise ScriptError('Ошибка анализа возвращаемых данных, получена строка', response)


# Получаем с биржи данные, необходимые для построения индикаторов
def get_ticks(pair):
    resource = requests.get('https://api.exmo.me/v1/trades/?pair=%s&limit=10000' % pair)
    data = json.loads(resource.text)

    chart_data = {}  # сформируем словарь с ценой закрытия по 5 минут
    for item in reversed(data[pair]):
        d = int(float(item['date']) / (PERIOD * 60)) * (PERIOD * 60)  # Округляем время сделки до PERIOD минут
        chart_data[d] = float(item['price'])
    return chart_data


# С помощью MACD делаем вывод о целесообразности торговли в данный момент (https://bablofil.ru/macd-python-stock-bot/)
def get_macd_advice(chart_data):
    macd, macdsignal, macdhist = talib.MACD(numpy.asarray([chart_data[item] for item in sorted(chart_data)]),
                                            fastperiod=12, slowperiod=26, signalperiod=9)

    idx = numpy.argwhere(numpy.diff(numpy.sign(macd - macdsignal)) != 0).reshape(-1) + 0
    inters = []

    for offset, elem in enumerate(macd):
        if offset in idx:
            inters.append(elem)
        else:
            inters.append(numpy.nan)
    trand = 'BULL' if macd[-1] > macdsignal[-1] else 'BEAR'
    hist_data = []
    max_v = 0
    growing = False
    for offset, elem in enumerate(macdhist):
        growing = False
        curr_v = macd[offset] - macdsignal[offset]
        if abs(curr_v) > abs(max_v):
            max_v = curr_v
        perc = curr_v / max_v

        if ((macd[offset] > macdsignal[offset] and perc * 100 > BULL_PERC)  # восходящий тренд
            or (
                            macd[offset] < macdsignal[offset] and perc * 100 < (100 - BEAR_PERC)
            )

            ):
            v = 1
            growing = True
        else:
            v = 0

        if offset in idx and not numpy.isnan(elem):
            # тренд изменился
            max_v = curr_v = 0  # обнуляем пик спреда между линиями
        hist_data.append(v * 1000)

    return ({'trand': trand, 'growing': growing})


# Выводит всякую информацию на экран, самое важное скидывает в Файл log.txt
def log(*args):
    if USE_LOG:
        l = open("./log.txt", 'a', encoding='utf-8')
        print(datetime.now(), *args, file=l)
        l.close()
    print(datetime.now(), ' ', *args)


# Ф-ция для создания ордера на покупку
def create_buy(pair):
    global USE_LOG
    USE_LOG = True
    log(pair, 'Создаем ордер на покупку')
    log(pair, 'Получаем текущие курсы')

    offers = call_api('order_book', pair=pair)[pair]
    try:
        # current_rate =  float(offers['ask'][0][0]) # покупка по лучшей цене
        current_rate = sum(
            [float(item[0]) for item in offers['ask'][:3]]) / 3  # покупка по средней цене из трех лучших в стакане
        can_buy = CAN_SPEND / current_rate
        print('buy', can_buy, current_rate)
        log(pair, """
            Текущая цена - %0.8f
            На сумму %0.8f %s можно купить %0.8f %s
            Создаю ордер на покупку
            """ % (current_rate, CAN_SPEND, pair[0], can_buy, pair[1])
            )
        new_order = call_api(
            'order_create',
            pair=pair,
            quantity=can_buy,
            price=current_rate,
            type='buy'
        )
        log("Создан ордер на покупку %s" % new_order['order_id'])
    except ZeroDivisionError:
        print('Не удается вычислить цену', prices)
    USE_LOG = False


# Ф-ция для создания ордера на продажу
def create_sell(pair):
    global USE_LOG
    USE_LOG = True
    balances = call_api('user_info')['balances']
    # if float(balances[pair[:-4]]) >= CURRENCY_1_MIN_QUANTITY: # Есть ли в наличии CURRENCY_1, которую можно продать?
    wanna_get = CAN_SPEND + CAN_SPEND * (STOCK_FEE + MARKUP)
    order_amount = float(balances[pair[:-4]])
    new_rate = wanna_get / order_amount
    new_rate_fee = new_rate / (1 - STOCK_FEE)
    offers = call_api('order_book', pair=pair)[pair]
    current_rate = float(offers['bid'][0][0])  # Берем верхнюю цену, по которой кто-то покупает
    choosen_rate = current_rate if current_rate > new_rate_fee else new_rate_fee
    print('sell', balances[pair[:-4]], wanna_get, choosen_rate)
    log(pair, """
    Итого на этот ордер было потрачено %0.8f %s, получено %0.8f %s
    Что бы выйти в плюс, необходимо продать купленную валюту по курсу %0.8f
    Тогда, после вычета комиссии %0.4f останется сумма %0.8f %s
    Итоговая прибыль составит %0.8f %s
    Текущий курс продажи %0.8f
    Создаю ордер на продажу по курсу %0.8f
    """
        % (
            wanna_get, pair[0], order_amount, pair[1],
            new_rate_fee,
            STOCK_FEE, (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE), pair[0],
            (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE) - wanna_get, pair[0],
            current_rate,
            choosen_rate,
        )
        )
    new_order = call_api(
        'order_create',
        pair=pair,
        quantity=balances[pair[:-4]],
        price=choosen_rate,
        type='sell'
    )
    log(pair, "Создан ордер на продажу %s" % new_order['order_id'])
    print(new_order)
    if DEBUG:
        print('Создан ордер на продажу', pair[:-4], new_order['order_id'])
    USE_LOG = False


# Бесконечный цикл процесса - основная логика
while True:
    try:
        for pair in MARKETS:  # Проходим по каждой паре из списка в начале\
            try:
                # Получаем список активных ордеров
                try:
                    opened_orders = call_api('user_open_orders')[pair]
                except KeyError:
                    if DEBUG:
                        print('Открытых ордеров нет')
                        log(pair, "Открытых ордеров нет")
                    opened_orders = []
                sell_orders = []
                # Есть ли неисполненные ордера на продажу CURRENCY_1?
                log(pair, " Обработка...")
                for order in opened_orders:
                    if order['type'] == 'sell':
                        # Есть неисполненные ордера на продажу CURRENCY_1, выход
                        raise ScriptQuitCondition(
                            'Выход, ждем пока не исполнятся/закроются все ордера на продажу (один ордер может быть разбит биржей на несколько и исполняться частями)')
                        # пропуск продажи
                        # pass
                    else:
                        # Запоминаем ордера на покупку CURRENCY_1
                        sell_orders.append(order)
                # Проверяем, есть ли открытые ордера на покупку CURRENCY_1
                if sell_orders:  # открытые ордера есть
                    for order in sell_orders:
                        # Проверяем, есть ли частично исполненные
                        if DEBUG:
                            print('Проверяем, что происходит с отложенным ордером', order['order_id'])
                        try:
                            order_history = call_api('order_trades', order_id=order['order_id'])
                            # по ордеру уже есть частичное выполнение, выход
                            raise ScriptQuitCondition(
                                'Выход, продолжаем надеяться докупить валюту по тому курсу, по которому уже купили часть')
                        except ScriptError as e:
                            if 'Error 50304' in str(e):
                                if DEBUG:
                                    print('Частично исполненных ордеров нет')

                                time_passed = time.time() + STOCK_TIME_OFFSET * 60 * 60 - int(order['created'])

                                if time_passed > ORDER_LIFE_TIME * 60:
                                    log('Пора отменять ордер %s' % order)
                                    # Ордер уже давно висит, никому не нужен, отменяем
                                    call_api('order_cancel', order_id=order['order_id'])
                                    log('Ордер %s отменен' % order)
                                    raise ScriptQuitCondition('Отменяем ордер -за ' + str(
                                        ORDER_LIFE_TIME) + ' минут не удалось купить ' + str(CURRENCY_1))
                                else:
                                    raise ScriptQuitCondition(
                                        'Выход, продолжаем надеяться купить валюту по указанному ранее курсу, со времени создания ордера прошло %s секунд' % str(
                                            time_passed))
                            else:
                                raise ScriptQuitCondition(str(e))
                else:  # Открытых ордеров нет
                    balances = call_api('user_info')['balances']
                    reserved = call_api('user_info')['reserved']
                    min_quantityy = call_api('pair_settings', pair=pair)[pair]
                    CURRENCY_1_MIN_QUANTITY = float(min_quantityy['min_quantity'])
                    if float(balances[pair[
                                      :-4]]) >= CURRENCY_1_MIN_QUANTITY:  # Есть ли в наличии CURRENCY_1, которую можно продать?
                        print('Баланс: ' + str(float(balances[pair[:-4]])) + ' ' + str(pair[:-4]))
                        if USE_MACD:
                            macd_advice = get_macd_advice(
                                chart_data=get_ticks(pair))  # проверяем, можно ли создать sell
                            if macd_advice['trand'] == 'BEAR' or (
                                    macd_advice['trand'] == 'BULL' and macd_advice['growing']):
                                print('Продавать нельзя, т.к. ситуация на рынке неподходящая: Трэнд ' + str(
                                    macd_advice['trand']) + '; Рост ' + str(macd_advice['growing']))
                                # log(pair, 'Для ордера %s не создаем ордер на продажу, т.к. ситуация на рынке неподходящая' % order['oreder_id'] )
                            else:
                                print('Выставляем ордер на продажу, т.к ситуация подходящая: ' + str(
                                    macd_advice['trand']) + ' ' + str(macd_advice['growing']))
                                log(pair, "Для выполненного ордера на покупку выставляем ордер на продажу")
                                create_sell(pair=pair)
                        else:  # создаем sell если тенденция рынка позволяет
                            log(pair, "Для выполненного ордера на покупку выставляем ордер на продажу")
                            create_sell(pair=pair)
                    else:
                        if float(balances[pair[-3:]]) >= CAN_SPEND:
                            # log(pair, "Неисполненных ордеров нет, пора ли создать новый?")
                            # Проверяем MACD, если рынок в нужном состоянии, выставляем ордер на покупку
                            if USE_MACD:
                                macd_advice = get_macd_advice(chart_data=get_ticks(pair))
                                if macd_advice['trand'] == 'BEAR' and macd_advice['growing']:
                                    log(pair, "Создаем ордер на покупку")
                                    create_buy(pair=pair)
                                else:
                                    log(pair, "Условия рынка не подходят для торговли", macd_advice)
                            else:
                                log(pair, "Создаем ордер на покупку")
                                create_buy(pair=pair)
                        else:
                            order = str(
                                ' В ордере :' + str(float(reserved[pair[:-4]])) + '. ' + str(pair[:-4])) if float(
                                reserved[pair[:-4]]) > 0.0 else ''
                            raise ScriptQuitCondition('Не хватает денег для торговли: баланс ' + str(
                                round(float(balances[pair[-3:]]))) + ' ' + str(pair[-3:]) + order)
            except ScriptError as e:
                print(e)
            except ScriptQuitCondition as e:
                print(e)
            except Exception as e:
                print("!!!!", e)
        time.sleep(1)
    except Exception as e:
        print(e)