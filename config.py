import os

import alpaca_trade_api as tradeapi

from dotenv import load_dotenv
load_dotenv()

# API Info for fetching data, portfolio, etc. from Alpaca
BASE_URL = "https://paper-api.alpaca.markets/v2"
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY') #"YOUR_API_KEY"
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY') #"YOUR_SECRET_KEY"
rest_api = tradeapi.REST(key_id=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY)

# Instantiate REST API Connection
api = tradeapi.REST(key_id=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY, api_version='v2')

HEADERS = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCE-API-SECRET-KEY': ALPACA_SECRET_KEY
}

kucoin_api_key = os.getenv('kucoin_api_key') #'your_api_key'
kukoin_api_secret = os.getenv('kukoin_api_secret') #'your_api_secret'
kukoin_api_passphrase = os.getenv('kukoin_api_passphrase') #'your_api_passphrase'
