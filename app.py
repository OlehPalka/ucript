import balance_listener
import requests
from flask import *
import json
import uc_db_clients_sql
import mongo_db_futures_trading
import mongo_db_spot_trading
import Binance_1
import keys
bin = Binance_1.Binance(keys.key, keys.secret)

app = Flask(__name__)


@app.route("/createUser", methods=["POST"])
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
def user_profile():
    try:
        data = request.json()
    except:
        data = request.json
    id = data['userId']
    avatar = data['avatar']
    name = data['name']

    uc_db_clients_sql.change_image(id, avatar)
    uc_db_clients_sql.change_name(id, name)

    result = {"avatar": avatar,
              "name": name}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/getAllBalances", methods=["POST"])
def get_all_balances():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
    binance_spot_bal = float(bin.get_spot_balance("USDT"))
    spot_bal = float(mongo_db_spot_trading.get_balance(id))
    if spot_bal < binance_spot_bal:
        spot_bal = binance_spot_bal
        mongo_db_spot_trading.change_balance(id, spot_bal)
    print(spot_bal)
    all_coins_bal = mongo_db_spot_trading.get_different_coins_balances(id)
    print(all_coins_bal)
    fut_balance = mongo_db_futures_trading.get_balance(id)
    print(fut_balance)
    crypto_api_bal = balance_listener.get_balances()
    print(crypto_api_bal)
    result = {"spotUsdtBalance": spot_bal, "AllCoinsSpotBalance": all_coins_bal, "futuresBalance": fut_balance,
              "crypto_api_bal": crypto_api_bal}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/wallet", methods=["POST"])
def wallet():
    try:
        data = request.json()
    except:
        data = request.json
    print(data)
    id = int(data['UserId'])

    all_coins_bal = mongo_db_spot_trading.get_different_coins_balances(id)
    all_coins = []
    for i in all_coins_bal:
        all_coins.append({"symbol": i,
                          "balance": all_coins_bal[i]})

    result = {"infoOfAllCoins": all_coins}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/spot", methods=["POST"])
def spot():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']

    all_coins_bal = mongo_db_spot_trading.get_different_coins_balances(id)
    all_coins = []
    for i in all_coins_bal:
        all_coins.append({"symbol": i,
                          "balance": all_coins_bal[i]})

    result = {"userId": id, "infoOfAllCoins": all_coins}

    return json.dumps(result), 200, {"ContentType": "application/json"}


@app.route("/openSpotOrder", methods=["POST"])
def openSpotOrder():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
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
def futures():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']

    positions = mongo_db_futures_trading.get_positions(id)
    open_orders = mongo_db_futures_trading.get_limit_positions(id)
    balance = mongo_db_futures_trading.get_balance(id)

    return json.dumps({"balance": balance, "positions": positions, "openOrders": open_orders}), 200, {"ContentType": "application/json"}


@app.route("/editFuturesPosition", methods=["POST"])
def editFuturesPosition():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
    pair = data['pair']
    openFuturesTakeProffit = data['openFuturesTakeProffit']
    openFuturesStopLoss = data['openFuturesStopLoss']
    side = data['side']  # BUY SELL
    QNT = data['qnt']
    leverage = data['leverage']
    isol_cros = data['cros']  # ISOLATED CROS
    stop = "_"
    take = "_"
    if openFuturesStopLoss != 'undefined':
        stop = bin.open_futures_stoploss_position(pair, side, QNT, float(
            openFuturesStopLoss), id, leverage, isol_cros)["clientOrderId"]
    if openFuturesTakeProffit != 'undefined':
        take = bin.open_futures_takeprofit_position(pair, side, QNT, float(
            openFuturesTakeProffit), id, leverage, isol_cros)["clientOrderId"]

    return json.dumps({"take_id": take, "stop_id": stop}), 200, {"ContentType": "application/json"}


@app.route("/closeFuturesPosition", methods=["POST"])
def closeFuturesPosition():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
    pair = data['pair']
    side = data['side']  # BUY SELL
    qnt = (data['sum'] / data['price']) * data['leverage']
    leverage = data['leverage']

    bin.close_part_of_open_position_market(pair, side, qnt, id, leverage)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/createFuturesPosition", methods=["POST"])
def createFuturesPosition():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
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
def cancelOrder():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
    pair = data['pair']
    order_id = data['orderId']
    bin.cancel_open_futures_order(pair, order_id)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
    pair = data['pair']
    blockchain = ["blockchain"]
    address = ["address"]
    sum = ['sum']

    bin.withdraw(pair, sum, address, id, blockchain)
    if pair == "USDT":
        cur_bal = mongo_db_spot_trading.get_balance(id)
        cur_bal -= sum
        mongo_db_spot_trading.change_balance(id, cur_bal)
    else:
        pair = pair + "USDT"
        cur_pair_balance = mongo_db_spot_trading.get_different_coins_balances(id)[pair]
        cur_pair_balance -= sum
        mongo_db_spot_trading.change_different_coins_balance(id, pair, cur_pair_balance)

    return json.dumps({}), 200, {"ContentType": "application/json"}


@app.route("/convert", methods=["POST"])
def convert():
    try:
        data = request.json()
    except:
        data = request.json

    id = data['UserId']
    send_point = data['send_point']
    destination_point = data['destination_point']
    blockchain = ["blockchain"]
    address = ["address"]
    sum = ['sum']
    if send_point == 'wallet' and destination_point == "spot":
        balance_listener.deposit(blockchain, "USDT", sum)
    elif send_point == 'wallet' and destination_point == "futures":
        balance_listener.deposit(blockchain, "USDT", sum)
        mongo_db_futures_trading.change_balance(id, sum)
    elif send_point == 'spot' and destination_point == "futures":
        spot_bal = mongo_db_spot_trading.get_balance(id)
        futures_bal = mongo_db_futures_trading.get_balance(id)
        bin.transfer_spot_to_futures(sum, "USDT")
        spot_bal -= sum
        futures_bal += sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        mongo_db_futures_trading.change_balance(id, futures_bal)
    elif send_point == 'futures' and destination_point == "spot":
        spot_bal = mongo_db_spot_trading.get_balance(id)
        futures_bal = mongo_db_futures_trading.get_balance(id)
        bin.transfer_futures_to_spot(sum, "USDT")
        spot_bal += sum
        
        mongo_db_spot_trading.change_balance(id, spot_bal)
        mongo_db_futures_trading.change_balance(id, futures_bal)
    elif send_point == 'futures' and destination_point == "wallet":
        futures_bal = mongo_db_futures_trading.get_balance(id)
        futures_bal -= sum
        mongo_db_futures_trading.change_balance(id, futures_bal)
        bin.transfer_futures_to_spot(sum, "USDT")
        bin.withdraw("USDT", sum, address)
    elif send_point == 'spot' and destination_point == "wallet":
        spot_bal = mongo_db_spot_trading.get_balance(id)
        spot_bal -= sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        bin.withdraw("USDT", sum, address)
    elif send_point == 'spot' and destination_point == "invest":
        spot_bal = mongo_db_spot_trading.get_balance(id)
        spot_bal -= sum
        mongo_db_spot_trading.change_balance(id, spot_bal)
        bin.withdraw("USDT", sum, address)
    elif send_point == 'wallet' and destination_point == "invest":
        balance_listener.withdraw(blockchain, address, "USDT", sum)
    elif send_point == 'futures' and destination_point == "invest":
        futures_bal = mongo_db_futures_trading.get_balance(id)
        futures_bal -= sum
        mongo_db_futures_trading.change_balance(id, futures_bal)
        bin.transfer_futures_to_spot(sum, "USDT")
        bin.withdraw("USDT", sum, address)
    

    return json.dumps({}), 200, {"ContentType": "application/json"}


