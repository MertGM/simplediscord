from socket import *
import os
import json
import urllib3
from threading import Thread
import sys
import signal
import websocket
import time
import zlib


# Discord opcodes
op_dispatch = 0
op_heartbeat = 1
op_identify = 2
op_update_client_presence = 3
op_voice_state_update = 4
op_resume_session = 6
op_reconnect = 7
op_guild_members = 8
op_invalid_session = 9
op_hello = 10
op_heartbeat_ack = 11

# Discord close events
# Discord closes connection or sends invalid codes for no reason
close_event_unknown = 4000
close_event_unknown_opcode = 4001
close_event_decode_error = 4002
close_event_not_authenticated = 4003
close_event_authentication_failed = 4004
close_event_already_authenticated = 4005
close_event_invalid_seq = 4007
close_event_rate_limited = 4008
close_event_session_timed_out = 4009
close_event_invalid_shard = 4010
close_event_sharding_required = 40011
close_event_invalid_api_version = 4012
close_event_invalid_intents = 4013
close_event_disallowed_intents = 4014


port = 80
LF = 10

http = urllib3.PoolManager()
hostname = "discord.com"
port = 443
token = "Bot " + os.getenv("DISCORD_TOKEN")
api = os.getenv("DISCORD_API")
guild = os.getenv("DISCORD_GUILD")

wss = None
ws = None
interval = None
loop_heartbeat = True
loop_event = False
disconnected = False
seq = None
session_id = None
start = None

thread_created = False
identified = False
prev_op_code = None


def Interrupt(signal, frame):
    loop_heartbeat = False
    data = {"op": 1000}
    ws.send(json.dumps(data))
    ws.close()
    print("killed connection")
    sys.exit(0)

def Event_handler(ws, op_code, seq, message):
    global start
    global disconnected
    global prev_op_code

    # Todo:
    # Need to know if after a heartbeat send I get a ack
    # If I don't receive anything I should disconnect and reconnect
    # However this Event_handler doesn't get executed if I don't
    # receive anything

    """"
    disconnected = True
    start = None
    ws.close()
    Connect()
    """

    # There might be a better way than long if statements
    if  op_code == op_heartbeat:
        print("got a heartbeat")
        data = {
                "op": op_heartbeat,
                "d": seq
            }
        ws.send(json.dumps(data))

    elif op_code == op_heartbeat_ack:
        print("ACK heartbeat")
        # Ack the heartbeat
    elif op_code == op_dispatch:
        print("Got a dispatch")
    elif op_code == op_reconnect:
        print("Got a reconnect")
        Connect()
    elif op_code == op_invalid_session:
        print("Got a invalid session")
    elif op_code == op_hello:
        # Sometimes we're not receiving a ready response
        print("Got a hello req")
        global thread_created
        global loop_heartbeat
        # ws and loop_heartbeat are probably passed by value
        # ws seems to be working tho, because it's a class?
        def Send_heartbeat(ws, loop_heartbeat):
            global interval
            while loop_heartbeat is True:
                print(loop_heartbeat)
                print("send a heartbeat")
                data = {
                        "op": op_heartbeat,
                        "d": seq
                    }

                # Wait based on the interval before requesting to discord api
                time.sleep(interval)
                ws.send(json.dumps(data))
        Thread(target=Send_heartbeat, args=(ws,loop_heartbeat), daemon=True).start()


    elif ((op_code >= close_event_unknown) and (op_code <= close_event_disallowed_intents)):
        disconnected = True
        ws.close()
        Connect()
    else:
        pass
        # Some other event

        """"
    elif op_code == close_event_unknown_opcode:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_decode_error:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_not_authenticated:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code  == close_event_authentication_failed:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code  == close_event_already_authenticated:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code  == close_event_invalid_seq:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_rate_limited:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_session_timed_out:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_invalid_shard:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_sharding_required:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_invalid_api_version:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_invalid_intents:
        disconnected = True
        print(message)
        ws.close()
        Connect()
    elif op_code == close_event_disallowed_intents:
        disconnected = True
        print(message)
        ws.close()
        Connect()
        """

def Identify(ws):
    data = {
            "op": op_identify,
            "d": {
                "token": token,
                "intents": 8,
                "properties": {
                    "$os": "windows",
                    "$browser": "fun",
                    "$device": "fun"
                }
            }
        }

    ws.send(json.dumps(data))

def Interactions(message):
    print(f"message in interactions {message}")
    user = message["d"]["member"]["user"]["username"]
    interaction_token = message["d"]["token"]
    interaction_id = message["d"]["id"]
    print(f"user {user}")
    url = f"https://discord.com/api/v9/interactions/{interaction_id}/{interaction_token}/callback"
    print(message["d"]["data"]["name"])

    if ((message["d"]["data"]["name"]) == "greetings"):
        data = {
                "type": 4,
                "data": {
                    "content": "Greetings " + user
                }
            }
        print(f"data {data}")
        resp = RequestHTTP("POST", url, data)
        print(resp.data)


def On_message(ws, message):
    global interval
    global identified
    global seq
    global session_id

    print(ws)
    message_d = json.loads(message)
    print(f"message: {message_d}")
    
    if message_d["t"] == "INTERACTION_CREATE":
        #Interactions(message_d)
        Thread(target=Interactions, args=(message_d,)).start()
    else:
        op_code = None
        seq = None
        seq = message_d["s"]

        if message_d["d"] is not None or message_d["d"] is not False:
            if interval is None:
                if "heartbeat_interval" in message_d["d"]:
                    interval = int((message_d["d"]["heartbeat_interval"]) / 1000)

        print(f"interval: {interval}")
        print(f"seq {seq}")

        # op code will most likely always be in the response
        op_code = message_d["op"]
        print(f"op code: {op_code}")


        Event_handler(ws, op_code, seq, message)
        if identified is False:
            Identify(ws)
            identified = True
            session_id = message_d["d"]["session_id"]


def Resume(ws):
    global seq
    global session_id
    data = {
            "op": op_resume_session,
            "d": {
                "token": token,
                "session_id": session_id,
                "seq": seq
            }
        }
    ws.send(json.loads(data))


def On_open(ws):
    global disconnected
    if disconnected is True:
        Resume(ws)
        disconnected = False
    print("connecting")
    print(f"gateway {wss}")


def On_error(ws, error):
    print(error)


def On_close(ws, close_status_code, close_msg):
    print("connection closed")
    print(f"status: {close_status_code}")
    print(f"close message: {close_msg}")


def RequestHTTP(method, url, data=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    print("request called")
    #if method == "GET":
    #    headers["Authorization"] = token
    if data is not None:
        print(f"data not None {data}")
        data_encoded = json.dumps(data)
        print(f"data encoded {data}")
        resp = http.request(
                method,
                url,
                headers=headers,
                body=data_encoded)
        return resp
    else:
        resp = http.request(
                method,
                url,
                headers=headers)
        return resp

def isServerDown():
    resp = RequestHTTP("GET", "https://discord.com/api/v9/gateway/bot")
    if resp.status != 200:
        print(f"server is down {resp.status}")
        return True
    return False



def Connect():
    global wss
    global ws
    if wss is None:
        # Create a file if gateway is not already cached
        if os.path.isfile("url.txt") is False: 
            print("Gateway is not cached yet")
            url = "https://discord.com/api/v9/gateway/bot"
            resp = RequestHTTP("GET", url)
            wss = ((json.loads(resp.data)["url"]) + "?v=9&encoding=json")
            with open("url.txt", "w") as f:
                f.write(wss)
        else:
            print("Got the cached gateway")
            with open("url.txt", "r") as f:
                wss = f.readline().strip("\n")

    ws = websocket.WebSocketApp(wss, on_message=On_message, on_error=On_error, 
                                       on_close=On_close, on_open=On_open)
    ws.run_forever()


def Main():
    signal.signal(signal.SIGINT, Interrupt)
    #websocket.enableTrace(True)
    #url = f"https://discord.com/api/v9/applications/{api}/guilds/{guild}/commands"
    Connect()

    print("Main exit")

    # Not handling closing properly, need to close websocket somehow
    # making ws global gives errors


if __name__ == "__main__":
    Main()
