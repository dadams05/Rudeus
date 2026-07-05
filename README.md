# Rudeus

A self-hostable Discord bot for posting a Word of the Day in various languages.

## Features

* **Multi-Language Support**: Choose from 24 different languages to post in your server.
* **Pronunciation Media**: Automatically downloads and attaches MP3 files so you can actually hear how the word and example phrase are pronounced.
* **Flexible Scheduling**: Tell the bot when to post using normal phrases like "3:30 PM" or "midnight" directly in Discord.
* **Built-in Updates**: The bot can download code updates straight from GitHub and restart itself without you having to touch the server.

## Technical Design Notes

* **Made for Raspberry Pi**: This project is built and tested to run on a Raspberry Pi using a Linux operating system. This bot can work on other operating systems, but will require configuration not discussed here.
* **Runs in the Background**: The bot uses a tool called `screen` (in a session named `rudeus`). This just means it runs safely in the background and can restart itself after an update without you needing to manually step in.
* **Auto-Updates**: Auto-updating is turned off by default. You can use a Discord command to check for updates manually, or you can turn on auto-updates using the bot's chat commands.

## System Prerequisites

Make sure your Raspberry Pi or Linux setup has these installed:

```bash
sudo apt update
sudo apt install python3-venv python3-pip git screen -y
```

## Installation and Deployment

Follow these steps to get Rudeus manually configured and running:

### 1. Download the Code

Clone the repository and enter the directory:

```bash
git clone https://github.com/dadams05/Rudeus.git
cd Rudeus
```

### 2. Set Up the Environment & Dependencies

Create a Python virtual environment and install the required packages:

```bash
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

### 3. Add Your Discord Token

Create a `.env` file in the main folder (or rename `.env.example` to `.env`) and add your Discord bot token:

```env
DISCORD_TOKEN=your_secret_bot_token_here
```

### 4. Make the Updater Executable

Ensure the auto-updater has permission to run when triggered by the bot:

```bash
chmod +x updater.sh
```

### 5. Launch the Bot inside Screen

Create a new background window named `rudeus` and launch the bot inside it:

```bash
screen -S rudeus ./.venv/bin/python rudeus.py
```

*(Once it boots up successfully, you can leave it running in the background by pressing `Ctrl + A`, then `D`)*.

## Managing the Bot Process

Because the bot runs in a dedicated `screen` session, you will use these commands to manage it in your terminal:

* **View the Bot's Console / Logs**: See what the bot is doing right now:

```bash
screen -r rudeus
```

* **Leave the Console Safely**: To hide the console view without shutting down the bot, press `Ctrl + A`, then press the `D` key on your keyboard.
* **Kill the Bot**: Completely stop the bot process from your main terminal:

```bash
screen -X -S rudeus quit
```

## Chat Commands Reference

The bot sets up all its slash commands automatically when it turns on:

| Command | Parameter | Description |
| --- | --- | --- |
| `/info` | *None* | Shows bot info, uptime, post time, and a list of available languages. |
| `/add_wotd` | `channel`, `language` | Tells the bot to start posting a specific language in a channel. (Has auto-complete!). |
| `/remove_wotd` | `channel`, `language` | Stops posting a specific language in a channel. |
| `/show_config` | *None* | Shows a list of which languages are currently posting in which channels. |
| `/clear_config` | *None* | Wipes all your Word of the Day channel setups. |
| `/set_post_time` | `time_input` | Changes what time the words post (e.g., "3:30 PM", "18:00"). |
| `/set_auto_update` | `value` (`on`/`off`) | Turns the automatic GitHub updates on or off. |
| `/check_for_update` | *None* | Manually checks GitHub for a new update and installs it right then. |
