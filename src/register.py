import io
import json
import urllib3
import os

http = urllib3.PoolManager()
token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")
def Register(url="https://discord.com/api/v9/applications/{app}/guilds/{guild}/commands".format(app=api,guild=guild)):
    headers = {
            "Authorization": token,
            "Content-Type": "application/json"
    }
    data = {
            "name": "greetings",
            "type": 1,
            "description": "Send your greetings",
            "value": "hi there"
    }
    data_encoded = json.dumps(data)
    resp = http.request(
            "POST",
            url,
            headers=headers,
            body=data_encoded)

    resp.auto_close = False
    print(resp.data)
    if resp.status == 200:
        print(resp.status)
        for line in io.TextIOWrapper(resp):
            print(line)
        print()
        for k,v in resp.headers.items():
            print(f"{k}: {v}")

    else:
        print(resp.status)
        for line in io.TextIOWrapper(resp):
            print(line)
        print()
        for k,v in resp.headers.items():
            print(f"{k}: {v}")

def Commands(url):
    headers = {
            "Authorization": token,
            "Content-Type": "application/json"
    }

    resp = http.request(
            "GET",
            url,
            headers=headers)

    resp.auto_close = False
    print("Bot commands:")
    for k,v in json.loads(resp.data)[0].items():
        print(f"{k}: {v}")
    if resp.status == 200:
        print(resp.status)
        print()
        for k,v in resp.headers.items():
            print(f"{k}: {v}")

    else:
        print(resp.status)
        for line in io.TextIOWrapper(resp):
            print(line)
        print()
        for k,v in resp.headers.items():
            print(f"{k}: {v}")
if __name__ == "__main__":
    #Register("https://discord.com/api/v9/applications/{app}/guilds/{guild}/commands".format(app=api,guild=guild))
    Commands("https://discord.com/api/v9/applications/{app}/guilds/{guild}/commands".format(app=api,guild=guild))
