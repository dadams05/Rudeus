#!/bin/bash

wait $1
git pull origin
./.venv/bin/python ./rudeus.py
