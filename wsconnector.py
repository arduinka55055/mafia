import os
import io
import json
import random
import urllib
import asyncio
import datetime
import aiomysql
from wsconnector import WebsocketHandler
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
        self.gid = data.get("gid")          # Google ID
        self.nick = data.get("nick")        # Nickname
        self.param = data.get("param")      # Reserved
        self.target = data.get("uuid")      # Unique ID (not GID) of target
        self.game = data.get("gameuuid")    # Unique ID of game room
        self.newroom = data.get("newroom")  # Are you creating new room?

    def validate(self) -> bool:
        return False if self.gid == None or self.nick == None else True

    def consumePacket(self):
        if not self.newroom == None:
            roomHandler.rooms.newRoom(self.gid, self.newroom)
        elif self.param == "startgame":
            room = roomHandler.rooms.fromUUID(self.game)
            room.start(self.gid)
            clients.broadcast({"type":"started","uuid":room.getUUID()})
        elif self.param == "role":
            room = roomHandler.rooms.fromUUID(self.game)
            room.performRole(self.gid)

class Clients(set):
    def broadcast(self, message):
        for client in self:
            message=json.dumps(message)
            client.write_message(message)


clients = Clients()


class WebsocketConnector(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.add(self)
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)
        data = ClientPacket(message)
        if not data.validate():
            self.close(reason="Invalid data, relogin!")
            return

    def on_ping(self, data: bytes) -> None:
        print('PING!')
        return super().on_ping(data)

    def on_close(self):
        clients.broadcast("player problems!")
        print("WebSocket closed")
