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
import re
from simplediscord.utils import mylogger

# Discord opcodes
class Op_Code(IntEnum):
    DISPATCH               = 0
    HEARTBEAT              = 1
    IDENTIFY               = 2
    UPDATE_CLIENT_PRESENCE = 3
    VOICE_STATE_UPDATE     = 4
    RESUME_SESSION         = 6
    RECONNECT              = 7
    GUILD_MEMBERS          = 8
    INVALID_SESSION        = 9
    HELLO                  = 10
    HEARTBEAT_ACK          = 11

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

_token = None
_guild = None
_api = None

LOGGER_FATAL = mylogger.FATAL
LOGGER_WARNING = mylogger.WARNING
LOGGER_INFO = mylogger.INFO
LOGGER_DEBUG = mylogger.DEBUG

def SetLoggerLevel(level):
    mylogger.level = level


@dataclass
class Connection:
    ws = None
    url = None
    interval = None
    identified = False

_loop_heartbeat = True
_ack_heartbeat = None


commands = {}
intents_flag = 0

bot_name = None

banned_words = {}
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
    mylogger.debug("request called")

    if data:
        mylogger.debug(f"data not None")
        data_encoded = json.dumps(data)
        mylogger.debug(f"data encoded {data}")
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
    mylogger.debug(url)
    if url == None:
        url = f"https://discord.com/api/v9/applications/{_api}/guilds/{_guild}/commands"

    headers = {
            "Authorization": _token,
            "Content-Type": "application/json"
    }

    # Slash command with options and choices.
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
        mylogger.debug(f"{data=}")
        j = 0
        for i in range(name_index, len(name)):
            data["options"][0]["choices"].append({})
            data["options"][0]["choices"][j]["name"] = name[i]
            data["options"][0]["choices"][j]["value"] = message[j]
            j += 1

        mylogger.debug(f"{data=}")

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
        mylogger.debug(f"Successfully Registered bot command: {name}")
        mylogger.debug(resp.data)
    else:
        mylogger.debug(resp.status, resp.reason)


def Slash_commands(url=None):
    if not url:
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
        mylogger.debug("Registered bot commands:")
        mylogger.debug(resp.data)
    else:
        mylogger.debug(resp.status, resp.reason)


def Change_username(username):
    url = "https://discord.com/api/users/@me"
    data = {
            "username": username
    }
    resp = _RequestHTTP("PATCH", url, data)
    if resp.status != 200:
        mylogger.debug(resp.status, resp.reason)
    mylogger.debug(resp.status, resp.reason)


# The bot will delete a message containing word(s) from the dictionary in a channel, and warn the user.

# File syntax is as follows:
# Uppercase for specifying a language.
# Lowercase adjacent to the language for words.

def Filter(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            lang = None
            for line in f:
                if line[0].isupper():
                    lang = line.strip()
                elif lang and line != "\n":
                    if lang not in banned_words:
                        banned_words[lang] = [line.strip()]
                    else:
                        banned_words[lang].append(line.strip())
    except FileNotFoundError:
        mylogger.warning("Could not find file " + file)



def _Event_handler(ws, op_code, seq, message):
    global _ack_heartbeat
    if op_code == Op_Code.HEARTBEAT:
        mylogger.debug("Send heartbeat")
        data = {
                "op": int(Op_Code.HEARTBEAT),
                "d": seq
            }
        ws.send(json.dumps(data))

    elif op_code == Op_Code.HEARTBEAT_ACK:
        mylogger.debug("ACK heartbeat")
        _ack_heartbeat = True
    elif op_code == Op_Code.DISPATCH:
        pass
        mylogger.debug("Message dispatched")
    elif op_code == Op_Code.RECONNECT:
        _Reconnect()
    elif op_code == Op_Code.INVALID_SESSION:

        # Discord sends this op code if it's down, so according to the docs I should continue to heartbeat.
        # This could be ambiguous and thus behave incorrectly.
        mylogger.fatal("Discord is down, waiting untill it's up...")
        _ack_heartbeat = True
    elif op_code == Op_Code.HELLO:
        mylogger.debug("Hello request received.")
        def Send_heartbeat(ws, _loop_heartbeat):
            while _loop_heartbeat is True:
                global _ack_heartbeat

                # None = the first initiation of the connection.
                if _ack_heartbeat is None or _ack_heartbeat is True:

                    # Only check for ack of a heartbeat after the connection is established, 
                    # because the process of connecting includes sending a heartbeat once.
                    if _ack_heartbeat is True:
                        _ack_heartbeat = False
                    mylogger.debug("Send heartbeat interval")
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
        mylogger.fatal("We're not sure what went wrong. Trying to reconnect...")
        _Resume(ws, seq)
    elif op_code == Close_Event.UNKNOWN_OPCODE:
        mylogger.fatal("You sent an invalid Gateway opcode or an invalid payload for an opcode. Don't do that!")
        os._exit(0)
    elif op_code == Close_Event.DECODE_ERROR:
        mylogger.fatal("You sent an invalid payload to us. Don't do that!")
        os._exit(0)
    elif op_code == Close_Event.NOT_AUTHENTICATED:
        mylogger.fatal("You sent us a payload prior to identifying.")
        os._exit(0)
    elif op_code == Close_Event.AUTHENTICATION_FAILED:
        mylogger.fatal("You sent an invalid payload to us. Don't do that!")
        os._exit(0)
    elif op_code == Close_Event.ALREADY_AUTHENTICATED:
        mylogger.fatal("You sent more than one identify payload. Don't do that!")
        os._exit(0)
    elif op_code == Close_Event.INVALID_SEQ:
        mylogger.fatal("The account token sent with your identify payload is incorrect.")
        os._exit(0)
    elif op_code == Close_Event.RATE_LIMITED:
        mylogger.fatal("Woah nelly! You're sending payloads to us too quickly. Slow it down! You will be disconnected on receiving this.")
        os._exit(0)
    elif op_code == Close_Event.SESSION_TIMED_OUT:
        mylogger.fatal("Your session timed out. Reconnect and start a new one.")
        os._exit(0)
    elif op_code == Close_Event.INVALID_SHARD:
        mylogger.fatal(" You sent us an invalid shard when identifying.")
        os._exit(0)
    elif op_code == Close_Event.SHARDING_REQUIRED:
        mylogger.fatal("The session would have handled too many guilds - you are required to shard your connection in order to connect.")
        os._exit(0)
    elif op_code == Close_Event.INVALID_API_VERSION:
        mylogger.fatal("You sent an invalid version for the gateway.")
        os._exit(0)
    elif op_code == Close_Event.INVALID_INTENTS:
        mylogger.fatal("You sent an invalid intent for a Gateway Intent. You may have incorrectly calculated the bitwise value.")
        os._exit(0)
    elif op_code == Close_Event.DISALLOWED_INTENTS:
        mylogger.fatal("You sent a disallowed intent for a Gateway Intent. You may have tried to specify an intent that you have not enabled or are not approved for.")
        os._exit(0)


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
    message_name = message["d"]["data"]["name"]
    interaction_token = message["d"]["token"]
    interaction_id = message["d"]["id"]
    mylogger.debug(f"username: {username}")
    url = f"https://discord.com/api/v9/interactions/{interaction_id}/{interaction_token}/callback"
    mylogger.debug(message["d"]["data"]["name"])
    http_resp = None

    for k,v in commands.items():
        if message_name == k:
            mylogger.debug(f"{k=} {v=}")
            if type(v) == list:
                if len(v[0]) >= 4:
                    if v[0][0:4] == "func":
                        # Call the user-defined function with the message value as arguments or no arguments if @value is not defined.
                        ret = v[1]((v[0][4::].replace("@value", message["d"]["data"]["options"][0]["value"])))
                        data = {
                                "type": 4,
                                "data": {
                                    "content": ret
                                }
                            }

                    else:
                        mylogger.fatal("Command[0] does not contain func keyword.")
                        break

                else:
                    mylogger.fatal("Command[0] must contain func keyword.")
                    break

            else:
                data = {
                        "type": 4,
                        "data": {
                            "content": v.replace("@username", username)
                        }
                    }
            mylogger.debug(f"data {data}")
            http_resp = _RequestHTTP("POST", url, data)
            mylogger.debug(http_resp.data)
            break

    if not http_resp:
        mylogger.warning("Command has not been registered.")


# This function checks the message content as opposed to its name.
# This will become a privilige in August 31st of 2022 for bots that are in more than 75 servers, and also GUILD_PRESENCES and GUILD_MEMBERS intents.
# Note: GUILD_MESSAGES intents needs to be specified when identifying to trigger this function.

def _Message_content(message):
    channel_id = message["d"]["channel_id"]
    username = message["d"]["author"]["username"]
    content = message["d"]["content"]
    message_id = message["d"]["id"]
    mylogger.debug(f"username: {username}")
    mylogger.debug(f"channel_id: {channel_id}")
    mylogger.debug(f"content: {content}")

    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    url_delete = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
    data = None

    for k,v in banned_words.items():
        for word in v:
            # Very naive checker.
            if re.search(word, content.lower()):
                mylogger.debug("bad word found")
                mylogger.debug(f"language: {k}")
                if k in banned_words_reaction:
                    data = {
                            "content": banned_words_reaction[k]
                    }
                else:
                    mylogger.warning(f"Found {k} bad word, but no reaction defined.")
                break

    if data:
        http_resp = _RequestHTTP("POST", url, data)
        mylogger.debug(http_resp.data)
        http_resp = _RequestHTTP("DELETE", url_delete)
        mylogger.debug(http_resp.data)


def _On_message(ws, message):
    mylogger.debug(ws)
    message_d = json.loads(message)

    mylogger.debug("START Message content: \n")
    # Print JSON structures nicely with format_print.
    mylogger.debug(message_d, True)
    mylogger.debug("END Message content end\n")
    
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

        if not Connection.interval:
            if message_d["d"] and "heartbeat_interval" in message_d["d"]:
                Connection.interval = int((message_d["d"]["heartbeat_interval"]) / 1000)

        mylogger.debug(f"interval: {Connection.interval}")
        mylogger.debug(f"seq {seq}")

        # Op code will most likely always be in the response.
        op_code = message_d["op"]
        mylogger.debug(f"op code: {op_code}")


        _Event_handler(ws, op_code, seq, message)

        if not Connection.identified:
            _Identify(ws)
            Connection.identified = True
            Connection.id = message_d["d"]["session_id"]


def _On_open(ws):
    mylogger.info("Connected")
    mylogger.debug(f"gateway {Connection.url}\n")


# Error gets fired even though no errors have been found,
# I assume this bug is due to executing the websocket.forever function in a different thread.
def _On_error(ws, error):
    pass


def _On_close(ws, close_status_code, close_msg):
    mylogger.info("Connection closed")
    mylogger.debug(f"Close status code: {close_status_code}")
    mylogger.debug(f"Close message: {close_msg}\n")
    os._exit(0)


def _Connect():
    if not Connection.url:
        # Create a file if gateway is not already cached
        if os.path.isfile("url.txt") is False: 
            mylogger.debug("Gateway is not cached yet.")
            url = "https://discord.com/api/v9/gateway/bot"
            resp = _RequestHTTP("GET", url)
            Connection.url = ((json.loads(resp.data)["url"]) + "?v=9&encoding=json")
            with open("url.txt", "w") as f:
                f.write(Connection.url)
        else:
            mylogger.debug("Used cached gateway.")
            with open("url.txt", "r") as f:
                Connection.url = f.readline().strip("\n")

    Connection.ws = websocket.WebSocketApp(Connection.url, on_message=_On_message, on_error=_On_error, 
                                       on_close=_On_close, on_open=_On_open)
    Connection.ws.run_forever()


def Connect(token, api, guild=None, intents=None):
    #websocket.enableTrace(True)
    if token and api:
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
            if intents_flag == 0:
                # Intents is required upon identifying, so the default is GUILDS.
                intents_flag = 1

        elif intents:
            mylogger.fatal("Intents must be an array.")
            os._exit(0)

        else:
            intents_flag = 1

        mylogger.debug(f"{intents_flag=}")

        Thread(target=_Connect, daemon=True).start()
    else:
        mylogger.fatal("Token and api key are required.")
        os._exit(0)


def _Keep_alive():
    signal.signal(signal.SIGINT, _Interrupt)
    # We need this to keep the main thread alive, since daemon threads stop running when the main program stops, 
    # by pressing CTRL + C.
    while True:
        pass

# Entry point to all bot applications, this function is required to keep the program running and execute user defined functions.
def Main(func):
    if _token and _api: 
        def wrapper(*args, **kwargs):
            # Bug-fatal: calling this too many times could cause a too many request error, 
            # and having this error too many times causes your token to be revoked; thus your bot disabled.
            func()

        return wrapper(), _Keep_alive()
    else:
        mylogger.fatal("No token or api key given.")
        os._exit(0)
