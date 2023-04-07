import balance_listener
import requests
from flask import *
from flask_cors import cross_origin
import json
import uc_db_clients_sql
import mongo_db_futures_trading
import mongo_db_spot_trading
import Binance_1
import keys
import psycopg2
from balance_listener import *
from binance import Client
bin = Binance_1.Binance(keys.key, keys.secret)

app = Flask(__name__)


@app.route("/createUser", methods=["POST"])
@cross_origin()
def create():
    try:
        data = request.json()
    except:
        data = request.json

    uc_db_clients_sql.add_client(data['email'], data["password"], data['pin'])
    user_data = uc_db_clients_sql.find_user_by_email(data['email'])
    print(user_data)
    mongo_db_spot_trading.add_new_client(user_data[0], user_data[1], "_")
    mongo_db_futures_trading.add_new_client(user_data[0], user_data[1])

    result = {"relevantEmailAndPassword": True, "userId": user_data[0]}
    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/getUser", methods=["POST"])
@cross_origin()
def get_user():
    try:
        data = request.json()
    except:
        data = request.json
    result = {}
    try:
        user_data = uc_db_clients_sql.find_user_by_email(data['email'])
        if user_data[1] == data['email'] and user_data[2] == data['password']:
            result["relevantEmailAndPassword"] = True
            result['user_id'] = user_data[0]
        else:
            result["relevantEmailAndPassword"] = False

        if user_data[3] == data['pin']:
            result["relevantPin"] = True
        else:
            result["relevantPin"] = False

    except:
        result = {"relevantEmailAndPassword": False,
                  "relevantPin": False}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/userProfile", methods=["POST"])
@cross_origin()
def user_profile():
    try:
        data = request.json()
    except:
        data = request.json
    id = int(data['userId'])

    try:
        name = data['name']
        uc_db_clients_sql.change_name(id, name)
    except Exception:
        name = uc_db_clients_sql.find_user_by_id(id)[-2]
        pass

    try:
        avatar = data['avatar']
        uc_db_clients_sql.change_image(id, avatar)
    except Exception:
        avatar = uc_db_clients_sql.find_user_by_id(id)[-1]
        pass

    result = {"avatar": avatar,
              "name": name}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/getAllBalances", methods=["POST"])
@cross_origin()
def get_all_balances():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    spot_usdt_bal = float(mongo_db_spot_trading.get_balance(id))
    all_coins_bal = mongo_db_spot_trading.get_different_coins_balances(id)

    binance_balances = Client(keys.key, keys.secret).get_account()['balances']
    for coin_info in binance_balances:
        coin_name = coin_info['asset']
        if coin_name == "USDT":
            amount = float(coin_info['free'])
            spot_usdt_bal = float(coin_info['free'])
            all_coins_bal[coin_name] = amount
        else:
            amount = float(coin_info['free'])
            if amount > 0:
                all_coins_bal[coin_name] = amount

    mongo_db_spot_trading.change_all_different_coins_balance(id, all_coins_bal)
    mongo_db_spot_trading.change_balance(id, spot_usdt_bal)

    for coin_info in binance_balances:
        coin_name = coin_info['asset']
        amount = float(coin_info['free'])
        if amount > 0:
            try:
                pair = coin_name + "USDT"
                key = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
                data = requests.get(key)
                data = data.json()
                cur_price = float(data['price'])
                spot_usdt_bal += cur_price * amount
            except Exception:
                continue

    fut_balance = mongo_db_futures_trading.get_balance(id)
    crypto_api_bal = balance_listener.get_balances()

    result = {"spotUsdtBalance": spot_usdt_bal, "AllCoinsSpotBalance": all_coins_bal, "futuresBalance": fut_balance,
              "crypto_api_bal": crypto_api_bal}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/wallet", methods=["POST"])
@cross_origin()
def wallet():
    try:
        data = request.json()
    except:
        data = request.json
    print(data)
    id = int(data['UserId'])

    crypt_api = balance_listener.get_balances()
    usdt_balance = 0
    for i in crypt_api:
        if "USDT" in crypt_api[i]:
            usdt = float(crypt_api[i]['USDT'])
            usdt_balance += usdt

    # for i in crypt_api:
    #     for coin in crypt_api[i]:
    #         pair = coin + "USDT"
    #         amount = float(crypt_api[i][coin])
    #         key = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    #         data = requests.get(key)
    #         data = data.json()
    #         cur_price = float(data['price'])
    #         usdt_balance += cur_price * amount

    # crypt_api['tron']['OP'] = 20
    # crypt_api['tron']['BTC'] = 1

    result = {"balance": usdt_balance, "infoOfAllCoins": crypt_api}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/spot", methods=["POST"])
@cross_origin()
def spot():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])

    all_coins_bal = mongo_db_spot_trading.get_different_coins_balances(id)
    spot_usdt_bal = float(mongo_db_spot_trading.get_balance(id))

    binance_balances = Client(keys.key, keys.secret).get_account()['balances']
    for coin_info in binance_balances:
        coin_name = coin_info['asset']
        if coin_name == "USDT":
            amount = float(coin_info['free'])
            spot_usdt_bal = float(coin_info['free'])
            all_coins_bal[coin_name] = amount
        else:
            amount = float(coin_info['free'])
            if amount > 0:
                all_coins_bal[coin_name] = amount

    mongo_db_spot_trading.change_all_different_coins_balance(id, all_coins_bal)
    mongo_db_spot_trading.change_balance(id, spot_usdt_bal)

    for coin_info in binance_balances:
        coin_name = coin_info['asset']
        amount = float(coin_info['free'])
        try:
            if amount > 0:
                pair = coin_name + "USDT"
                key = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
                data = requests.get(key)
                data = data.json()
                cur_price = float(data['price'])
                spot_usdt_bal += cur_price * amount
        except Exception:
            continue

    all_coins = []
    for i in all_coins_bal:
        all_coins.append({"symbol": i,
                          "balance": all_coins_bal[i]})

    result = {"UserId": id, "infoOfAllCoins": all_coins,
              'balance': spot_usdt_bal}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/openSpotOrder", methods=["POST"])
@cross_origin()
def openSpotOrder():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    pair = data['pair']
    side = data["longOrShort"]
    money = data['replenishment']

    key = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    data = requests.get(key)
    data = data.json()
    cur_price = float(data['price'])
    qnt = money/cur_price

    bin.open_spot_position(pair, side, qnt, 'MARKET', id)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/futures", methods=["POST"])
@cross_origin()
def futures():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])

    positions = mongo_db_futures_trading.get_positions(id)
    open_orders = mongo_db_futures_trading.get_limit_positions(id)
    balance = mongo_db_futures_trading.get_balance(id)

    return json.dumps({"balance": balance, "positions": positions, "openOrders": open_orders}), 200, {"ContentType": "application/json"}


@app.route("/editFuturesPosition", methods=["POST"])
@cross_origin()
def editFuturesPosition():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    pair = data['pair']
    openFuturesTakeProffit = data['openFuturesTakeProffit']
    openFuturesStopLoss = data['openFuturesStopLoss']
    side = data['side']  # BUY SELL
    sum_stop = data['sum_stop']
    sum_take = data['sum_take']
    qnt_stop = (sum_stop / openFuturesStopLoss) * data['leverage']
    qnt_take = (sum_take / openFuturesTakeProffit) * data['leverage']
    leverage = data['leverage']
    isol_cros = data['cros']  # ISOLATED CROS
    stop = "_"
    take = "_"
    if openFuturesStopLoss != 'undefined':
        stop = bin.open_futures_stoploss_position(pair, side, qnt_stop, float(
            openFuturesStopLoss), id, leverage, isol_cros)["clientOrderId"]
    if openFuturesTakeProffit != 'undefined':
        take = bin.open_futures_takeprofit_position(pair, side, qnt_take, float(
            openFuturesTakeProffit), id, leverage, isol_cros)["clientOrderId"]

    return json.dumps({"take_id": take, "stop_id": stop}), 200, {"ContentType": "application/json"}


@app.route("/closeFuturesPosition", methods=["POST"])
@cross_origin()
def closeFuturesPosition():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    pair = data['pair']
    side = data['side']  # BUY SELL
    qnt = (data['sum'] / data['price']) * data['leverage']
    leverage = data['leverage']

    bin.close_part_of_open_position_market(pair, side, qnt, id, leverage)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/createFuturesPosition", methods=["POST"])
@cross_origin()
def createFuturesPosition():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    pair = data['pair']
    side = data['longOrShort']  # BUY SELL
    qnt = (data['replenishment'] / data['price']) * data['leverage']
    leverage = data['leverage']
    isol_cros = data['crossOrIsolate']
    limit_market = data["limitOrMarket"]
    price = data['price']
    pose = bin.open_futures_position(
        pair, side, qnt, limit_market, id, leverage, isol_cros, price)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/cancelOrder", methods=["POST"])
@cross_origin()
def cancelOrder():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    pair = data['pair']
    order_id = data['orderId']
    bin.cancel_open_futures_order(pair, order_id)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/send", methods=["POST"])
@cross_origin()
def send():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])
    coin = data['coin']
    blockchain = ["blockchain"]
    address = ["address"]
    sum = ['sum']

    withdraw(blockchain, address, coin, sum)

    # bin.withdraw(pair, sum, address, id, blockchain)
    # if pair == "USDT":
    #     cur_bal = mongo_db_spot_trading.get_balance(id)
    #     cur_bal -= sum
    #     mongo_db_spot_trading.change_balance(id, cur_bal)
    # else:
    #     pair = pair + "USDT"
    #     cur_pair_balance = mongo_db_spot_trading.get_different_coins_balances(id)[
    #         pair]
    #     cur_pair_balance -= sum
    #     mongo_db_spot_trading.change_different_coins_balance(
    #         id, pair, cur_pair_balance)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/invest", methods=["POST"])
@cross_origin()
def invest():
    try:
        data = request.json()
    except:
        data = request.json

    bin_2 = Client(
        'plxLnpLOzxAqEBPlcptaZToVeUFDhiT2auzdznOBkmqPM7cu5oqiLIQoPuL6dcRr', '2azbW1U3E4S0aQhA9f6IP4BdhCo5TeqEBe8VtWBYfosmMMcZSzJl3lHqgXyKiwGF')

    spot_bal = bin_2.get_asset_balance(asset="USDT")["free"]

    futures_bal = bin_2.futures_account_balance()[8]['balance']
    return json.dumps({"spot_invest_bal_usdt": spot_bal, "futures_invest_bal_usdt": futures_bal}), 200, {"ContentType": "application/json"}


@app.route("/convert", methods=["POST"])
@cross_origin()
def convert():
    "поменять ЮСДТ на любую монетку"
    try:
        data = request.json()
    except:
        data = request.json

    bin_2 = Client(
        'plxLnpLOzxAqEBPlcptaZToVeUFDhiT2auzdznOBkmqPM7cu5oqiLIQoPuL6dcRr', '2azbW1U3E4S0aQhA9f6IP4BdhCo5TeqEBe8VtWBYfosmMMcZSzJl3lHqgXyKiwGF')

    id = int(data['UserId'])
    send_point = data['send_point']
    destination_point = data['destination_point']
    blockchain = data["blockchain"]
    sum = data["sum"]

    try:
        address = ["address"]
    except Exception:
        pass
    if send_point == 'wallet' and destination_point == "spot":
        balance_listener.deposit(blockchain, "USDT", sum)
    elif send_point == 'wallet' and destination_point == "futures":
        balance_listener.deposit(blockchain, "USDT", sum)
        mongo_db_futures_trading.change_balance(id, sum)
    elif send_point == 'spot' and destination_point == "futures":
        spot_bal = float(mongo_db_spot_trading.get_balance(id))
        futures_bal = float(mongo_db_futures_trading.get_balance(id))
        bin.transfer_spot_to_futures(sum, "USDT")
        spot_bal -= sum
        futures_bal += sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        mongo_db_futures_trading.change_balance(id, futures_bal)
    elif send_point == 'futures' and destination_point == "spot":
        spot_bal = float(mongo_db_spot_trading.get_balance(id))
        futures_bal = float(mongo_db_futures_trading.get_balance(id))
        bin.transfer_futures_to_spot(sum, "USDT")
        spot_bal += sum

        mongo_db_spot_trading.change_balance(id, spot_bal)
        mongo_db_futures_trading.change_balance(id, futures_bal)
    elif send_point == 'futures' and destination_point == "wallet":
        futures_bal = float(mongo_db_futures_trading.get_balance(id))
        futures_bal -= sum
        mongo_db_futures_trading.change_balance(id, futures_bal)
        bin.transfer_futures_to_spot(sum, "USDT")
        bin.withdraw("USDT", sum, address)
    elif send_point == 'spot' and destination_point == "wallet":
        spot_bal = float(mongo_db_spot_trading.get_balance(id))
        spot_bal -= sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        bin.withdraw("USDT", sum, address)
    elif send_point == 'spot' and destination_point == "invest":
        spot_bal = float(mongo_db_spot_trading.get_balance(id))
        spot_bal -= sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        bin.withdraw("USDT", sum, address)
    elif send_point == 'wallet' and destination_point == "invest":
        balance_listener.withdraw(blockchain, address, "USDT", sum)
    elif send_point == 'futures' and destination_point == "invest":
        futures_bal = float(mongo_db_futures_trading.get_balance(id))
        futures_bal -= sum
        mongo_db_futures_trading.change_balance(id, futures_bal)
        bin.transfer_futures_to_spot(sum, "USDT")
        bin.withdraw("USDT", sum, address)
    elif send_point == 'invest' and destination_point == "spot":
        spot_bal = float(mongo_db_spot_trading.get_balance(id))
        spot_bal += sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        bin_2.withdraw("USDT", sum, address)
    elif send_point == 'invest' and destination_point == "wallet":
        bin_2.withdraw("USDT", sum, address)
    elif send_point == 'invest' and destination_point == "futures":
        futures_bal = float(mongo_db_futures_trading.get_balance(id))
        futures_bal += sum
        mongo_db_futures_trading.change_balance(id, futures_bal)
        bin.transfer_spot_to_futures(sum, "USDT")
        bin_2.withdraw("USDT", sum, address)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/close_all_futures_positons",  methods=["POST"])
@cross_origin()
def close_all_futures_positons():
    try:
        data = request.json()
    except:
        data = request.json

    id = int(data['UserId'])

    positions = mongo_db_futures_trading.get_positions(id)

    for pose in positions:
        coin_poses = positions[pose]
        if coin_poses["BUY"] != []:
            pair = pose
            side = "BUY"
            qnt = coin_poses["BUY"][1]
            leverage = coin_poses["BUY"][0]
            bin.close_part_of_open_position_market(
                pair, side, qnt, id, leverage)
        elif coin_poses["SELL"] != []:
            pair = pose
            side = "SELL"
            qnt = coin_poses["SELL"][1]
            leverage = coin_poses["SELL"][0]
            bin.close_part_of_open_position_market(
                pair, side, qnt, id, leverage)

    mongo_db_futures_trading.terminate_all_limit_position(id)

    positions = mongo_db_futures_trading.get_positions(id)
    open_orders = mongo_db_futures_trading.get_limit_positions(id)
    balance = mongo_db_futures_trading.get_balance(id)

    return json.dumps({'positions': positions, "open_orders": open_orders, "balance": balance}), 200, {"ContentType": "application/json"}
