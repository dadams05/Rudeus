# Rudeus

A self-hostable Discord bot for posting a Word of the Day in various languages.

![rudy and co](images/banner_2k.png) 

## Contents

* [Features](#features)
* [Technical Design Notes](#technical-design-notes)
* [System Prerequisites](#system-prerequisites)
* [Discord Developer Portal Setup](#discord-developer-portal-setup)
* [Installation and Deployment](#installation-and-deployment)
* [Managing the Bot Process](#managing-the-bot-process)
* [Chat Commands Reference](#chat-commands-reference)

## Features

* **Multi-Language Support**: Choose from 24 different languages to post in your server.
* **Pronunciation Media**: Automatically downloads and attaches MP3 files so you can hear how the word and example phrase sound.
* **Flexible Scheduling**: Customize the post time using natural phrases (e.g., "3:30 PM", "midnight") directly in chat.
* **Built-in Updates**: Can download updates from GitHub and automatically restart itself.

## Technical Design Notes

* **Made for Raspberry Pi**: Built and tested specifically for Raspberry Pi (Linux). Other operating systems require separate configuration.
* **Background Execution**: Runs inside a GNU `screen` session named `rudeus` so it can stay live and auto-restart cleanly.
* **Auto-Updates**: Disabled by default. Can be toggled on via chat command or checked manually.

## System Prerequisites

Install the required tools on your Linux setup:

```bash
sudo apt update && sudo apt install python3-venv python3-pip git screen -y
```

## Discord Developer Portal Setup

You need a Discord Developer Account. If you get stuck, this [video guide](https://www.youtube.com/watch?v=CHbN_gB30Tw) offers a helpful visual walkthrough.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Name your bot.
2. Go to the **Bot** tab on the left sidebar. Under **Privileged Gateway Intents**, turn on:
   * Presence Intent
   * Server Members Intent
   * Message Content Intent
3. Go to the **OAuth2** tab, then select **URL Generator**.
   * Under **Scopes**, check `bot`.
   * Under **Bot Permissions**, select these bare minimums: *View Channels*, *Send Messages*, *Embed Links*, and *Attach Files*.
   * Copy the generated link at the bottom to invite the bot to your server.
4. While still on the **Bot** tab, find the **Token** section and click **Reset Token** to copy your bot's secret API key for the next steps.

## Installation and Deployment

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/dadams05/Rudeus.git
cd Rudeus

python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

### 2. Configure Credentials & Permissions

Create a `.env` file from the example template and paste your Discord bot token inside it:

```bash
cp .env.example .env
nano .env  # Paste your token into: DISCORD_TOKEN=your_token_here
```

Give the update script execution permissions:

```bash
chmod +x updater.sh
```

### 3. Launch Inside Screen

Start the bot inside a background window named `rudeus`:

```bash
screen -S rudeus ./.venv/bin/python rudeus.py
```

*To leave the bot running in the background, press `Ctrl + A`, then `D` to detach.*

## Managing the Bot Process

Use these terminal commands to manage your background `screen` session:

* **View Console / Logs**: `screen -r rudeus`
* **Disconnect Safely (Keep Bot Alive)**: Press `Ctrl + A`, then `D`
* **Kill the Bot Process**: `screen -X -S rudeus quit`

## Chat Commands Reference

The bot syncs its application slash commands automatically on startup:

| Command | Parameter | Description |
| --- | --- | --- |
| `/info` | *None* | Shows bot info, uptime, post time, and available languages. |
| `/add_wotd` | `channel`, `language` | Configures a channel to post a language's WOTD. (Has autocomplete). |
| `/remove_wotd` | `channel`, `language` | Stops posting a specific language in a channel. |
| `/show_config` | *None* | Lists which languages are currently mapped to which channels. |
| `/clear_config` | *None* | Wipes all active channel configurations. |
| `/set_post_time` | `time_input` | Changes global post time using human terms (e.g., "3:30 PM", "18:00"). |
| `/set_auto_update` | `value` (`on`/`off`) | Turns automatic GitHub code updates on or off. |
| `/check_for_update` | *None* | Manually checks GitHub and applies updates immediately. |
