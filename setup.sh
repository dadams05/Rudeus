#!/usr/bin/env bash

# Exit immediately if any command fails
set -e

echo "=========================================="
echo "Starting Rudeus Bot Environment Setup..."
echo "=========================================="

# 1. Install system prerequisites if missing (python3-venv and screen)
echo "[1/4] Checking system dependencies..."
if ! command -v screen &> /dev/null || ! python3 -c "import venv" &> /dev/null; then
    echo "Installing screen and python3-venv via apt..."
    sudo apt-get update && sudo apt-get install -y screen python3-venv python3-pip
else
    echo "Dependencies verified."
fi

# 2. Set up the virtual environment
echo "[2/4] Creating Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists. Skipping."
fi

# 3. Upgrade pip and install package requirements
echo "[3/4] Installing requirements inside the virtual environment..."
.venv/bin/pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    .venv/bin/pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found! Skipping dependency install."
fi

# 4. Kill any old detached screen instances with the same name to prevent overlaps
if screen -list | grep -q "\.rudeus\s"; then
    echo "Found an existing 'rudeus' screen instance. Terminating it to restart..."
    screen -X -S rudeus quit || true
fi

# 5. Launch the bot inside a detached screen session named "rudeus"
echo "[4/4] Launching the bot in a detached screen session named 'rudeus'..."
screen -dmS rudeus .venv/bin/python rudeus.py

echo "=========================================="
echo "Setup Successful!"
echo "=========================================="
echo "-> Your bot is now running in the background."
echo "-> To view the live bot logs/console, run: screen -r rudeus"
echo "-> To exit the screen without killing the bot, press: Ctrl + A, then D"
echo "=========================================="
