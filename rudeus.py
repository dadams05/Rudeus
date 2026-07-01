import os
import json
import discord
import tzlocal
import datetime
import requests
import xmltodict
import subprocess
from shutil import copyfile
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discord import app_commands
from bs4 import BeautifulSoup as bs
from discord.ext import commands, tasks 


VERSION = "v1.0.0"
CONFIG_FILE = "config.json"
DEFAULT_CONFIG_FILE = "default.json"
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

# load in custom environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# set up the discord bot object
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

#############################################################################################
# get the word of the day
#############################################################################################

@tasks.loop(time=SCHEDULE)
async def get_wotd():
    print("Getting words of the day...")
    # get config, return if empty
    config = get_config()
    if not config.get("wotd"):
        return
    # start going through languages
    for language in config["wotd"]:
        # skip language if no channels post it
        if not config["wotd"][language]: continue
        try:
            # get the data
            response = requests.get(MAPPING[language], headers=CUSTOM_HEADERS)
            soup = bs(response.text, "html.parser")
            wotd = xmltodict.parse(soup.find("words").prettify())["words"]
            # create the audio file names
            word_file_path = f"./word_{language}.mp3"
            phrase_file_path = f"./phrase_{language}.mp3"
            # download word audio file
            w_res = requests.get(wotd["wordsound"], headers=CUSTOM_HEADERS)
            if w_res.status_code == 200:
                with open(word_file_path, "wb") as file:
                    file.write(w_res.content)
            else:
                word_file_path = None
                print(f"Failed downloading word sound for {language}. Status: {w_res.status_code}")
            # download phrase audio file
            p_res = requests.get(wotd["phrasesound"], headers=CUSTOM_HEADERS)
            if p_res.status_code == 200:
                with open(phrase_file_path, "wb") as file:
                    file.write(p_res.content)
            else:
                phrase_file_path = None
                print(f"Failed downloading phrase sound for {language}. Status: {p_res.status_code}")
            # set up the description
            description = ""
            if wotd["wotd:transliteratedword"] and wotd["wotd:transliteratedsentence"]:
                description = f"# {wotd["word"]}\n" \
                              f"*{wotd["wotd:transliteratedword"]}*\n" \
                              f"> Part of Speech: {wotd["wordtype"]}\n" \
                              f"> Meaning: {wotd["translation"]}\n\n" \
                              f"### Example Usage\n" \
                              f"# {wotd["fnphrase"]}\n" \
                              f"*{wotd["wotd:transliteratedsentence"]}*\n "\
                              f"> {wotd["enphrase"]}\n"
            else:
                description = f"# {wotd["word"]}\n" \
                              f"> Part of Speech: {wotd["wordtype"]}\n" \
                              f"> Meaning: {wotd["translation"]}\n\n" \
                              f"### Example Usage\n" \
                              f"# {wotd["fnphrase"]}\n" \
                              f"> {wotd["enphrase"]}\n" 
            # build the embed
            embed = discord.Embed(
                title=f"{language} Word of the Day",
                description=description,
                color=discord.Color.yellow()
            )
            embed.set_author(name=f"[{wotd["date"]}]")
            # send the embed to the corresponding channels
            for channel_id in config["wotd"][language]:
                # memory cache check first, fall back to API fetch if memory is empty
                channel = bot.get_channel(int(channel_id))
                if not channel:
                    try:
                        channel = await bot.fetch_channel(int(channel_id))
                    except Exception:
                        print(f"Could not locate channel ID {channel_id}")
                        continue
                try:
                    # append attachments only if files exist
                    attachments = []
                    if word_file_path and os.path.exists(word_file_path):
                        attachments.append(discord.File(word_file_path, filename=f"{language}_word_of_the_day.mp3"))
                    if phrase_file_path and os.path.exists(phrase_file_path):
                        attachments.append(discord.File(phrase_file_path, filename=f"{language}_example_phrase.mp3"))

                    await channel.send(embed=embed, files=attachments)
                except Exception as e:
                    print(f"Error sending {language} to channel {channel_id}: {e}")

            # clean up audio files inside the loop so they are wiped immediately after use
            if word_file_path and os.path.exists(word_file_path):
                os.remove(word_file_path)
            if phrase_file_path and os.path.exists(phrase_file_path):
                os.remove(phrase_file_path)

        except Exception as loop_error:
            print(f"Skipping language {language} due to processing error: {loop_error}")

#############################################################################################
# helper functions
#############################################################################################

def log(text: str) -> None:
    print(f"[{datetime.datetime.now()}] {text}")

def get_config() -> dict:
    return json.load(open(CONFIG_FILE, "r"))

def save_config(data: str) -> None:
    json.dump(data, open(CONFIG_FILE, "w"), indent=4)

async def has_permission(interaction: discord.Interaction, channel: discord.abc.GuildChannel) -> bool:
    perms = channel.permissions_for(interaction.guild.me)
    if not (perms.send_messages and perms.embed_links and perms.view_channel):
        await interaction.response.send_message(
            f"Error: Do not have permission to post in {channel.mention}", 
            ephemeral=True
        )
        return False
    return True

#############################################################################################
# updating
#############################################################################################

@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZoneInfo(tzlocal.get_localzone_name())))
async def auto_update() -> None:
    """Pull any updates from Github"""
    log("Checking for updates.")

    # get local HEAD hash
    try:
        local_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except Exception as e:
        log(f"Error getting local hash: {e}")
        return

    # get remote HEAD hash
    try:
        response = requests.get(
            url="https://api.github.com/repos/dadams05/Rudeus/git/ref/heads/main", 
            headers=CUSTOM_HEADERS,
            timeout=10,
        )
        response.raise_for_status() # raise error if request failed
        remote_hash = response.json()["object"]["sha"]
    except Exception as e:
        log(f"Error getting remote hash: {e}")
        return
    
    # call the updater.sh script
    try:
        if local_hash != remote_hash and get_config()["settings"]["auto-update"]:
            log("New version of bot. Downloading update and restarting.")
            subprocess.Popen(["./updater.sh", str(os.getpid())])
    except Exception as e:
        log(f"Error calling updater.sh: {e}")
        return

@bot.tree.command(name="check_for_update", description="Check for an update and install it if available")
async def check_for_update(interaction: discord.Interaction):
    # get local HEAD hash
    try:
        local_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except Exception as e:
        log(f"Error getting local hash: {e}")
        return

    # get remote HEAD hash
    try:
        response = requests.get(
            url="https://api.github.com/repos/dadams05/Rudeus/git/ref/heads/main", 
            headers=CUSTOM_HEADERS,
            timeout=10,
        )
        response.raise_for_status() # raise error if request failed
        remote_hash = response.json()["object"]["sha"]
    except Exception as e:
        log(f"Error getting remote hash: {e}")
        return
    
    # call the updater.sh script
    if local_hash != remote_hash and get_config()["settings"]["auto-update"]:
        embed = discord.Embed(
            title="New Update Available",
            description=f"Updating now. Please wait a moment before trying any more commands.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        log("New version of bot. Downloading update and restarting.")
        subprocess.Popen(["./updater.sh", str(os.getpid())])
    else:
        embed = discord.Embed(
            title="Up To Date",
            description=f"Current Version: {VERSION}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

#############################################################################################
# add/remove wotd
#############################################################################################

@bot.tree.command(name="add_wotd", description="Add a Word of the Day to a channel")
@app_commands.describe(channel="The channel to post updates to", language="The language to assign")
async def add_wotd(interaction: discord.Interaction, channel: discord.TextChannel | discord.VoiceChannel, language: str):
    # make sure given language is valid
    if language not in MAPPING:
        embed = discord.Embed(title="Error", description="Invalid language selection", color=discord.Color.red())
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    # check for channel perms
    if not await has_permission(interaction, channel): 
        return
    # add the language into the config
    channel_id = str(channel.id)
    config = get_config()
    if language not in config["wotd"]:
        config["wotd"][language] = []
    if channel_id not in config["wotd"][language]:
        config["wotd"][language].append(channel_id)
    save_config(config)
    # send the success message
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
    
    # check if the language is actually even posted
    if language not in config["wotd"] or channel_id not in config["wotd"][language]:
        embed = discord.Embed(
            title="Not Found",
            description=f"{channel.mention} does not post a(n) **{language}** Word of the Day",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    # check perms
    if not await has_permission(interaction, channel): 
        return
    # remove the language from the config
    config["wotd"][language].remove(channel_id)
    if not config["wotd"][language]:
        config["wotd"].pop(language)
    save_config(config)
    # send the success message
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

#############################################################################################
# config
#############################################################################################

@bot.tree.command(name="list_config", description="List the current languages/channels configuration")
async def list_config(interaction: discord.Interaction):
    config = get_config()

    output = ""
    for language in config["wotd"]:
        output += f"{language} WOTD posted in:\n" + "\n".join([f"• {bot.get_channel(int(channel)).mention}" for channel in config["wotd"][language]]) + "\n\n"
    
    embed = discord.Embed(
        title="Current Word of The Day Configuration",
        description=output,
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


#############################################################################################
# main functions
#############################################################################################

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        if not get_wotd.is_running():
            get_wotd.start()
        if get_config()["settings"]["auto-update"] and not auto_update.is_running():
            auto_update.start()
    except Exception as e:
        log(f"Exception on startup: {e}")

if __name__ == "__main__":
    # create a config if there isnt one
    try:
        file = open(CONFIG_FILE, "r")
    except Exception:
        copyfile(DEFAULT_CONFIG_FILE, CONFIG_FILE)
    # start the bot
    bot.run(TOKEN)
