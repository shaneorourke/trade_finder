#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
source env/bin/activate &&
python wipe_trade_data.py