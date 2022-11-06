#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
while 1=1
do
    /usr/bin/clear &&
    /usr/bin/sqlite3 trade.db 'select symbol, exchange, screener, interval, status, ema_cross from symbol_stats'
    sleep 30
done