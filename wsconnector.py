import os
import io
import json
import random
from typing import Union
import urllib
import asyncio
import datetime
import aiomysql
from tornado.escape import json_encode
import tornado.ioloop
import tornado.httpclient
import tornado.web
import tornado.auth
import tornado.template
import tornado.websocket
import user_agents

import roomHandler
"""
basic connection:

+-----ROOM-------+    +---------+
|   room UUID    | <- | players |
|   maxPlayers   |    |  (raw)  |
| optional rules | -> | gid+nick|
+================+    +=========+ 
       \\//
 +----PLAYER-----+    +---------+
 |   nickname    |    |  role   |   mainloop
 |   google ID   | -> | own gid | <-------+
 |   room        | -> |  UUID   |    Game |    
 +===============+    +=========+         |
                         \\//             |  
                     +==========+    +=========+
              (night)|  done!   | -> | results |
                     |  waiting |    |         |
                     +==========+    +=========+
"""


class ClientPacket:
    def __init__(self, data):
        data = json.loads(data)
        self.gid = data.get("gid")         # Google ID
        self.nick = data.get("nick")       # Nickname
        self.ava = data.get("avatar")      # Avatar
        self.pck = data.get("pck")         # Reserved
        self.target = data.get("uuid")     # Unique ID (not GID) of target
        self.game = data.get("gameuuid")   # Unique ID of game room
        self.data = data.get("data")       # Misc data

    def validate(self) -> bool:
        return False if self.gid == None or self.nick == None else True

    def consumePacket(self) -> Union[bytes, None]:
        if self.pck == "MakeRoom":
            roomHandler.rooms.newRoom(self.data[0], self.gid, self.data[1])

        elif self.pck == "GetInfo":
            return json_encode(roomHandler.rooms.stat()).encode()

        elif self.pck == "startgame":
            room = roomHandler.rooms.fromUUID(self.game)
            room.start(self.gid)
            clients.broadcast({"type": "started", "uuid": room.getUUID()})

        elif self.pck == "role":
            room = roomHandler.rooms.fromUUID(self.game)
            room.performRole(self.gid)


class Clients(set):
    def broadcast(self, message):
        for client in self:
            message = json.dumps(message)
            client.write_message(message)


clients = Clients()


class WebsocketConnector(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.add(self)
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message('{"pck":"conn_succ"}')
        print(message)
        data = ClientPacket(message)
        if not data.validate():
            self.close(reason="Invalid data, relogin!")
            return
        ret = data.consumePacket()
        if ret:
            self.write_message(ret)
        else:
            self.write_message('{"pck":"ack"}')

    def on_pong(self, data: bytes) -> None:
        print("PING!")
        return super().on_pong(data)

    def on_close(self):
        clients.remove(self)
        clients.broadcast("player problems!")
        print("WebSocket closed")

    def check_origin(self, origin):
        return True
