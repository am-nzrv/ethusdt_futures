from time import sleep

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
from binance.client import Client

from secrets import MY_API_KEY, MY_API_SECRET


api_key = MY_API_KEY
api_secret = MY_API_SECRET
client = Client(api_key=api_key, api_secret=api_secret)


def get_candles(symbol, interval, n):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=n)
    df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low',
                                       'Close', 'Volume', 'Close time',
                                       'Quote asset volume',
                                       'Number of trades',
                                       'Taker buy base asset volume',
                                       'Taker buy quote asset volume',
                                       'Ignore'])
    df = df[['Close']]
    df = df.astype('float')
    return df


# Узнаем последние 100 свечей для ETHUSDT и BTCUSDT за 1 минуту.
ethusdt_100_candle = get_candles('ETHUSDT', Client.KLINE_INTERVAL_1MINUTE, 100)
btcusdt_100_candle = get_candles('BTCUSDT', Client.KLINE_INTERVAL_1MINUTE, 100)


# Соберем фрейм из цен ETHUSDT и BTCUSDT на закрытии.
ethusdt_price = pd.Series(ethusdt_100_candle['Close'].values)
btcusdt_price = pd.Series(btcusdt_100_candle['Close'].values)
y_axis = ethusdt_price.to_frame(name='ethusdt_price')
x_axis = btcusdt_price.to_frame(name='btcusdt_price')
frame = pd.concat([y_axis, x_axis], axis=1)


# Построим диаграмму рассеяния.
plt.scatter(frame.ethusdt_price, frame.btcusdt_price)
plt.xlabel('BTCUSDT')
plt.ylabel('ETHUSDT')
# plt.show()
# По ней можно сделать вывод, что имеется положительная корреляция
# между ценой фьючерса ETHUSDT и BTCUSDT.


# Вычислим линейныйы коэффициент зависимости ETHUSDT от BTCUSDT.
model = sm.OLS(frame.ethusdt_price, frame.btcusdt_price)
result = model.fit()
dependence_coefficient = result.params[0]


# Т.о собственное движение цены на фьючерс ETHUSDT, исключая влияние BTCUSDT,
# выглядит таким образом.
eth_real = ethusdt_price - dependence_coefficient * btcusdt_price


def change_percentage_check(price_list):
    """Функция для отслеживания изменения цены более чем на 1%."""
    min_price = price_list[0]
    max_price = price_list[0]

    for price in price_list:
        if price < min_price:
            min_price = price
        if price > max_price:
            max_price = price

    change_percentage = round(
        abs((max_price - min_price) / min_price * 100),2)

    if change_percentage > 1:
        message = f'За последний час цена изменилась на {change_percentage}%'
        return message
    return False


while True:
    """Бесконечный цикл, который раз в 1 час проверяет изменение собственной 
    цены фьючерся ETHUSDT, и отправляет сообщение,
    если цена изменилась более чем на 1%."""
    latest_ethusdt_prices = get_candles('ETHUSDT',
                                       Client.KLINE_INTERVAL_1MINUTE,
                                       100)
    latest_btcusdt_prices = get_candles('BTCUSDT',
                                       Client.KLINE_INTERVAL_1MINUTE,
                                       100)

    ethusdt_real_price = (latest_ethusdt_prices['Close'].values
                          - (dependence_coefficient
                             * latest_btcusdt_prices['Close'].values))

    current_change = change_percentage_check(ethusdt_real_price)

    if current_change:
        print(current_change)
    sleep(3600)
