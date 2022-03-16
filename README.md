# A simple Discord API wrapper

Create slash commands with and without parameters, and delete user generated text that contain specified words.
This library is made to be as simple as possible with minimal external libraries used.

# Installation

## Unix/macOS

```bash

python3 -m pip install --upgrade build
python3 -m pip install git+https://github.com/MertGM/simplediscord.git

# Development install
git clone https://github.com/MertGM/simplediscord 
cd simplediscord
python3 -m build
python3 -m pip install dist/SimpleDiscord-version.wz or tar

```

## Windows

```shell

py -m pip install --upgrade build
py -m pip install git+https://github.com/MertGM/simplediscord.git

# Development install
git clone https://github.com/MertGM/simplediscord
cd simplediscord
py -m build
py -m pip install dist/SimpleDiscord-version.wz or tar

```

# Setting up a bot

To create a bot you need to go to the discord's application page at: https://discord.com/developers/applications.
After creating an application go to the Bot section in settings.
1. If you want to filter messages in your server, then tick 'message content intent' on.
2. Go to OAuth > URL Generator in the settings.
3. Enable 'bot' and 'applications.commands' in scopes, set up your permissions according to your needs,
or choose 'Administrator' to have everything you can.
4. Copy the generated url at the bottom and paste it in your search bar + enter.

And you're done!

# Examples 

## Greetings

```python

from simplediscord import SimpleDiscord as Discord
import os

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

## Rock, Paper, Scissors

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

# When modifying: make sure the language keyword begins with an uppercase and the words are all lowercased.
Discord.Filter("bad_words.txt")
Discord.banned_words_reaction["English"] = "Careful there, mind your language!"
Discord.banned_words_reaction["Turkish"] = "Hoop dedik kardesim, yavas ol!"
Discord.banned_words_reaction["Dutch"] = "Hey hey, geen gescheld!"

Discord.Connect(token, api, guild, ["GUILD_MESSAGES"])

@Discord.Main
def Bot():
    pass

```

# TODOs

* Unit tests
* Send compressed data to Discord's server
* Format complex data structures nicely (e.g dict arrays) in logging library
