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

    async def consumePacket(self,conn:WebsocketConnector) -> Union[bytes, None]:
        try:
            if self.pck == "MakeRoom":
                roomHandler.rooms.newRoom(self.data[0], self.gid, self.data[1])

            elif self.pck == "GetInfo":
                roomreply=roomHandler.rooms.stat()
                roomreply["pck"]="Info"
                return json_encode(roomreply).encode()

            elif self.pck == "GetTargets":
                roomreply={"pck":"InfoT","data":[]}
                roomreply["data"]=list(roomHandler.rooms.fromUUID(self.game).game.jsonable)
                return json_encode(roomreply).encode()

            elif self.pck == "ClientHello":
                session=roomHandler.rooms.fromUUID(self.game)
                player=mafia.PlayerRAW(self.nick,self.gid,self.ava)
                session.join(player)
                conn.gameLink(self.game,self.gid)
                return '{"pck":"ServerHello"}'.encode()

            elif self.pck == "StartGame":
                room = roomHandler.rooms.fromUUID(self.game)
                await room.start(self.gid)

            elif self.pck == "role":
                room = roomHandler.rooms.fromUUID(self.game)
                room.performRole(self.gid,self.target)

        except mafia.PlayerNotFoundError:
            return ('{"pck":"Error","id":"%s","msg":"PlayerNotFound"}' % self.target).encode()

        except roomHandler.RoomNotFoundError:
            return ('{"pck":"Error","id":"%s","msg":"RoomNotFound"}' % self.game).encode()

        except roomHandler.NoEnoughPlayersError:
            return '{"pck":"Error","msg":"GameStartError","spec":"NoEnoughPlayers"}'.encode()

        except roomHandler.PermissionDeniedError:
            return '{"pck":"Error","msg":"GameStartError","spec":"PermissionDenied"}'.encode()

        except:
            return '{"pck":"Error","msg":"ServerPizdecError","spec":"Пизда Серву!"}'.encode()

class Clients(set):

    async def broadcast(self, message:Union[dict,str]):
        for client in self:
            client.write_message(json.dumps(message))

    async def multicast(self, message:Union[dict,str], rid:mafia.ROOMID):
        for client in self:
            if client.gameuuid == rid:
                client.write_message(json.dumps(message))

    async def anycast(self, message:Union[dict,str],gid:mafia.PLAYERID):
        for client in self:
            if client.gamegid == gid:
                client.write_message(json.dumps(message))
                return        
        raise mafia.PlayerNotFoundError(gid)
    

clients = Clients()


class WebsocketConnector(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.add(self)
        print("WebSocket opened")

    async def on_message(self, message):
        self.write_message('{"pck":"conn_succ"}')
        print(message)
        data = ClientPacket(message)
        if not data.validate():
            self.close(reason="Invalid data, relogin!")
            return
        ret = await data.consumePacket(self)
        if ret:
            self.write_message(ret)
        else:
            self.write_message('{"pck":"ack"}')

    def on_pong(self, data: bytes) -> None:
        #print("PING!")
        return super().on_pong(data)

    def on_close(self):
        for client in clients:
            if client == self:
                client.destroy()
                break 
        print("WebSocket closed")

    def check_origin(self, origin):
        return True

    def destroy(self):
        roomHandler.rooms.fromUUID(self.gameuuid).leave(self.gamegid)
        clients.remove(self)

    def gameLink(self,gameUUID:mafia.ROOMID,gid:mafia.PLAYERID):
        self.gameuuid=gameUUID
        self.gamegid=gid
