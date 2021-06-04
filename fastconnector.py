from __future__ import annotations
import sys
import json
from typing import Any, Dict, Set, Union
import datetime
import asyncio
import datetime
from tornado.escape import json_encode
import tornado.ioloop
import tornado.httpclient
import tornado.web
import tornado.auth
import tornado.template
import tornado.websocket
from traceback import format_exception

import roomHandler
import mafia


from starlette.websockets import WebSocket
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.endpoints import WebSocketEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

import fastapi
from fastapi import FastAPI
from fastapi import responses
from fastapi.params import Cookie
from fastapi.encoders import jsonable_encoder

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
                roomHandler.rooms.newRoom(self.data[0], mafia.PlayerRAW(self.nick,self.gid,self.ava), self.data[1])

            elif self.pck == "GetInfo":
                roomreply=roomHandler.rooms.stat()
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
    async def broadcast(self:Set[WebSocket], message:Union[dict,str]):
        input_coroutines=[]
        for client in self:
            input_coroutines+=client.send_json(message)
        await asyncio.gather(*input_coroutines, return_exceptions=True)

    async def multicast(self, message:Union[dict,str], rid:mafia.ROOMID):
        input_coroutines=[]
        for client in self:
            if client.gameuuid == rid:#from GameLink
                input_coroutines+=client.send_json(message)
        await asyncio.gather(*input_coroutines, return_exceptions=True)

    async def anycast(self, message:Union[dict,str],gid:mafia.PLAYERID):
        for client in self:
            if client.gamegid == gid:#from GameLink
                await client.send_json(json.dumps(message))
                return        
        raise mafia.PlayerNotFoundError(gid)
    

clients = Clients()


class WebsocketConnector(WebSocketEndpoint):
    async def on_connect(self):
        clients.add(self)
        print("WebSocket opened")

    async def on_receive(self, client:WebSocket,message:Dict):
        #client.
        await client.send_json({"pck":"conn_succ"})
        print(message)
        data = ClientPacket(message)
        if not data.validate():
            await client.close()#wrong data, go away spammer
            return
        ret = await data.consumePacket(self)
        print(ret)
        if ret:
            await client.send_json(ret)
        else:
            await client.send_json({"pck":"ack"})

    def on_pong(self, data: bytes) -> None:
        ret={
            "pck":"Ping",
            "timestamp":datetime.datetime.timestamp(datetime.datetime.now()),
            "players":len(clients),
            "rooms":len(roomHandler.rooms)
        }
        self.write_message(json.dumps(ret))
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
