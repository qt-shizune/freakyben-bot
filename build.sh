#!/bin/bash

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install --no-binary :all: --prefer-binary -r requirements.txt
