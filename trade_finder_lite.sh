#!/bin/bash

PATH=$(dirname "$0")
x=1
cd $PATH &&
while [ $x -le 5 ]
do
    /usr/bin/clear &&
    /usr/bin/sqlite3 trade.db 'select symbol, exchange, screener, interval, status, ema_cross from symbol_stats where not(status like "%waiting%" and ema_cross like "%waiting%")'
    /usr/bin/sleep 30
done