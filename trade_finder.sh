#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
source env/bin/activate &&
python trade_finder.py