from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime
import config

from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import TimeInForce
from alpaca.data.timeframe import TimeFrame

import yfinance as yf

import backtrader as bt
import backtrader.analyzers as btanalyzers

from kucoin.client import Trade as Client
# from kucoin.client import Client
from kucoin.market import market

api_key = config.kucoin_api_key
api_secret = config.kukoin_api_secret
api_passphrase = config.kukoin_api_passphrase

kucoin_client = Client(api_key, api_secret, api_passphrase)
client_market = market.MarketData(url='https://api.kucoin.com')
client_alpaca = TradingClient(api_key=config.ALPACA_API_KEY, secret_key=config.ALPACA_SECRET_KEY, paper=True)
acount = dict(client_alpaca.get_account())
client_alpaca_historical = CryptoHistoricalDataClient()
request_params = CryptoLatestQuoteRequest(symbol_or_symbols=["BTC/USD", 'ETH/USDT', "BTC/USDT", "LTC/USDT"])


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        ticker = request.form.get('ticker') ##
        qty = request.form.get('qty')       ##
        print(ticker)
        print(qty)
    return render_template('index.html') #'YUDIN TRADE PROJECT'

@app.route('/apitrade/', methods=['POST', 'GET']) #work
def trading():
    url = "https://paper-api.alpaca.markets/v2/positions"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": config.ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": config.ALPACA_SECRET_KEY
    }
    response = requests.get(url, headers=headers)
    lst_for_parsing = []
    positions = response.json()
    symbol = ''
    qty = ''
    market_value = ''
    unrealized_pl = ''
    currency = ''
    cash = ''
    portfolio_value = ''

    for position in positions:
        for property_name, value in position.items():
            # print(f"\"{property_name}\": {value}")
            if property_name == "symbol":  # торговая пара BTCUSD
                symbol = f"{property_name}: {value}"
                lst_for_parsing.append((f"{property_name}: {value}"))
            if property_name == 'qty':  # количество в крипте
                qty = f"{property_name}: {value}"
                lst_for_parsing.append((f"{property_name}: {value}"))
            if property_name == 'market_value':  # сколько в крипте
                market_value = f"{property_name}: {value}"
                lst_for_parsing.append((f"{property_name}: {value}"))

    account = client_alpaca.get_account()
    for property_name, value in account:
        if property_name == 'currency':
            currency = f"{property_name}: {value}"
            #lst.append(f"{property_name}: {value}")
        if property_name == 'cash':
            cash = f"{property_name}: {value}"
            #lst.append(f"{property_name}: {value}")
        if property_name == 'portfolio_value':
            portfolio_value = value
            unrealized_pl = round(float(value) - 100_000, 2)
            #lst.append(f"{property_name}: {value}")

    lst = ''
    if request.method == 'POST':
        ordertype = request.form.get('ordertype')
        orderside = request.form.get('side')
        ticker = request.form.get('ticker')
        qty = request.form.get('qty')
        market_order_data = MarketOrderRequest(
            symbol=ticker,
            qty=qty,  # Количество
            side=orderside,  # BUY or SELL
            time_in_force=TimeInForce.GTC  # GTC - Good till Canceled or Generate to close
        )
        account = client_alpaca.get_account()
        lst = []
        for property_name, value in account:
            # print(f"{property_name}: {value}")
            # lst.append(property_name and value)
            if property_name == 'currency':
                lst.append(f"{property_name}: {value}")
            if property_name == 'cash':
                lst.append(f"{property_name}: {value}")
            if property_name == 'portfolio_value':
                lst.append(f"{property_name}: {value}")
        client_alpaca.submit_order(market_order_data)
    return render_template('apitrade.html', lst=lst, symbol=symbol,qty=qty,market_value=market_value,unrealized_pl=unrealized_pl, currency=currency, cash=cash, portfolio_value=portfolio_value)


@app.route('/margin-trading/', methods=['POST', 'GET']) #work 13.08.2024
def margin_trading():
    lst = ''
    msg = 'None'
    if request.method == 'POST':
        lst = []
        ticker = request.form.get('ticker')
        if ticker == 'BTC/USDT':
            for_kcoin = 'BTC-USDT'
        elif ticker == 'ETH/USDT':
            for_kcoin = 'ETH-USDT'
        elif ticker == 'LTC/USDT':
            for_kcoin = 'LTC-USDT'
        else:
            return redirect('/margin-trading/')
        for key, value in client_market.get_ticker(for_kcoin).items():
            if key == 'price':
                price_btc_usdt_kukoin = float(value)
                try:
                    alpaca_url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/bars?symbols={ticker}"
                    headers = {"accept": "application/json"}
                    response = requests.get(alpaca_url, headers=headers)
                    last_price = [i['c'] for ii in response.json().values() for i in ii.values()]
                    price_btc_usdt_alpaca = last_price[0]
                    diferent = round(float(price_btc_usdt_alpaca) / float(price_btc_usdt_kukoin) / 100, 4)
                    lst.append((f'Alpaca {for_kcoin} {price_btc_usdt_alpaca} {diferent}% {price_btc_usdt_kukoin} {for_kcoin} Kukoin').split()) ## тут ифо для консоли
                except Exception as e:
                    print('>>>', e.args)
    return render_template('margin-trading.html',  lst=lst)




@app.route('/backtesting/', methods=['POST', 'GET']) #not work (работает но надо добавить обработчик который при ошибке IndexError: list index out of range не выкидал на Werkzeug)
def history_trading():
    lst = []
    ticker = ''
    if request.method == 'POST':
        symbol_or_symbols = request.form.get('ticker')
        if symbol_or_symbols == "BTC/USD":
            ticker = "BTC-USD"
        elif symbol_or_symbols == "ETH/USD":
            ticker = "ETH-USD"
        elif symbol_or_symbols == "LTC/USD":
            ticker = "LTC-USD"

        timeframe = request.form.get('timeframe')
        start = request.form.get('start')
        end = request.form.get('end')

        list_history = [symbol_or_symbols, timeframe, start, end]

        if list_history[1] == "Min":
            timeframe = TimeFrame.Minute
            interval = '1T'
        elif list_history[1] == "Hour":
            timeframe = TimeFrame.Hour
            interval = '1H'
        elif list_history[1] == "Day":
            timeframe = TimeFrame.Day
            interval = '1D'
        elif list_history[1] == "Week":
            timeframe = TimeFrame.Week
            interval = '1W'
        elif list_history[1] == "Month":
            timeframe = TimeFrame.Month
            interval = '1M'
        else:
            return redirect('/backtesting/')

        try:
            # Use the requests library to make the API call
            url = f"https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={symbol_or_symbols}&timeframe={interval}&start={start}T00%3A00%3A00Z&end={end}T00%3A00%3A00Z&limit=1000&sort=asc"
            response = requests.get(url, headers={'APCA-API-KEY-ID': config.ALPACA_API_KEY, 'APCA-API-SECRET-KEY': config.ALPACA_SECRET_KEY})
            response.raise_for_status()  # Check for request errors
            bars = response.json()
            crypto_ticker = yf.Ticker(ticker=ticker)
            crypto_data = crypto_ticker.history(start=list_history[2], end=list_history[3], interval=interval)
            alpaca_values = [i for i in crypto_data['Open']]
            yahoofinance = bars.values()
            kucoin_values = [i['o'] for symbol_data in yahoofinance if symbol_data is not None for i in symbol_data['BTC/USD'] or symbol_data['ETH/USD']]
            time_values = [i['t'] for symbol_data in yahoofinance if symbol_data is not None for i in symbol_data['BTC/USD'] or symbol_data['ETH/USD']]

            for time_stamp, alpaca_history, yahoo_history in zip(time_values, alpaca_values, kucoin_values):
                diferent = round(float(alpaca_history) / float(yahoo_history) / 100, 4)
                parsed_time = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%SZ')
                time_stmp = parsed_time.strftime('%Y/%m/%d')
                lst.append((f'{time_stmp} {symbol_or_symbols} Alpaca {round(alpaca_history)} {diferent}%  Yahoo {round(yahoo_history)}').split())

        except IndexError as e:
            lst = ["IndexError: list index out of range. Please check your data range."]

    return render_template('backtesting.html', lst=lst)


@app.route('/test-strategy', methods=['POST', 'GET']) #work
def strategy():
    lst = 'Null'
    sharperatio = 0
    message = 0
    cash = 100000

    if request.method == 'POST':
        lst = []
        symbol_or_symbols = request.form.get('ticker')
        timeframe = request.form.get('timeframe')  # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        start = request.form.get('start')
        end = request.form.get('end')
        input_ma_fast = int(request.form.get('ma_fast'))
        input_ma_slow = int(request.form.get('ma_slow'))
        percents = int(request.form.get('percents'))

        class MaCrossStrategy(bt.Strategy):
            def __init__(self):
                ma_fast = bt.ind.SMA(period=input_ma_fast)
                ma_slow = bt.ind.SMA(period=input_ma_slow)
                self.crossover = bt.ind.CrossOver(ma_fast, ma_slow)

            def next(self):
                if not self.position:
                    if self.crossover > 0:
                        self.buy()
                elif self.crossover < 0:
                    self.close()

        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=yf.download(tickers=symbol_or_symbols,
                                                        start=start, end=end, auto_adjust=True, interval=timeframe))
        cerebro.adddata(data)
        cerebro.addstrategy(MaCrossStrategy)
        lst.append(cerebro.broker.setcash(100000.0))
        cerebro.addsizer(bt.sizers.PercentSizer, percents=percents)
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')  # коефициент шарпа
        cerebro.addanalyzer(btanalyzers.Transactions, _name='trans')
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trades')
        back = cerebro.run()
        cerebro.broker.getvalue()  # 100%что то комплит и сколько денег получилось
        back[0].analyzers.sharpe.get_analysis()
        for i, ii in back[0].analyzers.sharpe.get_analysis().items():
            lst.append((f'{i} {ii} {cerebro.broker.getvalue()}').split())
            message = int(cerebro.broker.getvalue() - 100_000)
            sharperatio = lst[0]
            cash = cash+message
    return render_template('test-strategy.html', lst=lst, message=message, sharperatio=sharperatio, cash=cash)


@app.route('/contacts')
def contact():
    return render_template('contacts.html')



if __name__ == '__main__':
    app.run(debug=True)

