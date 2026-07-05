# Rudeus
A self-hostable Discord bot for posting a Word of the Day in various languages

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

* Python 3.10 or newer
* `python3-venv` and `python3-pip`
* `git`
* `screen`

## Installation and Deployment

Follow these steps to get Rudeus running:

1. Download the code to your local folder:

```bash
git clone https://github.com/dadams05/Rudeus.git
cd Rudeus
```

2. Set up your Discord token. Create a `.env` file in the main folder, or rename `.env.example` to `.env`, and add your API key:

```env
DISCORD_TOKEN=your_secret_bot_token_here
```

3. Make the setup script runnable (if it isn't already):

```bash
chmod +x setup.sh
```

4. Run the setup script:

```bash
./setup.sh
```

The `setup.sh` script installs any missing packages, creates a virtual environment, installs the Python requirements, and starts the bot in the background for you.

## Managing the Bot Process

Because the bot runs in a `screen` session in the background, you will use these commands to interact with it in your terminal:

* **View the Bot's Console**: See the live logs and what the bot is doing right now:

```bash
screen -r <rudeus or whatever you named the session>
```

* **Leave the Console (Safely)**: To exit the view without killing the bot, press `Ctrl + A`, then press the `D` key.
* **Kill the Bot**: Completely stop the bot from running:

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
