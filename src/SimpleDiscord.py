import os
import json
import urllib3
from threading import Thread
import signal
import websocket
import time
import zlib
from enum  import IntEnum
from dataclasses import dataclass
import io


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
    UNKNOWN = 4000
    UNKNOWN_OPCODE = 4001
    DECODE_ERROR = 4002
    NOT_AUTHENTICATED = 4003
    AUTHENTICATION_FAILED = 4004
    ALREADY_AUTHENTICATED = 4005
    INVALID_SEQ = 4007
    RATE_LIMITED = 4008
    SESSION_TIMED_OUT = 4009
    INVALID_SHARD = 4010
    SHARDING_REQUIRED = 40011
    INVALID_API_VERSION = 4012
    INVALID_INTENTS = 4013
    DISALLOWED_INTENTS = 4014



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


user = {"username": None}


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
        print(f"data not None")
        data_encoded = json.dumps(data)
        print(f"data encoded {data}")
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


def Register(name, description, message, command_type=1, url=None):
    print(url)
    if url == None:
        url = f"https://discord.com/api/v9/applications/{_api}/guilds/{_guild}/commands"

    headers = {
            "Authorization": _token,
            "Content-Type": "application/json"
    }
    data = {
            "name": name,
            "type": command_type,
            "description": description,
            "value": message
    }
    data_encoded = json.dumps(data)
    resp = _http.request(
            "POST",
            url,
            headers=headers,
            body=data_encoded)

    resp.auto_close = False
    if resp.status == 200 or resp.status == 201:
        print("Registered bot commands:")
        print(resp.status, resp.reason)
        #for line in io.TextIOWrapper(resp):
        #    print(line)
        print()
        print(resp.data)
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
        print(resp.status, resp.reason)
        print()
        print(resp.data)
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
        print("Send heartbeat")
        data = {
                "op": int(Op_Code.HEARTBEAT),
                "d": seq
            }
        ws.send(json.dumps(data))

    elif op_code == Op_Code.HEARTBEAT_ACK:
        print("ACK heartbeat")
        _ack_heartbeat = True
    elif op_code == Op_Code.DISPATCH:
        print("Message dispatched")
    elif op_code == Op_Code.RECONNECT:
        _Reconnect()
    elif op_code == Op_Code.INVALID_SESSION:
        # Discord sends this op code if it's down, so according to the docs I should continue to heartbeat.
        print("Discord is down, waiting untill it's up...")
        _ack_heartbeat = True
    elif op_code == Op_Code.HELLO:
        print("Got a hello request")
        def Send_heartbeat(ws, _loop_heartbeat):
            while _loop_heartbeat is True:
                global _ack_heartbeat
                if _ack_heartbeat is None or _ack_heartbeat is True:
                    # Only check for ack of heartbeat if connection is established which includes sending a heartbeat once.
                    if _ack_heartbeat is True:
                        _ack_heartbeat = False
                    print("Send heartbeat interval")
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



    elif op_code >= Close_Event.UNKNOWN and op_code <= Close_Event.DISALLOWED_INTENTS:
        _Resume(ws, seq)
    else:
        pass
        # Some other event.


def _Identify(ws):
    data = {
            "op": int(Op_Code.IDENTIFY),
            "d": {
                "token": _token,
                "intents": 8,
                "properties": {
                    "$os": "windows",
                    "$browser": "fun",
                    "$device": "fun"
                }
            }
        }

    ws.send(json.dumps(data))

def _Interactions(message):
    print(f"message in interactions {message}")
    username = message["d"]["member"]["user"]["username"]
    interaction_token = message["d"]["token"]
    interaction_id = message["d"]["id"]
    print(f"username: {username}")
    url = f"https://discord.com/api/v9/interactions/{interaction_id}/{interaction_token}/callback"
    print(message["d"]["data"]["name"])
    user["username"] = username

    http_resp = None
    message_name = message["d"]["data"]["name"]
    for k,v in user.items():
        if message_name == k:
            data = {
                    "type": 4,
                    "data": {
                        "content": v.replace("None", username)
                    }
                }
            print(f"data {data}")
            http_resp = _RequestHTTP("POST", url, data)
            print(http_resp.data)

    if http_resp == None:
        print("Command has not been registered.")
    """
    if message_name == "greetings":
        data = {
                "type": 4,
                "data": {
                    "content": "Greetings " + username
                }
            }
        print(f"data {data}")
        http_resp = _RequestHTTP("POST", url, data)
        print(http_resp.data)
    if http_resp == None:
        print("Command has not been registered.")
    """


def _On_message(ws, message):
    #print(ws)
    message_d = json.loads(message)
    print(f"message: {message_d}")
    
    if message_d["t"] == "INTERACTION_CREATE":
        Thread(target=_Interactions, args=(message_d,)).start()
    else:
        op_code = None
        seq = message_d["s"]

        if Connection.interval is None:
            if message_d["d"] is not None or message_d["d"] is not False and "heartbeat_interval" in message["d"]:
                Connection.interval = int((message_d["d"]["heartbeat_interval"]) / 1000)

        print(f"interval: {Connection.interval}")
        print(f"seq {seq}")

        # Op code will most likely always be in the response.
        op_code = message_d["op"]
        print(f"op code: {op_code}")


        _Event_handler(ws, op_code, seq, message)

        if Connection.identified is False:
            _Identify(ws)
            Connection.identified = True
            Connection.id = message_d["d"]["session_id"]


def _On_open(ws):
    print("connected")
    print(f"gateway {Connection.wss}\n")


def _On_error(ws, error):
    print(error)


def _On_close(ws, close_status_code, close_msg):
    print("\nconnection closed")
    print(f"status: {close_status_code}")
    print(f"close message: {close_msg}\n")


def _Connect():
    if Connection.wss is None:
        # Create a file if gateway is not already cached
        if os.path.isfile("url.txt") is False: 
            print("Gateway is not cached yet")
            url = "https://discord.com/api/v9/gateway/bot"
            resp = _RequestHTTP("GET", url)
            Connection.wss = ((json.loads(resp.data)["url"]) + "?v=9&encoding=json")
            with open("url.txt", "w") as f:
                f.write(Connection.wss)
        else:
            print("Got the cached gateway")
            with open("url.txt", "r") as f:
                Connection.wss = f.readline().strip("\n")

    Connection.ws = websocket.WebSocketApp(Connection.wss, on_message=_On_message, on_error=_On_error, 
                                       on_close=_On_close, on_open=_On_open)
    Connection.ws.run_forever()


def Connect(token, api, guild=None):
    #websocket.enableTrace(True)
    global _token
    global _api
    global _guild
    _token = token
    _api = api
    _guild = guild

    Thread(target=_Connect, daemon=True).start()


def _Keep_alive():
    signal.signal(signal.SIGINT, _Interrupt)
    # We need this keep the main thread alive, since python only executes 1 thread at a time due to the global interperter lock, 
    # to stop the program immediately on pressing CTRL + C.
    while True:
        pass


def Main(func):
    print("main")
    def wrapper(*arg, **kwargs):
        func()

    return wrapper(), _Keep_alive()



#if __name__ == "__main__":
#    Connect()

