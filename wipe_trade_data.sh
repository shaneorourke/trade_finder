#!/bin/bash

PATH=$(dirname "$0")
sudo pkill -9 -f "python webserver.py"
cd $PATH &&
sudo rm trade.db