# A simple Discord API wrapper

Create slash commands with and without parameters, and delete user generated text which contain words specified in a file from the server.
This library is made to be as simple as possible with minimal external libraries used.

# Installation

## Unix/macOS

```bash

python3 -m pip install --upgrade build
python3 -m pip install git+https://github.com/MertGM/SimpleDiscord.git --upgrade

# Development install 
git clone https://github.com/MertGM/SimpleDiscord.git
cd SimpleDiscord
python3 -m build
python3 -m pip install dist/SimpleDiscord-version.wz or tar

```

## Windows

```shell

py -m pip install --upgrade build
py -m pip install git+https://github.com/MertGM/SimpleDiscord.git --upgrade

# Development install 
git clone https://github.com/MertGM/SimpleDiscord.git
cd SimpleDiscord
py -m build
py -m pip install dist/SimpleDiscord-version.wz or tar

```

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
    Discord.Register("hi", "say hi", "hi")
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

bad_words = {}

# Create file or specify a dict containing exactly as so:
# First letter uppercase is identified as language.
# lower case words are the comparison words.

with open("bad_words.txt", "r", encoding="utf-8") as f:
    lang = None
    for line in f:
        if line[0].isupper():
            lang = line.strip()
        elif lang is not None and line != "\n":
            if lang not in bad_words:
                bad_words[lang] = [line.strip()]
            else:
                bad_words[lang].append(line.strip())
            
print(bad_words)
Discord.banned_words = bad_words
Discord.banned_words_reaction["English"] = "Careful there, mind your language!"
Discord.banned_words_reaction["Turkish"] = "Hoop dedik kardesim, yavas ol!"
Discord.banned_words_reaction["Dutch"] = "Hey hey, geen gescheld!"

Discord.Connect(token, api, guild, ["GUILD_MESSAGES"])

```

# TODOs

* Unit tests
* Logging enabled when program is envoked for developing
* Send compressed data to Discord's server
* Format complex data structures nicely (e.g dict arrays) in logging library
