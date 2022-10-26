#!/bin/bash

PATH=$(dirname "$0")
sudo pkill -9 -f "python webserver.py"
cd $PATH &&
source env/bin/activate &&
python wipe_trade_data.py