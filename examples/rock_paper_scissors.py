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
Discord.Connect(token, api, guild)

print(Discord.commands)
@Discord.Main
def Bot():
    Discord.Register(["rpc", "play", "Rock", "Paper", "Scissors"], ["Rock, Paper, Scissors", "Play Rock, Paper, Scissors"], ["Rock", "Paper", "Scissors"])
    Discord.Slash_commands()
