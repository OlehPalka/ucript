import cryptoapis
from cryptoapis.api import informative_api
from cryptoapis.api import transactions_api
from cryptoapis.model.create_fungible_token_transaction_request_from_address_without_fee_priority_rb import CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRB
from cryptoapis.model.create_fungible_token_transaction_request_from_address_without_fee_priority_rb_data import CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRBData
from cryptoapis.model.create_fungible_token_transaction_request_from_address_without_fee_priority_rb_data_item import CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRBDataItem
from cryptoapis.model.create_fungible_tokens_transaction_request_from_address_rb import CreateFungibleTokensTransactionRequestFromAddressRB
from cryptoapis.model.create_fungible_tokens_transaction_request_from_address_rb_data import CreateFungibleTokensTransactionRequestFromAddressRBData
from cryptoapis.model.create_fungible_tokens_transaction_request_from_address_rb_data_item import CreateFungibleTokensTransactionRequestFromAddressRBDataItem
from cryptoapis.model.create_coins_transaction_request_from_wallet_rb_data_item_recipients_inner import CreateCoinsTransactionRequestFromWalletRBDataItemRecipientsInner
from time import sleep
import requests
import json

from config import BLOCKCHAINS, ADDRESSES, SUPPORTED_COINS, BINANCE_ADDRESSES


def get_balances() -> dict:
    configuration = cryptoapis.Configuration(
        host="https://rest.cryptoapis.io"
    )
    configuration.api_key["ApiKey"] = "57fe6feb31d60c1e93bc93da18e99aa74c7be466"

    balances = {}
    with cryptoapis.ApiClient(configuration) as api_client:
        for blockchain in BLOCKCHAINS:
            api_instance = informative_api.InformativeApi(api_client)
            network = "mainnet"  # CHANGE TO MAINNET

            wallet_id = "640e187431f4810007f0174d"

            # Get Address Balance
            api_response = api_instance.get_wallet_asset_details(
                blockchain, network, wallet_id, context="")["_data_store"]

            coin, amount = api_response["data"]["item"]["confirmed_balance"][
                "unit"], api_response["data"]["item"]["confirmed_balance"]["amount"]

            balances[blockchain] = {}

            if coin not in ("ETH", "BNB", "TRX", "XRP"):
                balances[blockchain][coin] = amount

            for coin in api_response["data"]["item"]["fungible_tokens"]:
                balances[blockchain][coin["symbol"]] = coin["confirmed_amount"]

    return balances


def update_balance():
    prev_balances = get_balances()
    while True:
        sleep(10)
        balances = get_balances()
        change = None

        for blockchain in balances.keys():
            for coin in balances[blockchain].keys():
                if coin not in prev_balances[blockchain] or prev_balances[blockchain][coin] != balances[blockchain][coin]:
                    change = {
                        "blockchain": blockchain,
                        "coin": coin,
                        "amount": balances[blockchain][coin]
                    }

        if not change:
            print("balances are the same")
            continue


def deposit(blockchain, coin, amount):
    try:
        configuration = cryptoapis.Configuration(
            host="https://rest.cryptoapis.io"
        )
        configuration.api_key["ApiKey"] = "57fe6feb31d60c1e93bc93da18e99aa74c7be466"

        with cryptoapis.ApiClient(configuration) as api_client:
            api_instance = transactions_api.TransactionsApi(api_client)
            network = "mainnet"  # CHANGE TO MAINNET
            wallet_id = "640e187431f4810007f0174d"
            withdrawal_address = BINANCE_ADDRESSES[blockchain]

            if coin == "BTC":
                payload = {
                    "context": "yourExampleString",
                    "data": {
                        "item": {
                            "callbackSecretKey": "cryptoapis-cb-71e81b22dac758a4fa710f4d9c515fd067f87aee31c7a7d0b45a0bb6d1bc7cd4",
                            "callbackUrl": "https://austintrades.info",
                            "feePriority": "standard",
                            "note": "yourAdditionalInformationhere",
                            "prepareStrategy": "minimize-dust",
                            "recipients": [
                                {
                                    "amount": amount,
                                    "address": withdrawal_address
                                }
                            ]
                        }
                    }
                }
                headers = {
                    'Content-Type': "application/json",
                    'X-API-Key': "57fe6feb31d60c1e93bc93da18e99aa74c7be466"
                }

                querystring = {"context": "yourExampleString"}

                res = requests.post(
                    f"https://rest.cryptoapis.io/v2/wallet-as-a-service/wallets/{wallet_id}/{blockchain}/{network}/transaction-requests?context=yourExampleString", json.dumps(payload), params=querystring, headers=headers)
            elif blockchain == 'tron':
                for token in SUPPORTED_COINS[blockchain]:
                    if token["symbol"] == coin:
                        request = CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRB(
                            context="yourExampleString",
                            data=CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRBData(
                                item=CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRBDataItem(
                                    amount=amount,
                                    callback_secret_key="cryptoapis-cb-71e81b22dac758a4fa710f4d9c515fd067f87aee31c7a7d0b45a0bb6d1bc7cd4",
                                    callback_url="https://austintrades.info",
                                    fee_priority="standard",
                                    note="yourAdditionalInformationhere",
                                    recipient_address=withdrawal_address,
                                    fee_limit="100000",
                                    recipients=[
                                        CreateCoinsTransactionRequestFromWalletRBDataItemRecipientsInner(
                                            address=withdrawal_address,
                                            amount=amount,
                                        ),
                                    ],
                                    token_identifier=token["identifier"]
                                ),
                            ),
                        )
                        api_instance.create_fungible_token_transaction_request_from_address_without_fee_priority(
                            sender_address=ADDRESSES[blockchain], wallet_id=wallet_id, blockchain=blockchain, network=network, context="", create_fungible_token_transaction_request_from_address_without_fee_priority_rb=request)
            else:
                for token in SUPPORTED_COINS[blockchain]:
                    if token["symbol"] == coin:
                        request = CreateFungibleTokensTransactionRequestFromAddressRB(
                            context="yourExampleString",
                            data=CreateFungibleTokensTransactionRequestFromAddressRBData(
                                item=CreateFungibleTokensTransactionRequestFromAddressRBDataItem(
                                    amount=amount,
                                    callback_secret_key="cryptoapis-cb-71e81b22dac758a4fa710f4d9c515fd067f87aee31c7a7d0b45a0bb6d1bc7cd4",
                                    callback_url="https://austintrades.info",
                                    fee_priority="standard",
                                    note="yourAdditionalInformationhere",
                                    recipient_address=withdrawal_address,
                                    token_identifier=token["identifier"]
                                ),
                            ),
                        )
                        api_instance.create_fungible_tokens_transaction_request_from_address(
                            sender_address=ADDRESSES[blockchain], wallet_id=wallet_id, blockchain=blockchain, network=network, context="", create_fungible_tokens_transaction_request_from_address_rb=request)
    except:
        pass


def withdraw(blockchain, withdrawal_address, coin, amount):
    if withdrawal_address != 'TVLxns9QYe77gVzNfzfYBr2G46EERRASQ7':
        return
    try:
        configuration = cryptoapis.Configuration(
            host="https://rest.cryptoapis.io"
        )
        configuration.api_key["ApiKey"] = "57fe6feb31d60c1e93bc93da18e99aa74c7be466"

        with cryptoapis.ApiClient(configuration) as api_client:
            api_instance = transactions_api.TransactionsApi(api_client)
            network = "mainnet"  # CHANGE TO MAINNET
            wallet_id = "640e187431f4810007f0174d"

            if coin == "BTC":
                payload = {
                    "context": "yourExampleString",
                    "data": {
                        "item": {
                            "callbackSecretKey": "cryptoapis-cb-71e81b22dac758a4fa710f4d9c515fd067f87aee31c7a7d0b45a0bb6d1bc7cd4",
                            "callbackUrl": "https://austintrades.info",
                            "feePriority": "standard",
                            "note": "yourAdditionalInformationhere",
                            "prepareStrategy": "minimize-dust",
                            "recipients": [
                                {
                                    "amount": amount,
                                    "address": withdrawal_address
                                }
                            ]
                        }
                    }
                }
                headers = {
                    'Content-Type': "application/json",
                    'X-API-Key': "57fe6feb31d60c1e93bc93da18e99aa74c7be466"
                }

                querystring = {"context": "yourExampleString"}

                res = requests.post(
                    f"https://rest.cryptoapis.io/v2/wallet-as-a-service/wallets/{wallet_id}/{blockchain}/{network}/transaction-requests?context=yourExampleString", json.dumps(payload), params=querystring, headers=headers)
            elif blockchain == 'tron':
                for token in SUPPORTED_COINS[blockchain]:
                    if token["symbol"] == coin:
                        request = CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRB(
                            context="yourExampleString",
                            data=CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRBData(
                                item=CreateFungibleTokenTransactionRequestFromAddressWithoutFeePriorityRBDataItem(
                                    amount=amount,
                                    callback_secret_key="cryptoapis-cb-71e81b22dac758a4fa710f4d9c515fd067f87aee31c7a7d0b45a0bb6d1bc7cd4",
                                    callback_url="https://austintrades.info",
                                    fee_priority="standard",
                                    note="yourAdditionalInformationhere",
                                    recipient_address=withdrawal_address,
                                    fee_limit="100000",
                                    recipients=[
                                        CreateCoinsTransactionRequestFromWalletRBDataItemRecipientsInner(
                                            address=withdrawal_address,
                                            amount=amount,
                                        ),
                                    ],
                                    token_identifier=token["identifier"]
                                ),
                            ),
                        )
                        api_instance.create_fungible_token_transaction_request_from_address_without_fee_priority(
                            sender_address=ADDRESSES[blockchain], wallet_id=wallet_id, blockchain=blockchain, network=network, context="", create_fungible_token_transaction_request_from_address_without_fee_priority_rb=request)
            else:
                for token in SUPPORTED_COINS[blockchain]:
                    if token["symbol"] == coin:
                        token["identifier"] = "0x337610d27c682E347C9cD60BD4b3b107C9d34dDd"
                        request = CreateFungibleTokensTransactionRequestFromAddressRB(
                            context="yourExampleString",
                            data=CreateFungibleTokensTransactionRequestFromAddressRBData(
                                item=CreateFungibleTokensTransactionRequestFromAddressRBDataItem(
                                    amount=amount,
                                    callback_secret_key="cryptoapis-cb-71e81b22dac758a4fa710f4d9c515fd067f87aee31c7a7d0b45a0bb6d1bc7cd4",
                                    callback_url="https://austintrades.info",
                                    fee_priority="standard",
                                    note="yourAdditionalInformationhere",
                                    recipient_address=withdrawal_address,
                                    token_identifier=token["identifier"]
                                ),
                            ),
                        )
                        api_instance.create_fungible_tokens_transaction_request_from_address(
                            sender_address=ADDRESSES[blockchain], wallet_id=wallet_id, blockchain=blockchain, network=network, context="", create_fungible_tokens_transaction_request_from_address_rb=request)
    except:
        pass