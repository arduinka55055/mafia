from __future__ import annotations
import os
import io
import sys
import html
import json
import random
from typing import Any, Dict, Set, Union
import datetime
import urllib
import asyncio
import datetime
import aiomysql
from starlette.websockets import WebSocket
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
        try:
            self.nick=html.escape(self.nick)
            self.ava=html.escape(self.ava)
            return False if self.gid == None or self.nick == None else (self.ava[0:8]=="https://" )
        except:
            return False
    def getRoom(self)->roomHandler.Room:
        return roomHandler.rooms.fromUUID(self.game)

    async def consumePacket(self,ws:WebSocket) -> Union[Dict, None]:
        try:
            if self.pck == "MakeRoom":
                # id:12345
                roomreply = {}
                roomreply["id"]=roomHandler.rooms.newRoom(self.data[0], mafia.PlayerRAW(self.nick,self.gid,self.ava), self.data[1])
                roomreply["pck"]="MadeRoom"
                return roomreply
            elif self.pck == "GetInfo":
                roomreply=roomHandler.rooms.stat(self.gid)
                roomreply["pck"]="Info"
                roomreply["players"]=len(clients)
                roomreply["timestamp"]=datetime.datetime.timestamp(datetime.datetime.now())
                return roomreply

            elif self.pck == "GetTargets":
                roomreply={"pck":"InfoT","data":[]}
                roomreply["data"]=list(self.getRoom().game.jsonable)
                return roomreply
                

            elif self.pck == "Me":
                session=self.getRoom()
                if session.isStarted:
                    roomreply=session.game.getByGID(self.gid).jsonableP
                    roomreply['pck']="You"
                    return roomreply
                else:
                    raise roomHandler.GameNotStartedError(self.game)

            elif self.pck == "ClientHello":
                session=self.getRoom()
                player=mafia.PlayerRAW(self.nick,self.gid,self.ava)
                session.join(player)
                ws.session["rid"]=session.UUID
                ws.session["gid"]=self.gid
                return {"pck":"ServerHello"}

            elif self.pck == "Reconnect":
                session=self.getRoom()
                ws.session["rid"]=session.UUID
                ws.session["gid"]=self.gid
                return {"pck":"Success"}
                
            elif self.pck == "StartGame":
                room = self.getRoom()
                await room.start(self.gid)
                return {"pck":"GameStartSuccess"}

            elif self.pck == "Perform":
                room = self.getRoom()
                return  await room.performRole(self.gid,self.target)

            elif self.pck == "Vote":
                room = self.getRoom()
                return await room.doVote(self.gid,self.target)

            elif self.pck == "Chat":
                room = self.getRoom()
                await room.sendchat(mafia.PlayerRAW(self.nick,self.gid,self.ava),self.data)

            elif self.pck == "GameStat":
                room = self.getRoom()
                return {"pck":"GameStat", "state":mafia.LOC[room.game.status[0]],"timer":room.game.status[1]}

        except mafia.PlayerNotFoundError:
            return {"pck":"Error","id":self.target,"msg":"PlayerNotFound"}

        except roomHandler.RoomNotFoundError:
            return {"pck":"Error","id":self.game,"msg":"RoomNotFound"}

        except roomHandler.NoEnoughPlayersError:
            return {"pck":"Error","msg":"GameStartError","spec":"NoEnoughPlayers"}
        
        except roomHandler.GameNotStartedError:
            return {"pck":"Error","msg":"GameNotStarted","spec":"GameNotStarted"}

        except roomHandler.PermissionDeniedError:
            return {"pck":"Error","msg":"GameStartError","spec":"PermissionDenied"}

        except:
            err=sys.exc_info()
            shit=''.join(format_exception(*err))
            shit=shit.replace('"','\"').replace("'","\'")
            return {"pck":"Error","msg":"ServerPizdecError","spec":"Пизда Серву!" +shit}
class Clients(set):
    async def broadcast(self:Set[WebSocket], message:Union[dict,str]):
        input_coroutines=[]
        for client in self:
            input_coroutines.append(client.send_json(message))
        await asyncio.gather(*input_coroutines, return_exceptions=True)

    async def multicast(self:Set[WebSocket], message:Union[dict,str], rid:mafia.ROOMID):
        input_coroutines=[]
        for client in self:
            if client.session.get("rid","") == rid:#from GameLink
                input_coroutines.append(client.send_json(message))
        await asyncio.gather(*input_coroutines, return_exceptions=True)

    async def anycast(self:Set[WebSocket], message:Union[dict,str],gid:mafia.PLAYERID):
        for client in self:
            if client.session["gid"] == gid:#from GameLink
                await client.send_json(json.dumps(message))
                return        
        raise mafia.PlayerNotFoundError(gid)
    def remove(self, ws: WebSocket) -> None:
        #roomHandler.rooms.kick(ws.session["gid"])
        #roomHandler.rooms.purgeIter()
        return super().remove(ws)
    
def disconnect(gid:mafia.PLAYERID):
    roomHandler.rooms.kick(gid)
    roomHandler.rooms.purgeIter()
clients = Clients()