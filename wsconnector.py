from __future__ import annotations
import os
import io
import sys
import json
import random
from typing import Any, Union
import datetime
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
from traceback import format_exception

import roomHandler
import mafia
"""
basic connection:

+-----ROOM-------+    +---------+    +===========+
|   room UUID    | <- | players | <- |  connect  |
|   maxPlayers   |    |  (raw)  |    |  manager  |
| optional rules | -> | gid+nick| -> |(framework)|
+================+    +=========+    +===========+
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
        self.gid = data.get("gid")        # Google ID
        self.nick = data.get("nick")      # Nickname
        self.ava = data.get("avatar")     # Avatar
        self.pck = data.get("pck")        # Packet type
        self.target = data.get("pid")     # Unique ID (not GID) of target
        self.game = data.get("rid")       # Unique ID of game room
        self.data = data.get("data")      # Misc data

    def validate(self) -> bool:
        return False if self.gid == None or self.nick == None else True
        
    def getRoom(self)->roomHandler.Room:
        return roomHandler.rooms.fromUUID(self.game)

    async def consumePacket(self,conn:WebsocketConnector) -> Union[bytes, None]:
        try:
            if self.pck == "MakeRoom":
                # id:12345
                roomreply = {}
                roomreply["id"]=roomHandler.rooms.newRoom(self.data[0], mafia.PlayerRAW(self.nick,self.gid,self.ava), self.data[1])
                roomreply["pck"]="MadeRoom"
                return json_encode(roomreply).encode(encoding="utf-8")
            elif self.pck == "GetInfo":
                roomreply=roomHandler.rooms.stat(self.gid)
                roomreply["pck"]="Info"
                return json_encode(roomreply).encode(encoding="utf-8")

            elif self.pck == "GetTargets":
                roomreply={"pck":"InfoT","data":[]}
                roomreply["data"]=list(self.getRoom().game.jsonable)
                return json_encode(roomreply).encode()

            elif self.pck == "Me":
                session=self.getRoom()
                if session.isStarted:
                    roomreply=session.game.getByGID(self.gid).jsonableP
                    roomreply['pck']="You"
                    return json_encode(roomreply).encode()
                else:
                    raise roomHandler.GameNotStartedError(self.game)

            elif self.pck == "ClientHello":
                session=self.getRoom()
                player=mafia.PlayerRAW(self.nick,self.gid,self.ava)
                roomHandler.rooms.kick(player.id)
                session.join(player)
                conn.gameLink(session.UUID,self.gid)
                return '{"pck":"ServerHello"}'.encode()

            elif self.pck == "Reconnect":
                session=self.getRoom()
                conn.gameLink(session.UUID,self.gid)
                return '{"pck":"Success"}'.encode()
                
            elif self.pck == "StartGame":
                room = self.getRoom()
                await room.start(self.gid)
                return '{"pck":"GameStartSuccess"}'.encode()

            elif self.pck == "Perform":
                room = self.getRoom()
                await room.performRole(self.gid,self.target)

        except mafia.PlayerNotFoundError:
            return ('{"pck":"Error","id":"%s","msg":"PlayerNotFound"}' % self.target).encode()

        except roomHandler.RoomNotFoundError:
            return ('{"pck":"Error","id":"%s","msg":"RoomNotFound"}' % self.game).encode()

        except roomHandler.NoEnoughPlayersError:
            return '{"pck":"Error","msg":"GameStartError","spec":"NoEnoughPlayers"}'.encode()
        
        except roomHandler.GameNotStartedError:
            return '{"pck":"Error","msg":"GameNotStarted","spec":"GameNotStarted"}'.encode()

        except roomHandler.PermissionDeniedError:
            return '{"pck":"Error","msg":"GameStartError","spec":"PermissionDenied"}'.encode()

        except:
            err=sys.exc_info()
            shit=''.join(format_exception(*err))
            shit=shit.replace('"','\"').replace("'","\'")
            return ('{"pck":"Error","msg":"ServerPizdecError","spec":"Пизда Серву!%s"}' % shit).encode()

class Clients(set):

    async def broadcast(self, message:Union[dict,str]):
        for client in self:
            try:
                client.write_message(json.dumps(message))
            except:
                pass

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
        self.ping()
        print("WebSocket opened")

    async def on_message(self, message):
        self.write_message('{"pck":"conn_succ"}')
        #print(message) TODO:normal debug
        data = ClientPacket(message)
        if not data.validate():
            self.close(reason="['Invalid data, relogin!']")
            return
        ret = await data.consumePacket(self)
        #print(ret)
        if ret:
            self.write_message(ret)
        else:
            self.write_message('{"pck":"ack"}')

    def on_pong(self, data: bytes) -> None:
        ret={
            "pck":"Ping",
            "timestamp":datetime.datetime.timestamp(datetime.datetime.now()),
            "players":len(clients),
            "rooms":len(roomHandler.rooms)
        }
        self.write_message(json.dumps(ret))
        #self.ping()
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
        if self.gameuuid and self.gamegid:
            roomHandler.rooms.fromUUID(self.gameuuid).leave(self.gamegid)
        clients.remove(self)
    @property
    def gameuuid(self)->Union[mafia.ROOMID,None]:
        if hasattr(self,"_gameuuid"):
            return self._gameuuid
        return None
    @property
    def gamegid(self)->Union[mafia.PLAYERID,None]:
        if hasattr(self,"_gamegid"):
            return self._gamegid
        return None    
    def gameLink(self,gameUUID:mafia.ROOMID,gid:mafia.PLAYERID):
        self._gameuuid=gameUUID
        self._gamegid=gid
