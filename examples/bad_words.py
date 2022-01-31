# TODO: Package SimpleDiscord module to import it regardless of location.
# As of now the module needs to be inside the same folder of the corresponding script.

import os
import SimpleDiscord as Discord

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
