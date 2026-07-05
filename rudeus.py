import os
import json
import asyncio
import discord
import tzlocal
import datetime
import requests
import xmltodict
import dateparser
import subprocess
from typing import Literal
from shutil import copyfile
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discord import app_commands
from bs4 import BeautifulSoup as bs
from discord.ext import commands, tasks 

# ==========================================
# CONSTANTS & CONFIGURATION INITIALIZATION
# ==========================================

VERSION = "v1.2.2"
CONFIG_FILE = "config.json"
DEFAULT_CONFIG_FILE = "default.json"
START = datetime.datetime.now()
SCHEDULE = datetime.time(hour=3, minute=30, tzinfo=ZoneInfo(tzlocal.get_localzone_name()))

CUSTOM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

MAPPING = {
    "Arabic": "https://wotd.transparent.com/rss/arabic-widget.xml",
    "Chinese": "https://wotd.transparent.com/rss/zh-widget.xml",
    "Dari": "https://wotd.transparent.com/rss/dari-widget.xml",
    "Dutch": "https://wotd.transparent.com/rss/nl-widget.xml",
    "Esperanto": "https://wotd.transparent.com/rss/esp-widget.xml",
    "French": "https://wotd.transparent.com/rss/fr-widget.xml",
    "German": "https://wotd.transparent.com/rss/de-widget.xml",
    "Hebrew": "https://wotd.transparent.com/rss/hebrew-widget.xml",
    "Hindi": "https://wotd.transparent.com/rss/hindi-widget.xml",
    "Indonesian": "https://wotd.transparent.com/rss/indonesian-widget.xml",
    "Irish": "https://wotd.transparent.com/rss/ga-widget.xml",
    "Italian": "https://wotd.transparent.com/rss/it-widget.xml",
    "Japanese": "https://wotd.transparent.com/rss/ja-widget.xml",
    "Korean": "https://wotd.transparent.com/rss/korean-widget.xml",
    "Latin": "https://wotd.transparent.com/rss/la-widget.xml",
    "Norwegian": "https://wotd.transparent.com/rss/norwegian-widget.xml",
    "Pashto": "https://wotd.transparent.com/rss/pashto-widget.xml",
    "Polish": "https://wotd.transparent.com/rss/polish-widget.xml",
    "Portuguese": "https://wotd.transparent.com/rss/pt-widget.xml",
    "Russian": "https://wotd.transparent.com/rss/ru-widget.xml",
    "Spanish": "https://wotd.transparent.com/rss/es-widget.xml",
    "Swedish": "https://wotd.transparent.com/rss/swedish-widget.xml",
    "Turkish": "https://wotd.transparent.com/rss/turkish-widget.xml",
    "Urdu": "https://wotd.transparent.com/rss/urdu-widget.xml"
}

# load environmental variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# bot framework initialization
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ==========================================
# CORE BACKING LOOPS
# ==========================================

@tasks.loop(time=SCHEDULE)
async def get_wotd() -> None:
    """Processes RSS feeds, downloads audio components, and posts the Word of the Day."""
    config = get_config()
    if not config.get("wotd"): 
        return
        
    log("Getting words of the day")
    
    for language in config["wotd"]:
        if not config["wotd"][language]: 
            continue
            
        try:
            # Offload blocking HTTP calls to avoid locking up core execution
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: requests.get(MAPPING[language], headers=CUSTOM_HEADERS))
            soup = bs(response.text, "html.parser")
            wotd = xmltodict.parse(soup.find("words").prettify())["words"]

            word_file_path = f"./word_{language}.mp3"
            phrase_file_path = f"./phrase_{language}.mp3"

            # Async execution for core sound files
            w_res = await loop.run_in_executor(None, lambda: requests.get(wotd["wordsound"], headers=CUSTOM_HEADERS))
            if w_res.status_code == 200:
                with open(word_file_path, "wb") as file:
                    file.write(w_res.content)
            else:
                word_file_path = None
                log(f"Failed downloading word sound for {language}. Status: {w_res.status_code}")

            p_res = await loop.run_in_executor(None, lambda: requests.get(wotd["phrasesound"], headers=CUSTOM_HEADERS))
            if p_res.status_code == 200:
                with open(phrase_file_path, "wb") as file:
                    file.write(p_res.content)
            else:
                phrase_file_path = None
                log(f"Failed downloading phrase sound for {language}. Status: {p_res.status_code}")

            # Construct clean embed payload data
            description_parts = [f"# {wotd['word']}"]
            if wotd.get("wotd:transliteratedword"):
                description_parts.append(f"*{wotd['wotd:transliteratedword']}*")
            description_parts.extend([
                f"> Part of Speech: {wotd['wordtype']}",
                f"> Meaning: {wotd['translation']}\n",
                "### Example Usage",
                f"# {wotd['fnphrase']}"
            ])
            if wotd.get("wotd:transliteratedsentence"):
                description_parts.append(f"*{wotd['wotd:transliteratedsentence']}*")
            description_parts.append(f"> {wotd['enphrase']}\n")
            description = "\n".join(description_parts)

            embed = discord.Embed(
                title=f"{language} Word of the Day",
                description=description,
                color=discord.Color.gold()
            )
            embed.set_author(name=f"[{wotd['date']}]")

            # Route messages out to registered guild configurations
            for channel_id in config["wotd"][language]:
                channel = bot.get_channel(int(channel_id))
                if not channel:
                    try:
                        channel = await bot.fetch_channel(int(channel_id))
                    except Exception:
                        print(f"Could not locate channel ID {channel_id}")
                        continue

                try:
                    attachments = []
                    if word_file_path and os.path.exists(word_file_path):
                        attachments.append(discord.File(word_file_path, filename=f"{language.lower()}_word_of_the_day.mp3"))
                    if phrase_file_path and os.path.exists(phrase_file_path):
                        attachments.append(discord.File(phrase_file_path, filename=f"{language.lower()}_example_phrase.mp3"))
                    await channel.send(embed=embed, files=attachments)
                except Exception as e:
                    print(f"Error sending {language} to channel {channel_id}: {e}")

            # Post clean-up logic executed per iteration
            if word_file_path and os.path.exists(word_file_path):
                os.remove(word_file_path)
            if phrase_file_path and os.path.exists(phrase_file_path):
                os.remove(phrase_file_path)

        except Exception as loop_error:
            print(f"Skipping language {language} due to processing error: {loop_error}")

# ==========================================
# TIME RECONFIGURATION COMMANDS
# ==========================================

@bot.tree.command(name="set_post_time", description="Set the time at which the bot post the Word(s) of the Day")
@app_commands.describe(time_input="When should the bot post? (e.g., '3:30 PM', '21:00', 'midnight')")
async def set_post_time(interaction: discord.Interaction, time_input: str):
    parsed_datetime = dateparser.parse(time_input)
    if parsed_datetime is None:
        embed = discord.Embed(
            title="Error", 
            description="Could not figure out what time you meant. Try something like `3:30 PM` or `18:45`.", 
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
        
    parsed_time = parsed_datetime.time()
    
    config = get_config()
    config["settings"]["post-time"] = str(parsed_time)
    save_config(config)
    
    try:
        local_tz = ZoneInfo(tzlocal.get_localzone_name())
        loop_time = parsed_time.replace(tzinfo=local_tz)
        
        get_wotd.change_interval(time=loop_time)
        if get_wotd.is_running():
            get_wotd.restart()
            
        log(f"Successfully adjusted background loop interval to {loop_time}")
    except Exception as e:
        log(f"Failed to dynamically adjust loop time: {e}")
        
    embed = discord.Embed(
        title="Success", 
        description=f"Word(s) of the Day will be posted daily at **{parsed_time.strftime('%I:%M %p')}**", 
        color=discord.Color.green()
    )
    return await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# PERSISTENT STORAGE CORE HELPERS
# ==========================================

def log(text: str) -> None:
    print(f"[{datetime.datetime.now()}] {text}")

def get_config() -> dict:
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def has_permission(interaction: discord.Interaction, channel: discord.abc.GuildChannel) -> bool:
    perms = channel.permissions_for(interaction.guild.me)
    if not (perms.send_messages and perms.embed_links and perms.view_channel):
        await interaction.response.send_message(
            f"Error: Do not have permission to post in {channel.mention}", 
            ephemeral=True
        )
        return False
    return True

def get_versions() -> tuple[str | None, str | None]:
    """Interrogates Git and the GitHub api tracking branch divergences."""
    try:
        local_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except Exception as e:
        log(f"Error getting local hash: {e}")
        local_hash = None

    try:
        response = requests.get(
            url="https://api.github.com/repos/dadams05/Rudeus/git/ref/heads/main", 
            headers=CUSTOM_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        remote_hash = response.json()["object"]["sha"]
    except Exception as e:
        log(f"Error getting remote hash: {e}")
        remote_hash = None
    
    return local_hash, remote_hash

def merge_defaults(default: dict, user_config: dict) -> tuple[dict, bool]:
    """Recursively resolves downstream key updates without disrupting customized configurations."""
    has_changes = False
    
    for key, value in default.items():
        if key not in user_config:
            user_config[key] = value
            has_changes = True
        elif isinstance(value, dict) and isinstance(user_config[key], dict):
            deep_config, deep_changes = merge_defaults(value, user_config[key])
            if deep_changes:
                user_config[key] = deep_config
                has_changes = True
                
    return user_config, has_changes

# ==========================================
# SYSTEM AUTOMATION UPDATE ENDPOINTS
# ==========================================

@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZoneInfo(tzlocal.get_localzone_name())))
async def auto_update() -> None:
    log("Checking for updates.")
    local, remote = get_versions()
    if not local or not remote:
        return

    try:
        if local != remote and get_config()["settings"]["auto-update"]:
            log("New version of bot. Downloading update and restarting.")
            subprocess.Popen(["./updater.sh", str(os.getpid())])
            await bot.close()
    except Exception as e:
        log(f"Error auto updating: {e}")

@bot.tree.command(name="check_for_update", description="Check for an update and install it if available")
async def check_for_update(interaction: discord.Interaction):
    # Defer interaction payload parsing so external git operations don't trigger command failure status
    await interaction.response.defer(ephemeral=True)
    
    local, remote = get_versions()
    if not local or not remote:
        embed = discord.Embed(
            title="Update Error",
            description="Unable to reach local git repository or remote version control tracking data.",
            color=discord.Color.red()
        )
        return await interaction.followup.send(embed=embed, ephemeral=True)

    try:
        if local != remote:
            embed = discord.Embed(
                title="New Update Available",
                description="Updating now. Please wait a moment before trying any more commands.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            log("New version of bot. Downloading update and restarting.")
            subprocess.Popen(["./updater.sh", str(os.getpid())])
            await bot.close()
        else:
            embed = discord.Embed(
                title="Up To Date",
                description=f"Current Version: {VERSION}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        log(f"Error updating: {e}")

@bot.tree.command(name="set_auto_update", description="Turn auto-updating on/off")
@app_commands.describe(value="on/off")
async def set_auto_update(interaction: discord.Interaction, value: Literal["on", "off"]):
    config = get_config()
    config["settings"]["auto-update"] = True if value == "on" else False
    save_config(config)
    
    embed = discord.Embed(
        title="Success",
        description=f"Auto-updating has been turned {value}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# SERVER GUILD CHANNEL ASSIGNMENTS
# ==========================================

@bot.tree.command(name="add_wotd", description="Add a Word of the Day to a channel")
@app_commands.describe(channel="The channel to post updates to", language="The language to assign")
async def add_wotd(interaction: discord.Interaction, channel: discord.TextChannel | discord.VoiceChannel, language: str):
    if language not in MAPPING:
        embed = discord.Embed(title="Error", description="Invalid language selection", color=discord.Color.red())
        return await interaction.response.send_message(embed=embed, ephemeral=True)
        
    if not await has_permission(interaction, channel): 
        return
        
    channel_id = str(channel.id)
    config = get_config()
    if language not in config["wotd"]:
        config["wotd"][language] = []
    if channel_id not in config["wotd"][language]:
        config["wotd"][language].append(channel_id)
    save_config(config)
    
    embed = discord.Embed(
        title="Success",
        description=f"{channel.mention} will now post the **{language}** Word of the Day.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@add_wotd.autocomplete("language")
async def add_wotd_autocomplete(interaction: discord.Interaction, current: str):
    return [
        discord.app_commands.Choice(name=lang, value=lang)
        for lang in MAPPING.keys() if current.lower() in lang.lower()
    ][:25]

@bot.tree.command(name="remove_wotd", description="Remove a Word of the Day from a channel")
@app_commands.describe(channel="The channel to remove the language from", language="The language to remove")
async def remove_wotd(interaction: discord.Interaction, channel: discord.TextChannel | discord.VoiceChannel, language: str):
    channel_id = str(channel.id)
    config = get_config()
    
    if language not in config["wotd"] or channel_id not in config["wotd"][language]:
        embed = discord.Embed(
            title="Not Found",
            description=f"{channel.mention} does not post a(n) **{language}** Word of the Day",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
        
    if not await has_permission(interaction, channel): 
        return
        
    config["wotd"][language].remove(channel_id)
    if not config["wotd"][language]:
        config["wotd"].pop(language)
    save_config(config)
    
    embed = discord.Embed(
        title="Success",
        description=f"{channel.mention} will no longer post the **{language}** Word of the Day.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@remove_wotd.autocomplete("language")
async def remove_wotd_autocomplete(interaction: discord.Interaction, current: str):
    config = get_config()
    active_languages = list(config.get("wotd", {}).keys()) 
    return [
        discord.app_commands.Choice(name=lang, value=lang)
        for lang in active_languages if current.lower() in lang.lower()
    ][:25]

# ==========================================
# DIAGNOSTIC SYSTEM INFRASTRUCTURE COMMANDS
# ==========================================

@bot.tree.command(name="show_config", description="List the current languages/channels configuration")
async def show_config(interaction: discord.Interaction):
    config = get_config()
    output = ""
    
    for language, channels in config["wotd"].items():
        channel_list = []
        for channel_id in channels:
            channel = bot.get_channel(int(channel_id))
            channel_list.append(f"• {channel.mention}" if channel else f"• #deleted-channel ({channel_id})")
        output += f"**{language}** WOTD posted in:\n{'\n'.join(channel_list)}\n\n"
    
    if not output:
        output = "No Words of the Day have been configured"

    embed = discord.Embed(
        title="Current Word of The Day Configuration",
        description=output,
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="clear_config", description="Clear current Word of the Day configuration")
async def clear_config(interaction: discord.Interaction):
    config = get_config()
    config["wotd"].clear()
    save_config(config)
    
    embed = discord.Embed(
        title="Success",
        description="Configuration has been cleared/reset. No words will be posted now.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="info", description="Show bot information")
async def info(interaction: discord.Interaction):
    delta = datetime.datetime.now() - START
    total_secs = int(delta.total_seconds())
    hours, remainder = divmod(total_secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    config = get_config()

    description = (
        f"__**Version**__: {VERSION}\n"
        f"__**Uptime**__: {hours}:{minutes:02}:{seconds:02}\n"
        f"__**Autoupdate**__: {config['settings']['auto-update']}\n"
        f"__**Post Time**__: Currently configured to post at {get_wotd.time[0].strftime('%I:%M %p')}\n\n"
        f"Rudeus is a bot that posts words of the day from other languages. You can configure it "
        f"to post words in designated channels and choose which languages are posted. The words are pulled from:\n"
        f"https://www.transparent.com/word-of-the-day."
    )
    
    embed = discord.Embed(
        title="Rudeus",
        description=description,
        color=discord.Color.gold()
    )

    languages = sorted(list(MAPPING.keys()))
    per_col = (len(languages) + 2) // 3
    col1 = "\n".join(f"• {lang}" for lang in languages[:per_col])
    col2 = "\n".join(f"• {lang}" for lang in languages[per_col:per_col*2])
    col3 = "\n".join(f"• {lang}" for lang in languages[per_col*2:])
    
    embed.add_field(name="__Available Languages__", value=col1, inline=True)
    embed.add_field(name="\u200b", value=col2, inline=True)
    embed.add_field(name="\u200b", value=col3, inline=True)
   
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# GATEWAY CLIENT HANDLERS & BOT ENTRY
# ==========================================

@bot.event
async def on_ready():
    """Triggers looping configurations smoothly on basic initialization validation."""
    try:
        await bot.tree.sync()
        if not get_wotd.is_running():
            get_wotd.start()
        if get_config()["settings"]["auto-update"] and not auto_update.is_running():
            auto_update.start()
    except Exception as e:
        log(f"Exception on startup: {e}")

if __name__ == "__main__":
    # Ensure raw user profile storage baseline exists
    try:
        with open(CONFIG_FILE, "r") as f:
            pass
    except FileNotFoundError:
        log("No config found. Creating config.json from default.json.")
        copyfile(DEFAULT_CONFIG_FILE, CONFIG_FILE)

    # Reconcile properties to downstream targets dynamically
    try:
        with open(DEFAULT_CONFIG_FILE, "r") as f:
            default_data = json.load(f)
            
        with open(CONFIG_FILE, "r") as f:
            user_data = json.load(f)
            
        updated_config, changes_detected = merge_defaults(default_data, user_data)
        
        if changes_detected:
            log("Detected new schema updates in default.json. Migrating config.json safely...")
            with open(CONFIG_FILE, "w") as f:
                json.dump(updated_config, f, indent=4)
            log("Migration complete.")
            
    except Exception as e:
        log(f"Critical error checking or migrating configuration files: {e}")

    # Set specific timing objects inside the global system configuration scope
    config = get_config()
    config_time_str = config["settings"].get("post-time") 
    if config_time_str:
        try:
            parsed_time = datetime.time.fromisoformat(config_time_str)
            local_tz = ZoneInfo(tzlocal.get_localzone_name())
            startup_schedule = parsed_time.replace(tzinfo=local_tz)
            
            get_wotd.change_interval(time=startup_schedule)
            log(f"Loaded post-time from config: {startup_schedule}")
        except Exception as e:
            log(f"Error parsing startup config post-time, using default fallback: {e}")

    bot.run(TOKEN)
