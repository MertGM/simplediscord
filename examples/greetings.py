# TODO: Package SimpleDiscord module to import it regardless of location.
# As of now the module needs to be inside the same folder of the corresponding script.

import SimpleDiscord as Discord
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
