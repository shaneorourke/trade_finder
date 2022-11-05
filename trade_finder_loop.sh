#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
source env/bin/activate &&

while 1=1
do
    clear
    python trade_finder.py
done