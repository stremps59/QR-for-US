#!/usr/bin/env bash

# Upgrade pip
pip install --upgrade pip

# Install all normal dependencies
pip install -r requirements.txt

# Override qrcode with GitHub master branch that includes advanced styling
pip install git+https://github.com/lincolnloop/python-qrcode.git@master
