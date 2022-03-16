from simplediscord import SimpleDiscord as Discord
import os

token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")

Discord.commands["greetings"] = "Greetings @username"
Discord.commands["bye"] = "Bye @username"
Discord.commands["hi"] = "Hi there @username"
Discord.Connect(token, api, guild)

Discord.Set_logger_level(Discord.LOGGER_DEBUG)

@Discord.Main
def Bot():
    Discord.Register("hi", "say hi")
    Discord.Register("greetings", "say greetings")
    Discord.Register("bye", "say bye")
    Discord.Slash_commands()
