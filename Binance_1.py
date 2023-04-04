import time
import requests
from binance import Client
import uuid
import keys
from mongo_db_spot_trading import *

class Binance():

    def __init__(self, api_key, api_secret) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(api_key, api_secret)
        pos_mode = self.client.futures_get_position_mode()
        if not pos_mode["dualSidePosition"]:
            self.client.futures_change_position_mode(**{
                "dualSidePosition": True
            })

    def generate_client_order_id(self, user_id, leverage, isol_cross='CROS'):
        order_id = str(uuid.uuid4())
        user_id_str = str(user_id)
        user_id_str = "0" * (6 - len(user_id_str)) + user_id_str
        user_lev_str = str(leverage)
        user_lev_str = "0" * (6 - len(user_lev_str)) + user_lev_str
        order_id = user_id_str + user_lev_str + order_id[12:]
        if isol_cross == "ISOLATED":
            order_id = order_id[:13] + \
                "0" + order_id[14:]
        else:
            order_id = order_id[:13] + \
                "1" + order_id[14:]
        return order_id

    def get_user_id_from_client_order_id(self, client_order_id):
        return int(client_order_id[:6])

    def get_user_lev_from_client_order_id(self, client_order_id):
        return int(client_order_id[6:12])
    
    def get_user_position_type_from_client_order_id(self, client_order_id):
        if client_order_id[13] == '0':
            return "isol"
        else:
            return 'cros'

    def open_futures_position(self, SYMBOL, SIDE, QTY, TYPE, id, leverage, isol_cross, PRICE=0):
        self.client.futures_change_leverage(symbol=SYMBOL, leverage=1)
        if SIDE == "BUY":
            positionS = "LONG"
        else:
            positionS = "SHORT"

        if TYPE == "MARKET":
            response = self.client.futures_create_order(symbol=SYMBOL,
                                                        side=SIDE,
                                                        positionSide=positionS,
                                                        type="MARKET",
                                                        quantity=QTY,
                                                        newClientOrderId=self.generate_client_order_id(
                                                            id, leverage, isol_cross)
                                                        )
        else:
            response = self.client.futures_create_order(symbol=SYMBOL,
                                                        Side=SIDE,
                                                        positionSide=positionS,
                                                        type=TYPE,
                                                        quantity=QTY,
                                                        price=PRICE,
                                                        newClientOrderId=self.generate_client_order_id(
                                                            id, leverage, isol_cross),
                                                        timeInForce='GTC'
                                                        )
        return response

    def open_futures_takeprofit_position(self, SYMBOL, SIDE, QTY, PRICE, id, leverage, isol_cross):
        if SIDE == "BUY":
            side_for_order = "SELL"
            positionSide = "LONG"
        else:
            side_for_order = "BUY"
            positionSide = "SHORT"
        response = self.client.futures_create_order(symbol=SYMBOL,
                                                    side=side_for_order,
                                                    positionSide=positionSide,
                                                    type='TAKE_PROFIT_MARKET',
                                                    timeInForce='GTC',
                                                    quantity=QTY,
                                                    stopPrice=PRICE,
                                                    newClientOrderId=self.generate_client_order_id(
                                                        id, leverage, isol_cross),
                                                    workingType='MARK_PRICE'
                                                    )
        return response

    def open_futures_stoploss_position(self, SYMBOL, SIDE, QTY, PRICE, id, leverage, isol_cross):
        if SIDE == "BUY":
            side_for_order = "SELL"
            positionSide = "LONG"
        else:
            side_for_order = "BUY"
            positionSide = "SHORT"
        response = self.client.futures_create_order(symbol=SYMBOL,
                                                    side=side_for_order,
                                                    positionSide=positionSide,
                                                    type='STOP_MARKET',
                                                    timeInForce='GTC',
                                                    quantity=QTY,
                                                    stopPrice=PRICE,
                                                    newClientOrderId=self.generate_client_order_id(
                                                        id, leverage, isol_cross),
                                                    workingType='MARK_PRICE'
                                                    )
        return response

    def cancel_open_futures_order(self, SYMBOL, clientOrderId):
        self.client.futures_cancel_order(symbol=SYMBOL,
                                         origClientOrderId=clientOrderId)

    def close_part_of_open_position_market(self, SYMBOL, SIDE, QTY, id, leverage):
        if SIDE == "BUY":
            side_for_order = "SELL"
            positionSide = "LONG"
        else:
            side_for_order = "BUY"
            positionSide = "SHORT"

        response = self.client.futures_create_order(symbol=SYMBOL,
                                                    side=side_for_order,
                                                    positionSide=positionSide,
                                                    type="MARKET",
                                                    newClientOrderId=self.generate_client_order_id(
                                                        id, leverage),
                                                    quantity=QTY
                                                    )
        return response

    def get_futures_balance(self):
        return self.client.futures_account_balance()[6]['balance']

    def futures_convert_to_1x(self, leverage, margin):
        return margin * leverage


    def futures_calculate_profit_percentage(self, entry_price, symbol_pair, side, leverage):
        key = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_pair}"
        data = requests.get(key)
        data = data.json()
        cur_price = float(data['price'])
        res = (cur_price / (entry_price / 100))
        if side == "SELL":
            return (100 - res) * leverage
        return (res - 100) * leverage

    def futures_calculate_pnl(self, margin, percents):
        return margin * (percents * 0.01)

    def open_spot_position(self, SYMBOL, SIDE, QTY, TYPE, id, PRICE=0):
        if TYPE == "MARKET":
            balance = get_balance(id)
            

            response = self.client.create_order(
                symbol=SYMBOL,
                side=SIDE,
                type=TYPE,
                quantity=QTY
            )
            money_from_position = QTY * float(response["fills"][0]['price'])
            try:
                pair_qnt_balance = get_different_coins_balances(id)[SYMBOL]
            except KeyError:
                pair_qnt_balance = 0
            if SIDE == "BUY":
                pair_qnt_balance += QTY
                balance -= money_from_position
            else:
                pair_qnt_balance -= QTY
                balance += money_from_position
            change_balance(id, balance)
            change_different_coins_balance(id, SYMBOL, pair_qnt_balance)
            
            
        else:
            response = self.client.create_order(
                symbol=SYMBOL,
                side=SIDE,
                type=TYPE,
                quantity=QTY,
                timeInForce='GTC',
                price=PRICE
            )
        return response

    def cancel_open_spot_order(self, SYMBOL, id, clientOrderId):
        self.client.cancel_order(symbol=SYMBOL, orderId=id,
                                 origClientOrderId=clientOrderId)

    def get_spot_balance(self, asset):
        return self.client.get_asset_balance(asset=asset)["free"]

    def transfer_futures_to_spot(self, amount, asset):
        self.client.futures_account_transfer(
            asset=asset, amount=float(amount), type="2", timeInForce='GTC')

    def transfer_spot_to_futures(self, amount, asset):
        self.client.futures_account_transfer(
            asset=asset, amount=float(amount), type="1", timeInForce='GTC')

    def withdraw(self, asset, amount, address, id, сеть):
        self.client.withdraw(
            coin=asset,
            address=address,
            amount=amount
        )
        add_pending_trans(id, сеть, asset, address, amount)


bin = Binance(keys.key, keys.secret)
# print(bin.open_futures_position("OPUSDT", "BUY", 2.5, "MARKET", 1, 20))
# time.sleep(1)
# print(bin.open_futures_position("OPUSDT", "BUY", 2.5, "MARKET", 1, 20))
# time.sleep(1)
# print(bin.close_part_of_open_position_market("OPUSDT", "BUY", 2.5, 1, 20))
# time.sleep(1)
# print(bin.open_futures_position("OPUSDT", "SELL", 2.5, "MARKET", 1, 20))
# time.sleep(1)
# print(bin.open_futures_position("OPUSDT", "SELL", 2.5, "MARKET", 1, 20))
# time.sleep(1)
# print(bin.close_part_of_open_position_market("OPUSDT", "SELL", 2.5, 1, 20))
# time.sleep(1)

# print(bin.open_futures_position("OPUSDT", "BUY", 25, "MARKET", 1, 20, 'CROS'))
# print(bin.cancel_open_futures_order(
#     "OPUSDT", "00000100002041488b-a21a-e2f0f8ff5d5a"))
# print(bin.cancel_open_futures_order(
#     "OPUSDT", "000001000020d145cc-ab47-e1d67b193118"))

# print(bin.open_futures_takeprofit_position("OPUSDT", "BUY", 25, 1.85, 1, 20))

print(bin.open_futures_stoploss_position("OPUSDT", "BUY", 25, 2, 1, 20, "CROS"))

# print(bin.open_spot_position("SOLUSDT", "BUY", 1, "MARKET", 1))

