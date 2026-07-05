#!/bin/bash

OLD_PID=$1

# 1. loop until the old process is no longer running
while kill -0 "$OLD_PID" 2>/dev/null; do
    sleep 0.5
done

# 2. pull the newest code from GitHub
git pull origin

# 3. upgrade pip and reinstall requirements inside the venv
echo "Updating virtual environment packages..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

# 4. restart the bot
echo "Starting Rudeus..."
./.venv/bin/python ./rudeus.py
