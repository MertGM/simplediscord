import SimpleDiscord as Discord
import os
from random import randint

token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")

Discord.commands["greetings"] = "Greetings @username"
Discord.commands["bye"] = "Bye @username"
Discord.commands["hi"] = "Hi there @username"

def Rpc(user):
    a = ["r", "p", "s"]
    elements = ["Rock", "Paper", "Scissors"]
    n = randint(0, 2)
    bot = a[n]
    bot_pick = elements[n]

    if bot == "r" and user[0].lower() == "s":
        return f"You picked: {user},\n I picked: {bot_pick},\n I win!"
    elif bot == "p" and user[0].lower() == "r":
        return f"You picked: {user},\n I picked: {bot_pick},\n I win!"
    elif bot == "s" and user[0].lower() == "p":
        return f"You picked: {user},\n I picked: {bot_pick},\n I win!"
    elif bot == user[0].lower():
        return f"You picked: {user},\n I picked: {bot_pick},\n we tie!"
    else:
        return f"You picked: {user},\n I picked: {bot_pick},\n you win!"

Discord.commands["rpc"] = ["func@value", Rpc]

bad_words = {}
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
            
#print(bad_words)
Discord.banned_words = bad_words
Discord.banned_words_reaction["English"] = "Careful there, mind your language!"
Discord.banned_words_reaction["Turkish"] = "Hoop dedik kardesim, yavas ol!"
Discord.banned_words_reaction["Dutch"] = "Hey hey, geen gescheld!"

Discord.Connect(token, api, guild, ["GUILDS", "GUILD_MEMBERS", "GUILD_BANS", "GUILD_MESSAGES"])


#print(Discord.commands)
@Discord.Main
def Bot():
    pass
    #Discord.Register(["rpc", "play", "Rock", "Paper", "Scissors"], ["Rock, Paper, Scissors", "Play Rock, Paper, Scissors"], ["Rock", "Paper", "Scissors"])
    #Discord.Slash_commands()
