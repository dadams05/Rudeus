#!/bin/bash

OLD_PID=$1

# loop until the old process is no longer running
while kill -0 "$OLD_PID" 2>/dev/null; do
    sleep 0.5
done

git pull origin
./.venv/bin/python ./rudeus.py
