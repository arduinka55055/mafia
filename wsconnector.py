from __future__ import annotations
import os
import io
import json
import random
from typing import Any, Union
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
import mafia
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
        self.pck = data.get("pck")         # Packet type
        self.target = data.get("uuid")     # Unique ID (not GID) of target
        self.game = data.get("gameuuid")   # Unique ID of game room
        self.data = data.get("data")       # Misc data

    def validate(self) -> bool:
        return False if self.gid == None or self.nick == None else True

    def consumePacket(self,conn:WebsocketConnector) -> Union[bytes, None]:
        try:
            if self.pck == "MakeRoom":
                roomHandler.rooms.newRoom(self.data[0], self.gid, self.data[1])

            elif self.pck == "GetInfo":
                roomreply=roomHandler.rooms.stat()
                roomreply["pck"]="Info"
                return json_encode(roomreply).encode()

            elif self.pck == "ClientHello":
                session=roomHandler.rooms.fromUUID(self.game)
                player=mafia.PlayerRAW(self.nick,self.gid,self.ava)
                session.join(player)
                conn.gameLink(self.game,self.gid)
                return '{"pck":"ServerHello"}'.encode()

            elif self.pck == "StartGame":
                room = roomHandler.rooms.fromUUID(self.game)
                room.start(self.gid)
                clients.broadcast({"pck": "GameStarted", "rid": room.getUUID()})

            elif self.pck == "role":
                room = roomHandler.rooms.fromUUID(self.game)
                room.performRole(self.gid)

        except mafia.PlayerNotFoundError:
            return ('{"pck":"Error","id":"%s","msg":"PlayerNotFound"}' % self.target).encode()

        except roomHandler.RoomNotFoundError:
            return ('{"pck":"Error","id":"%s","msg":"RoomNotFound"}' % self.game).encode()

        except roomHandler.NoEnoughPlayersError:
            return '{"pck":"Error","msg":"GameStartError","spec":"NoEnoughPlayers"}'.encode()

        except roomHandler.PermissionDeniedError:
            return '{"pck":"Error","msg":"GameStartError","spec":"PermissionDenied"}'.encode()

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
        ret = data.consumePacket(self)
        if ret:
            self.write_message(ret)
        else:
            self.write_message('{"pck":"ack"}')

    def on_pong(self, data: bytes) -> None:
        print("PING!")
        return super().on_pong(data)

    def on_close(self):
        for client in clients:
            if client == self:
                client.destroy()
                break 
        clients.broadcast("player problems!")
        print("WebSocket closed")

    def check_origin(self, origin):
        return True

    def destroy(self):
        roomHandler.rooms.fromUUID(self.gameuuid).leave(self.gamegid)
        clients.remove(self)

    def gameLink(self,UUID,gid):
        self.gameuuid=UUID
        self.gamegid=gid
