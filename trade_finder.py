from datetime import datetime
from tradingview_ta import TA_Handler, Interval, Exchange, TradingView
import sqlite3 as sql
import json
import time
import logging
import os

log_file_date = str(datetime.now()).split(' ')[0].replace('-','_')
if not os.path.exists('Logs'):
    os.mkdir('Logs')
logging.basicConfig(filename=f'Logs/trading_{log_file_date}.log', filemode='a', format='%(message)s')

connection = sql.connect("trade.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS symbol_stats (symbol TEXT, exchange TEXT, screener TEXT, interval TEXT, status TEXT, buy_or_sell TEXT, rsi float, stock_k float, stock_d float, macd float, macd_signal float)")
connection.commit()

def get_indicators(sym,ex,scrn,interv):
    if str(interv[-1:]).lower() == 'm':
        if interv[:-1] == '15':
            hndlr = TA_Handler(
                symbol=sym,
                exchange=ex,
                screener=scrn,
                interval=Interval.INTERVAL_15_MINUTES,
                timeout=10
            )
    RSI = hndlr.get_analysis().indicators["RSI"]
    StochK = hndlr.get_analysis().indicators["Stoch.K"]
    StochD = hndlr.get_analysis().indicators["Stoch.D"]
    macd = hndlr.get_analysis().indicators["MACD.macd"]
    macdSignal = hndlr.get_analysis().indicators["MACD.signal"]
    return RSI,StochK,StochD,macd,macdSignal

def get_db_data(symbol, screener, interval):
    cursor.execute(f'SELECT status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal FROM symbol_stats WHERE symbol="{symbol}" and screener="{screener}" and interval="{interval}"')
    stats = cursor.fetchone()
    status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal = stats[0], stats[1], stats[2], stats[3], stats[4], stats[5], stats[6]
    return status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal

def check_status(symbol,screener,interval):
    status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal = get_db_data(symbol, screener, interval)
    if stock_k > 80 and stock_d > 80:
         buy_or_sell = 'sell'
         status = 'stock'
    if stock_k < 20 and stock_d < 20:
        buy_or_sell = 'buy'
        status = 'stock'
    if buy_or_sell == 'buy':
        if status == 'stock':
            if stock_k > 20 and stock_d > 20:
                if rsi > 50:
                    if macd > macd_signal:
                        status = 'OPEN LONG'
                    else:
                        status = 'stock'
                else:
                    status = 'stock'
            if stock_k > 80 or stock_d > 80:
                status = 'waiting'
    if buy_or_sell == 'sell':
        if status == 'stock':
            if stock_k < 80 and stock_d < 80:
                if rsi < 50:
                    if macd < macd_signal:
                        status = 'OPEN SHORT'
                    else:
                        status = 'stock'
                else:
                    status = 'stock'
            if stock_k < 20 or stock_d < 20:
                status = 'waiting'
    return status, buy_or_sell

def insert_into_db(symbol,exch,screener,interval,status,buy_or_sell):
    RSI,StochK,StochD,macd,macdSignal = get_indicators(symbol,exch,screener,interval)
    
    cursor.execute(f'SELECT count(*) FROM symbol_stats WHERE symbol="{symbol}" and screener="{screener}" and interval="{interval}"')
    exists = int(cursor.fetchone()[0])

    if exists == 0:
        sql = f"""INSERT INTO symbol_stats (symbol, exchange, screener, interval, status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal)
            VALUES ("{symbol}","{exch}","{screener}","{interval}","waiting","waiting",{RSI},{StochK},{StochD},{macd},{macdSignal})
                """
    else:
        status, buy_or_sell = check_status(symbol,screener,interval)
        sql = f"""UPDATE symbol_stats
        SET exchange = '{exch}', status = '{status}', buy_or_sell = '{buy_or_sell}', rsi = {RSI}, stock_k = {StochK}, stock_d = {StochD}, macd = {macd}, macd_signal = {macdSignal}
        WHERE symbol="{symbol}" and screener="{screener}" and interval="{interval}"
        """
    cursor.execute(sql)
    connection.commit()


with open('symbols.json') as f:
   symbols = json.load(f)

#while True:
for data in symbols['symbols']:
    symbol, exhange, screener, interval, status, buy_or_sell = data['symbol'], data['exhange'], data['screener'], data['interval'], data['status'], data['buy_or_sell']
    insert_into_db(symbol, exhange, screener, interval, status, buy_or_sell)
    status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal = get_db_data(symbol, screener, interval)
    logging.warning(f'{datetime.now()}::symbol:{symbol} || status:{status} || buy_or_sell:{buy_or_sell} || rsi:{rsi} || stock_k:{stock_k} || stock_d:{stock_d} || macd:{macd} || macd_signal:{macd_signal}')
    #if not status == 'waiting':
    if not status == 'waiting' and not status == 'stock':
        print(f'symbol:{symbol} || status:{status} || buy_or_sell:{buy_or_sell} || rsi:{rsi} || stock_k:{stock_k} || stock_d:{stock_d} || macd:{macd} || macd_signal:{macd_signal}')
    connection.commit()
    #time.sleep(60)