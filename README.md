# A simple Discord API wrapper

Create slash commands, and delete user generated text upon matching words in a specific file.
This library is made to be as simple as possible with a 'minimal' amount of dependency.

# Installation

## Unix/macOS

```bash

python3 -m pip install --upgrade build
python3 -m pip install git+https://github.com/MertGM/simplediscord.git

# Development install
git clone https://github.com/MertGM/simplediscord 
cd simplediscord
python3 -m build
python3 -m pip install SimpleDiscord-0.1.3-py3-none-any.whl or SimpleDiscord-0.1.3.tar.gz

```

## Windows

```shell

py -m pip install --upgrade build
py -m pip install git+https://github.com/MertGM/simplediscord.git

# Development install
git clone https://github.com/MertGM/simplediscord
cd simplediscord
py -m build
py -m pip install SimpleDiscord-0.1.3-py3-none-any.whl or SimpleDiscord-0.1.3.tar.gz

```

# Setting up a bot

To create a bot, first create an application at: https://discord.com/developers/applications.
After creating an application go to the Bot section in settings.
1. If you want to filter messages in your server, then tick 'message content intent' on.
2. Go to OAuth > URL Generator in the settings.
3. Enable 'bot' and 'applications.commands' in scopes, set up your permissions according to your needs
or choose 'Administrator' to have everything you can.
4. Copy the generated url at the bottom and paste it in your search bar + enter.

And you're done!

# Examples 

## Greetings

```python

from simplediscord import SimpleDiscord as Discord
import os

# It is recommended to save your api key and token in a safe environment e.g: an environment variable.

token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")

Discord.commands["greetings"] = "Greetings @username"
Discord.commands["bye"] = "Bye @username"
Discord.commands["hi"] = "Hi there @username"
Discord.Connect(token, api, guild)

@Discord.Main
def Bot():
    Discord.Register("hi", "say hi")
    Discord.Register("greetings", "say greetings")
    Discord.Register("bye", "say bye")
    Discord.Slash_commands()

```

## Rock Paper Scissors

```python

from simplediscord import SimpleDiscord as Discord
import os
from random import randint

token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")


def Rpc(user):
    a = ["r", "p", "s"]
    elements = ["Rock", "Paper", "Scissors"]
    n = randint(0, 2)
    bot = a[n]
    bot_pick = elements[n]

    print("bot picked: " + bot)
    print("user picked: " + user)
    if bot == "r" and user[0].lower() == "s":
        print("Bot wins!")
        return f"You picked: {user},\n I picked: {bot_pick},\n I win!"
    elif bot == "p" and user[0].lower() == "r":
        print("Bot wins!")
        return f"You picked: {user},\n I picked: {bot_pick},\n I win!"
    elif bot == "s" and user[0].lower() == "p":
        print("Bot wins!")
        return f"You picked: {user},\n I picked: {bot_pick},\n I win!"
    elif bot == user[0].lower():
        print("Tie!")
        return f"You picked: {user},\n I picked: {bot_pick},\n we tie!"
    else:
        print("User wins!")
        return f"You picked: {user},\n I picked: {bot_pick},\n you win!"

Discord.commands["rpc"] = ["func@value", Rpc]


Discord.Connect(token, api, guild)

print(Discord.commands)

@Discord.Main
def Bot():
    Discord.Register(["rpc", "play", "Rock", "Paper", "Scissors"], ["Rock, Paper, Scissors", "Play Rock, Paper, Scissors"], ["Rock", "Paper", "Scissors"])
    Discord.Slash_commands()

```

## Bad words

```python

import os
from simplediscord import SimpleDiscord as Discord

token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")

# When modifying: make sure the language keyword begins with an uppercase and the words are lowercased.
Discord.Filter("bad_words.txt")
Discord.banned_words_reaction["English"] = "Careful there, mind your language!"
Discord.banned_words_reaction["Turkish"] = "Hoop dedik kardesim, yavas ol!"
Discord.banned_words_reaction["Dutch"] = "Hey hey, geen gescheld!"

Discord.Connect(token, api, guild, ["GUILD_MESSAGES"])

@Discord.Main
def Bot():
    pass

```

## Logger

```python

from simplediscord import SimpleDiscord as Discord
from simplediscord.utils.colors import Color
from simplediscord.utils.mylogger import logging_color

token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")

# The logging level hierarchy is as the following:
#
# Debug
# Info
# Warning
# Fatal
# None
#
# Loggings with the specified level and subsequent will be triggered if set.

Discord.SetLoggerLevel(Discord.LOGGER_DEBUG)

# Enable Virtual Terminal Sequences if you're using cmd or PowerShell.
#from simplediscord.utils.colors import EnableVT
#EnableVT()

# Change the foreground color.
logging_color["fatal_fg"] = Color.red
logging_color["info_fg"] = Color.green
logging_color["warning_fg"] = Color.yellow
logging_color["debug_fg"] = Color.corn_flower_blue

# And background color if you wish.
#logging_color["fatal_bg"] = Color.blue
#logging_color["info_bg"] = Color.purple
#logging_color["warning_bg"] = Color.magenta
#logging_color["debug_bg"] = Color.black

# For more colors see the colors.py file, to see the currently supported colors.


Discord.Connect(token, api, guild, ["GUILD_MESSAGES"])

@Discord.Main
def Bot():
    pass

```

# TODOs

* Unit tests
* Send compressed data to Discord's server
