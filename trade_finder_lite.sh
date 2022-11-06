#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
$(clear >&2) &&
sqlite3 trade.db 'select symbol, exchange, screener, interval, status, ema_cross from symbol_stats'