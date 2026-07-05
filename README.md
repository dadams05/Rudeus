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

* **Made for Raspberry Pi**: Built and tested on a Raspberry Pi (Linux). Other systems will require a different setup not discussed here.
* **Background Execution**: Designed to run inside a GNU `screen` session so it can stay live and auto-restart cleanly.
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

### 2. Set Up Your Discord Token

To connect the bot to Discord, create a `.env` file using one of these two options:

#### Option A: Copy the template file

```bash
cp .env.example .env
nano .env
```

Replace the dummy token with your real one: `DISCORD_TOKEN=your_actual_token_here`.

#### Option B: Create a new file directly

```bash
nano .env
```

Type out your token line exactly like this: `DISCORD_TOKEN=your_actual_token_here`.

Finally, make sure the update script has permission to execute:

```bash
chmod +x updater.sh
```

### 3. Launch Inside Screen

To ensure the bot stays open in the background and can safely restart itself during updates, you must create the `screen` terminal *before* running the script:

1. Open a new background terminal session named `rudeus`:
```bash
screen -S rudeus
```

2. Now, inside this new terminal window, run the bot using your virtual environment:
```bash
./.venv/bin/python rudeus.py
```

3. Once the bot successfully turns on, leave it running in the background by detaching from the window. Press **`Ctrl + A`**, then press **`D`**.

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
