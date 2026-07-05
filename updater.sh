#!/bin/bash

OLD_PID=$1

# 1. Loop until the old process is no longer running
while kill -0 "$OLD_PID" 2>/dev/null; do
    sleep 0.5
done

# 2. Pull the newest code from GitHub
git pull origin main

# 3. Upgrade pip and reinstall requirements inside the venv
echo "Updating virtual environment packages..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

# 4. Restart the bot cleanly
echo "Starting Rudeus..."

# Check if the script itself is currently running inside an active screen session named "rudeus"
# or if a "rudeus" screen session is already active on the system.
if [[ "$STY" == *".rudeus"* ]] || screen -list | grep -q "\.rudeus\s"; then
    echo "Detected screen environment. Ensuring bot spins up inside screen..."
    
    # Force close any stale screen wrappers
    screen -X -S rudeus quit 2>/dev/null || true
    
    # Launch a fresh, detached screen session
    screen -dmS rudeus ./.venv/bin/python ./rudeus.py
else
    # Fallback: If the user manually ran it outside of screen, just run it normally
    echo "No screen session detected. Starting bot in standard foreground process."
    ./.venv/bin/python ./rudeus.py
fi
