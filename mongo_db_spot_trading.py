from pymongo import *
cluster = MongoClient(
    "mongodb+srv://Ucript:9MFTeFa7Yd!Gy-5@cluster0.py3riqk.mongodb.net/?retryWrites=true&w=majority")
db = cluster["Ucript"]
spot_table = db["Spot_Trading"]


def add_new_client(id, email, spot_account_number, balance=0, different_coins_balance={}, spot_orders=[]):
    spot_table.insert_one({
        "_id": id,
        "email": email,
        "spot_account_number": spot_account_number,
        "balance": balance,
        "different_coins_balance": different_coins_balance,
        "spot_orders": spot_orders,
        "pending_trans": {}
    })


def get_spot_account_number(id):
    return spot_table.find_one(id)["spot_account_number"]


def get_pending_transactions(id):
    return spot_table.find_one(id)["pending_trans"]


def get_balance(id):
    return spot_table.find_one(id)["balance"]


def get_email(id):
    return spot_table.find_one(id)["email"]


def get_different_coins_balances(id):
    return spot_table.find_one(id)["different_coins_balance"]


def get_spot_orders(id):
    return spot_table.find_one(id)["spot_orders"]


def add_pending_trans(id, сеть, asset, address, amount):
    pending_trans = get_pending_transactions(id)
    pending_trans[сеть] = {asset: {"address": address,
                                   "amount": amount}}
    spot_table.update_one({'_id': id}, {"$set": {
        "pending_trans": pending_trans}})


def change_email(id, new_email):
    spot_table.update_one({'_id': id}, {"$set": {
        "email": new_email}})


def change_balance(id, balance):
    spot_table.update_one({'_id': id}, {"$set": {
        "balance": balance}})


def change_different_coins_balance(id, coin, balance):
    bal = get_different_coins_balances(id)
    bal[coin] = balance
    spot_table.update_one({'_id': id}, {"$set": {
        "different_coins_balance": bal}})


def add_spot_order(id, spot_order):
    orders = get_spot_orders(id)
    orders.append(spot_order)
    spot_table.update_one({'_id': id}, {"$set": {
        "spot_orders": orders}})


def remove_pending_transactions(id):
    spot_table.update_one({'_id': id}, {"$set": {
        "pending_trans": {}}})


def remove_spot_order(id, spot_order):
    orders = get_spot_orders(id)
    orders.remove(spot_order)
    spot_table.update_one({'_id': id}, {"$set": {
        "spot_orders": orders}})


def delete_user(id):
    spot_table.delete_one({"_id": id})

# delete_user(1)
# add_new_client(1, "palka@gmail.com", '123')
# change_balance(1, 100)


# print(get_different_coins_balances(1))
# print(get_balance(1))
add_pending_trans(1, 'bitcoin', "BTC", '14881337', 1)
print(get_pending_transactions(1))
