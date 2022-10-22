#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
source env/bin/activate &&
pip install -r requirements.txt &&
deactivate