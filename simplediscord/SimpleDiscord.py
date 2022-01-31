import os
import json
import urllib3
from threading import Thread
import signal
import websocket
import time
#import zlib
from enum  import IntEnum
from dataclasses import dataclass
#import io
import re


# Discord opcodes
class Op_Code(IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    UPDATE_CLIENT_PRESENCE = 3
    VOICE_STATE_UPDATE = 4
    RESUME_SESSION = 6
    RECONNECT = 7
    GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

# Discord close events
# Discord closes connection or sends invalid codes.
class Close_Event(IntEnum):
    UNKNOWN               = 4000
    UNKNOWN_OPCODE        = 4001
    DECODE_ERROR          = 4002
    NOT_AUTHENTICATED     = 4003
    AUTHENTICATION_FAILED = 4004
    ALREADY_AUTHENTICATED = 4005
    INVALID_SEQ           = 4007
    RATE_LIMITED          = 4008
    SESSION_TIMED_OUT     = 4009
    INVALID_SHARD         = 4010
    SHARDING_REQUIRED     = 4011
    INVALID_API_VERSION   = 4012
    INVALID_INTENTS       = 4013
    DISALLOWED_INTENTS    = 4014


Intents_Token = {
    "GUILDS"                    : 1,
    "GUILD_MEMBERS"             : 2,
    "GUILD_BANS"                : 4,
    "GUILD_EMOJIS_AND_STICKERS" : 8,
    "GUILD_INTEGRATIONS"        : 16,
    "GUILD_WEBHOOKS"            : 32,
    "GUILD_INVITES"             : 64,
    "GUILD_VOICE_STATES"        : 128,
    "GUILD_PRESENCES"           : 256,
    "GUILD_MESSAGES"            : 512,
    "GUILD_MESSAGE_REACTIONS"   : 1024,
    "GUILD_MESSAGE_TYPING"      : 2048,
    "DIRECT_MESSAGES"           : 4096,
    "DIRECT_MESSAGE_REACTIONS"  : 8192,
    "DIRECT_MESSAGE_TYPING"     : 16384,
    "GUILD_SCHEDULED_EVENTS"    : 32768
    }

_http = urllib3.PoolManager()

# Defined by the user
_token = None
_guild = None
_api = None


@dataclass
class Connection:
    ws = None
    wss = None
    interval = None
    identified = False

_loop_heartbeat = True
_ack_heartbeat = None


commands = {}
intents_flag = 0

bot_name = None

banned_words = None
banned_words_reaction = {}


def _Interrupt(signal, frame):
    _loop_heartbeat = False
    data = {"op": 1000}
    Connection.ws.send(json.dumps(data))
    Connection.ws.close()
    os._exit(0)


def _Resume(seq):
    # ws.run_forever() already tries to reconnect if a connection was closed,
    # so all we need is to send to the discord server is that we want to resume.
    data = {
            "op": int(Op_Code.RESUME_SESSION),
            "d": {
                "token": _token,
                "session_id": Connection.session_id,
                "seq": seq
            }
        }
    Connection.ws.send(json.loads(data))


def _Reconnect():
    # Close connection with a non-zero status code.
    Connection.ws.close(status=1001)
    Connection.ws = None
    Connection.interval = None
    Connection.identified = False
    global _loop_heartbeat 
    global _ack_heartbeat
    _loop_heartbeat = False
    _ack_heartbeat = None
    _Connect()


def _RequestHTTP(method, url, data=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": _token
    }
    #print("request called")

    if data is not None:
        #print(f"data not None")
        data_encoded = json.dumps(data)
        #print(f"data encoded {data}")
        resp = _http.request(
                method,
                url,
                headers=headers,
                body=data_encoded)
        return resp
    else:
        resp = _http.request(
                method,
                url,
                headers=headers)
        return resp


def Register(name, description, message=None, command_type=1, url=None):
    #print(url)
    if url == None:
        url = f"https://discord.com/api/v9/applications/{_api}/guilds/{_guild}/commands"

    headers = {
            "Authorization": _token,
            "Content-Type": "application/json"
    }

    # Command with options and choices.
    if type(description) == list:
        data = {
                "name": name[0],
                "type": command_type,
                "description": description[0]
        }

        name_index = 1
        p = data
        # Construct options structure.
        # Only support 1 options structure for now.
        for i in range(1, len(description)):
            p["options"] = [{
                    "name": name[i],
                    "type": 3, # String
                    "description": description[i],
                    "required": True
            }]

            data = p
            #p = p["options"]
            name_index += 1
        data["options"][0]["choices"] = []
        #print(f"{data=}")
        j = 0
        for i in range(name_index, len(name)):
            data["options"][0]["choices"].append({})
            data["options"][0]["choices"][j]["name"] = name[i]
            data["options"][0]["choices"][j]["value"] = message[j]
            j += 1

        #print(f"{data=}")

    # Standard slash command.
    else:
        data = {
                "name": name,
                "type": command_type,
                "description": description
        }
    data_encoded = json.dumps(data)
    resp = _http.request(
            "POST",
            url,
            headers=headers,
            body=data_encoded)

    resp.auto_close = False
    if resp.status == 200 or resp.status == 201:
        print(f"Successfully Registered bot command: {name}")
        #print(resp.data)
        #for line in io.TextIOWrapper(resp):
        #    print(line)
        #for k,v in resp.headers.items():
        #    print(f"{k}: {v}")

    else:
        print(resp.status, resp.reason)
        #for line in io.TextIOWrapper(resp):
        #    print(line)
        #print()
        #for k,v in resp.headers.items():
        #    print(f"{k}: {v}")


def Slash_commands(url=None):
    if url == None:
        url = f"https://discord.com/api/v9/applications/{_api}/guilds/{_guild}/commands"

    headers = {
            "Authorization": _token,
            "Content-Type": "application/json"
    }

    resp = _http.request(
            "GET",
            url,
            headers=headers)

    resp.auto_close = False
    if resp.status == 200 or resp.status == 304:
        print("Registered bot commands:")
        print(resp.data)
        #print()
        #for k,v in resp.headers.items():
        #    print(f"{k}: {v}")

    else:
        print(resp.status, resp.reason)
        #for line in io.TextIOWrapper(resp):
        #    print(line)
        #print()
        #for k,v in resp.headers.items():
        #    print(f"{k}: {v}")


def _Event_handler(ws, op_code, seq, message):
    global _ack_heartbeat
    if op_code == Op_Code.HEARTBEAT:
        #print("Send heartbeat")
        data = {
                "op": int(Op_Code.HEARTBEAT),
                "d": seq
            }
        ws.send(json.dumps(data))

    elif op_code == Op_Code.HEARTBEAT_ACK:
        #print("ACK heartbeat")
        _ack_heartbeat = True
    elif op_code == Op_Code.DISPATCH:
        pass
        #print("Message dispatched")
    elif op_code == Op_Code.RECONNECT:
        _Reconnect()
    elif op_code == Op_Code.INVALID_SESSION:
        # Discord sends this op code if it's down, so according to the docs I should continue to heartbeat.
        # This could be ambiguous and thus behave incorrectly.
        print("Discord is down, waiting untill it's up...")
        _ack_heartbeat = True
    elif op_code == Op_Code.HELLO:
        #print("Got a hello request")
        def Send_heartbeat(ws, _loop_heartbeat):
            while _loop_heartbeat is True:
                global _ack_heartbeat
                if _ack_heartbeat is None or _ack_heartbeat is True:
                    # Only check for ack of heartbeat if connection is established which includes sending a heartbeat once.
                    if _ack_heartbeat is True:
                        _ack_heartbeat = False
                    #print("Send heartbeat interval")
                    data = {
                            "op": int(Op_Code.HEARTBEAT),
                            "d": seq
                        }

                    # Wait based on the interval before requesting to discord api
                    time.sleep(Connection.interval)
                    ws.send(json.dumps(data))

                # Zombied or failed connection.
                else:
                    _Reconnect()

        Thread(target=Send_heartbeat, args=(ws, _loop_heartbeat)).start()



    # Error messages according to Discord's api docs.
    elif op_code == Close_Event.UNKNOWN:
        print("We're not sure what went wrong. Trying to reconnect...")
        _Resume(ws, seq)
    elif op_code == Close_Event.UNKNOWN_OPCODE:
        print("You sent an invalid Gateway opcode or an invalid payload for an opcode. Don't do that!")
    elif op_code == Close_Event.DECODE_ERROR:
        print("You sent an invalid payload to us. Don't do that!")
    elif op_code == Close_Event.NOT_AUTHENTICATED:
        print("You sent us a payload prior to identifying.")
    elif op_code == Close_Event.AUTHENTICATION_FAILED:
        print("You sent an invalid payload to us. Don't do that!")
    elif op_code == Close_Event.ALREADY_AUTHENTICATED:
        print("You sent more than one identify payload. Don't do that!")
    elif op_code == Close_Event.INVALID_SEQ:
        print("The account token sent with your identify payload is incorrect.")
    elif op_code == Close_Event.RATE_LIMITED:
        print("Woah nelly! You're sending payloads to us too quickly. Slow it down! You will be disconnected on receiving this.")
    elif op_code == Close_Event.SESSION_TIMED_OUT:
        print("Your session timed out. Reconnect and start a new one.")
    elif op_code == Close_Event.INVALID_SHARD:
        print(" You sent us an invalid shard when identifying.")
    elif op_code == Close_Event.SHARDING_REQUIRED:
        print("The session would have handled too many guilds - you are required to shard your connection in order to connect.")
    elif op_code == Close_Event.INVALID_API_VERSION:
        print("You sent an invalid version for the gateway.")
    elif op_code == Close_Event.INVALID_INTENTS:
        print("You sent an invalid intent for a Gateway Intent. You may have incorrectly calculated the bitwise value.")
    elif op_code == Close_Event.DISALLOWED_INTENTS:
        print("You sent a disallowed intent for a Gateway Intent. You may have tried to specify an intent that you have not enabled or are not approved for.")


def _Identify(ws):
    data = {
            "op": int(Op_Code.IDENTIFY),
            "d": {
                "token": _token,
                "intents": intents_flag,
                "properties": {
                    "$os": "windows",
                    "$browser": "fun",
                    "$device": "fun"
                }
            }
        }

    ws.send(json.dumps(data))


def _Interactions(message):
    username = message["d"]["member"]["user"]["username"]
    interaction_token = message["d"]["token"]
    interaction_id = message["d"]["id"]
    #print(f"username: {username}")
    url = f"https://discord.com/api/v9/interactions/{interaction_id}/{interaction_token}/callback"
    #print(message["d"]["data"]["name"])

    http_resp = None
    message_name = message["d"]["data"]["name"]
    username = message["d"]["member"]["user"]["username"]
    for k,v in commands.items():
        if message_name == k:
            #print(f"{k=} {v=}")
            if type(v) == list:
                if len(v[0]) >= 4:
                    if v[0][0:4] == "func":
                        ret = v[1]((v[0][4::].replace("@value", message["d"]["data"]["options"][0]["value"])))
                        data = {
                                "type": 4,
                                "data": {
                                    "content": ret
                                }
                            }

                    else:
                        print("Command[0] does not contain func keyword.")
                        break

                else:
                    print("Command[0] must contain func keyword.")
                    break

            else:
                data = {
                        "type": 4,
                        "data": {
                            "content": v.replace("@username", username)
                        }
                    }
            #print(f"data {data}")
            http_resp = _RequestHTTP("POST", url, data)
            #print(http_resp.data)
            break

    if http_resp == None:
        print("Command has not been registered.")

# This function checks the message content as opposed to the name.
# This will become a privilige in April of 2022 for bots that are in more than 75 servers.
# Note: GUILD_MESSAGES intents needs to be specified when identifying to trigger this function.

def _Message_content(message):
    channel_id = message["d"]["channel_id"]
    username = message["d"]["author"]["username"]
    content = message["d"]["content"]
    message_id = message["d"]["id"]
    #print(f"username: {username}")
    #print(f"channel_id: {channel_id}")
    #print(f"content: {content}")

    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    url_delete = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
    data = None

    for k,v in banned_words.items():
        for word in v:
            # Very naive checker.
            if re.search(word, content.lower()):
                #print("bad word found")
                #print(f"language: {k}")
                if k == "English":
                    if k in banned_words_reaction:
                        data = {
                                "content": banned_words_reaction[k]
                        }
                    else:
                        print("Found {lang} bad word, but no reaction defined.")

                elif k == "Turkish":
                    if k in banned_words_reaction:
                        data = {
                                "content": banned_words_reaction[k]
                        }
                    else:
                        print("Found {lang} bad word, but no reaction defined.")
                elif k == "Dutch":
                    if k in banned_words_reaction:
                        data = {
                                "content": banned_words_reaction[k]
                        }
                    else:
                        print("Found {lang} bad word, but no reaction defined.")

                break

    if data is not None:
        http_resp = _RequestHTTP("POST", url, data)
        #print(http_resp.data)
        http_resp = _RequestHTTP("DELETE", url_delete)
        #print(http_resp.data)
    #else:
        #print("No banned words found")


def _On_message(ws, message):
    #print(ws)
    message_d = json.loads(message)
    #print(f"message: {message_d}")
    
    if message_d["t"] == "READY":
        global bot_name
        bot_name = message_d["d"]["user"]["username"]
    elif message_d["t"] == "INTERACTION_CREATE":
        Thread(target=_Interactions, args=(message_d,)).start()
    elif message_d["t"] == "MESSAGE_CREATE" and message_d["d"]["author"]["username"] != bot_name:
        Thread(target=_Message_content, args=(message_d,)).start()
    else:
        op_code = None
        seq = message_d["s"]

        if Connection.interval is None:
            if message_d["d"] is not None or message_d["d"] is not False and "heartbeat_interval" in message["d"]:
                Connection.interval = int((message_d["d"]["heartbeat_interval"]) / 1000)

        #print(f"interval: {Connection.interval}")
        #print(f"seq {seq}")

        # Op code will most likely always be in the response.
        op_code = message_d["op"]
        #print(f"op code: {op_code}")


        _Event_handler(ws, op_code, seq, message)

        if Connection.identified is False:
            _Identify(ws)
            Connection.identified = True
            Connection.id = message_d["d"]["session_id"]


def _On_open(ws):
    print("Connected")
    #print(f"gateway {Connection.wss}\n")


# Error gets fired even though no errors have been found,
# I assume this bug is due to executing the websocket.forever function in a different thread.
def _On_error(ws, error):
    pass
    #print("Error")
    #print(error)


def _On_close(ws, close_status_code, close_msg):
    print("\nConnection closed")
    print(f"Status: {close_status_code}")
    print(f"Close message: {close_msg}\n")
    os._exit(0)


def _Connect():
    if Connection.wss is None:
        # Create a file if gateway is not already cached
        if os.path.isfile("url.txt") is False: 
            #print("Gateway is not cached yet")
            url = "https://discord.com/api/v9/gateway/bot"
            resp = _RequestHTTP("GET", url)
            Connection.wss = ((json.loads(resp.data)["url"]) + "?v=9&encoding=json")
            with open("url.txt", "w") as f:
                f.write(Connection.wss)
        else:
            #print("Got the cached gateway")
            with open("url.txt", "r") as f:
                Connection.wss = f.readline().strip("\n")

    Connection.ws = websocket.WebSocketApp(Connection.wss, on_message=_On_message, on_error=_On_error, 
                                       on_close=_On_close, on_open=_On_open)
    Connection.ws.run_forever()


def Connect(token, api, guild=None, intents=None):
    #websocket.enableTrace(True)
    if token is not None or api is not None:
        global _token
        global _api
        global _guild
        _token = token
        _api = api
        _guild = guild

        global intents_flag
        if type(intents) == list:
            for n in intents:
                if n in Intents_Token:
                    intents_flag += Intents_Token[n]

        elif intents is not None:
            print("Intents must be an array.")
            os._exit(0)

        if intents_flag == 0:
            # Intents is required upon identifying, so the default is GUILDS.
            intents_flag = 1

        #print(f"{intents_flag=}")

        Thread(target=_Connect, daemon=True).start()
    else:
        print("Token and api key are required.")
        os._exit(0)


def _Keep_alive():
    signal.signal(signal.SIGINT, _Interrupt)
    # We need this keep the main thread alive, since python only executes 1 thread at a time due to the global interperter lock, 
    # to stop the program immediately on pressing CTRL + C.
    while True:
        pass


def Main(func):
    if _token is not None or _api is not None: 
        def wrapper(*args, **kwargs):
            func()

        return wrapper(), _Keep_alive()
    else:
        print("You are not connected.")


