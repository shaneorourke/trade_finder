#!/bin/bash

PATH=$(dirname "$0")

cd $PATH &&
python -m venv env &&
source env/bin/activate &&
pip install -r requirements.txt &&
deactivate