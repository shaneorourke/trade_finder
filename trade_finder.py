from datetime import datetime
import datetime as dt
from tradingview_ta import TA_Handler, Interval, Exchange, TradingView
from pybit.usdt_perpetual import HTTP
import bybit_secrets as sc
import sqlite3 as sql
import json
import time
import logging
import os
import pandas as pd
import ta

session = HTTP("https://api.bybit.com",
               api_key= sc.API_KEY, api_secret=sc.API_SECRET,request_timeout=30)

now_today = dt.datetime.now()
now_timestamp = dt.datetime.now()
now = now_today + dt.timedelta(days=-1)
today = dt.datetime(now.year, now.month, now.day)

log_file_date = str(datetime.now()).split(' ')[0].replace('-','_')
if not os.path.exists('Logs'):
    os.mkdir('Logs')
logging.basicConfig(filename=f'Logs/trading_{log_file_date}.log', filemode='a', format='%(message)s')

connection = sql.connect("trade.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS symbol_stats (symbol TEXT, exchange TEXT, screener TEXT, interval TEXT, status TEXT, buy_or_sell TEXT, rsi float, stock_k float, stock_d float, macd float, macd_signal float, ema20 float, ema50 float)")
connection.commit()

def get_tv_indicators(sym,ex,scrn,interv):
    if str(interv[-1:]).lower() == 'm':
        if interv[:-1] == '15':
            hndlr = TA_Handler(
                symbol=sym,
                exchange=ex,
                screener=scrn,
                interval=Interval.INTERVAL_15_MINUTES,
                timeout=10
            )
        if interv[:-1] == '30':
            hndlr = TA_Handler(
                symbol=sym,
                exchange=ex,
                screener=scrn,
                interval=Interval.INTERVAL_30_MINUTES,
                timeout=10
            )
    if str(interv[-1:]).lower() == 'h':
        if interv[:-1] == '1':
            hndlr = TA_Handler(
                symbol=sym,
                exchange=ex,
                screener=scrn,
                interval=Interval.INTERVAL_1_HOUR,
                timeout=10
            )
    RSI = hndlr.get_analysis().indicators["RSI"]
    StochK = hndlr.get_analysis().indicators["Stoch.K"]
    StochD = hndlr.get_analysis().indicators["Stoch.D"]
    macd = hndlr.get_analysis().indicators["MACD.macd"]
    macdSignal = hndlr.get_analysis().indicators["MACD.signal"]
    ema20 = hndlr.get_analysis().indicators["EMA20"]
    ema50 = hndlr.get_analysis().indicators["EMA50"]
    return RSI,StochK,StochD,macd,macdSignal, ema20, ema50

def applytechnicals(df):
    df['FastSMA'] = df.close.rolling(20).mean()
    df['SlowSMA'] = df.close.rolling(50).mean()
    df['%K'] = ta.momentum.stoch(df.high,df.low,df.close,window=14,smooth_window=3)
    df['%D'] = df['%K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df.close,window=14)
    df['macd'] = ta.trend.macd(df.close)
    df['macd_signal'] = ta.trend.macd_signal(df.close)
    df.dropna(inplace=True)
    return df

def get_bybit_bars(trading_symbol, interval, startTime, apply_technicals):
    interval = str(interval).replace('m','')
    startTime = str(int(startTime.timestamp()))
    response = session.query_kline(symbol=trading_symbol,interval=interval,from_time=startTime)
    df = pd.DataFrame(response['result'])
    df.start_at = pd.to_datetime(df.start_at, unit='s') + pd.DateOffset(hours=1)
    df.open_time = pd.to_datetime(df.open_time, unit='s') + pd.DateOffset(hours=1)
    if apply_technicals:
        applytechnicals(df)
    return df

def get_db_data(symbol, screener, interval):
    cursor.execute(f'SELECT status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal, ema20, ema50 FROM symbol_stats WHERE symbol="{symbol}" and screener="{screener}" and interval="{interval}"')
    stats = cursor.fetchone()
    status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal, ema20, ema50 = stats[0], stats[1], stats[2], stats[3], stats[4], stats[5], stats[6], stats[7], stats[8]
    return status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal, ema20, ema50

def check_status(symbol,screener,interval):
    status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal, ema20, ema50 = get_db_data(symbol, screener, interval)
    # Sell
    if stock_k > 80 and stock_d > 80:
        status = 'sell-stock-waiting'
        buy_or_sell = 'sell'

    if status == 'sell-stock-waiting':
        if stock_k < 80 and stock_d < 80:
            status = 'sell-stock'
            buy_or_sell = 'sell'

    if status == 'sell-stock':
        if rsi < 50 and macd < macd_signal:
            status = 'OPEN SHORT'
            buy_or_sell = 'sell'

    # Status Resets
    if status == 'OPEN SHORT':
        if rsi > 50 or macd > macd_signal:
            status = 'sell-stock'
        if stock_k < 20 or stock_d < 20:
            status = 'waiting'

    if status == 'sell-stock':
        if stock_k > 80 and stock_d > 80:
            status = 'sell-stock-waiting'

    # Buys
    if stock_k < 20 and stock_d < 20:
        status = 'buy-stock-waiting'
        buy_or_sell = 'buy'

    if status == 'buy-stock-waiting':
        if stock_k > 20 and stock_d > 20:
            status = 'buy-stock'
            buy_or_sell = 'buy'

    if status == 'buy-stock':
        if rsi > 50 and macd > macd_signal:
            status = 'OPEN LONG'
            buy_or_sell = 'buy'

    # Status Resets
    if status == 'OPEN LONG':
        if rsi < 50 or macd < macd_signal:
            status = 'buy-stock'
        if stock_k > 80 or stock_d > 80:
            status = 'waiting'

    if status == 'buy-stock':
        if stock_k < 20 and stock_d < 20:
            status = 'buy-stock-waiting'

    return status, buy_or_sell


def insert_into_db(symbol,exch,screener,interval,status,buy_or_sell,RSI,StochK,StochD,macd,macdSignal,ema20,ema50):
   
    cursor.execute(f'SELECT count(*) FROM symbol_stats WHERE symbol="{symbol}" and screener="{screener}" and interval="{interval}"')
    exists = int(cursor.fetchone()[0])

    if exists == 0:
        sql = f"""INSERT INTO symbol_stats (symbol, exchange, screener, interval, status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal, ema20, ema50)
            VALUES ("{symbol}","{exch}","{screener}","{interval}","waiting","waiting",{RSI},{StochK},{StochD},{macd},{macdSignal}, {ema20}, {ema50})
                """
    else:
        sql = f"""UPDATE symbol_stats
        SET exchange = '{exch}', status = '{status}', buy_or_sell = '{buy_or_sell}', rsi = {RSI}, stock_k = {StochK}, stock_d = {StochD}, macd = {macd}, macd_signal = {macdSignal}, ema20 = {ema20}, ema50 = {ema50}
        WHERE symbol="{symbol}" and screener="{screener}" and interval="{interval}"
        """
    cursor.execute(sql)
    connection.commit()


with open('symbols.json') as f:
   symbols = json.load(f)

#while True:
for data in symbols['symbols']:
    symbol, exhange, screener, interval, status, buy_or_sell = data['symbol'], data['exhange'], data['screener'], data['interval'], data['status'], data['buy_or_sell']
    if exhange == 'ByBit':
        candles = get_bybit_bars(symbol,interval,today,True)
        most_recent = candles.iloc[-1]
        close_price = most_recent.close
        ema20 = most_recent.FastSMA
        ema50 = most_recent.SlowSMA
        StochK = most_recent['%K']
        StochD = most_recent['%D']
        RSI = most_recent['rsi']
        macd = most_recent['macd']
        macdSignal = most_recent['macd_signal']
    else:
        RSI,StochK,StochD,macd,macdSignal,ema20,ema50 = get_tv_indicators(symbol,exhange,screener,interval)
    #print(f'symbol:{symbol} || StochK:{StochK} || StochD:{StochD} || RSI:{RSI} || macd:{macd} || macdSignal:{macdSignal} || ema20:{ema20} || ema50:{ema50}')
    insert_into_db(symbol, exhange, screener, interval, status, buy_or_sell, RSI, StochK, StochD, macd, macdSignal, ema20, ema50)
    status, buy_or_sell = check_status(symbol,screener,interval)
    insert_into_db(symbol, exhange, screener, interval, status, buy_or_sell, RSI, StochK, StochD, macd, macdSignal, ema20, ema50)
    logging.warning(f'{datetime.now()}::symbol:{symbol} || status:{status} || buy_or_sell:{buy_or_sell} || rsi:{RSI} || stock_k:{StochK} || stock_d:{StochD} || macd:{macd} || macd_signal:{macdSignal} || ema20:{ema20}, ema50:{ema50}')
    #if not status == 'waiting':
    #if not status == 'waiting' and not status == 'stock':
    #    print(f'symbol:{symbol} || status:{status} || buy_or_sell:{buy_or_sell} || rsi:{rsi} || stock_k:{stock_k} || stock_d:{stock_d} || macd:{macd} || macd_signal:{macd_signal} || ema20:{ema20}, ema50:{ema50}')
    connection.commit()
    #time.sleep(60)