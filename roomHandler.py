
from __future__ import annotations
import uuid
import asyncio
from typing import Any, Set, Union
import wsconnector
import mafia

class RoomNotFoundError(Exception):
    def __init__(self,UUID:mafia.ROOMID):
        self.uuid=UUID
        super().__init__("Error! Room with RID:${self.uuid} not found!")

    def __repr__(self):
        return "Error! Room with RID:${self.uuid} not found!"

class PermissionDeniedError(Exception):
    def __init__(self,UUID:mafia.PLAYERID,role=None):
        self.uuid=UUID
        self.role=role
        super().__init__("Error! Player ${self.uuid} can't do that!")

    def __repr__(self):
        return "Error! Player ${self.uuid} can't do that!"

class NoEnoughPlayersError(Exception):
    def __init__(self,UUID,count):
        self.uuid=UUID
        self.count=count
        super().__init__("Error! No enough players in ${self.uuid} (${self.count}) to start!")

    def __repr__(self):
        return "Error! No enough players in ${self.uuid} (${self.count}) to start!"

class ServerPizdecError(Exception):
    def __init__(self):
        super().__init__("Server Error!")

    def __repr__(self):
        return "Server Error!"

class Rooms(set):
    def fromUUID(self, UUID)->Room:
        for room in self:
            return room
        raise RoomNotFoundError(UUID)

    def newRoom(self,*args):
        room=Room(*args)
        self.add(room)

    def stat(self:Set[Room]):
        data={"pck":"RoomData","rooms":[]}
        for room in self:
            data["rooms"].append(room.stat())
        return data

    def purgeIter(self):
        for x in self:
            if len(x.players)<=0:
                del x
        
rooms = Rooms()

class Room:
    @property
    def UUID(self)->mafia.ROOMID:
        return self.__uuid
    @property
    def players(self)->set[mafia.PlayerRAW]:
        return self.__players
    @property
    def game(self)->Union[mafia.GameMainloop,None]:
        return self.__game
    @property
    def gamers(self)->set[mafia.Player]:
        return self.__game.players

    def __init__(self, name,ownergid:mafia.PLAYERID, playersLimit):
        rooms.purgeIter()
        self.name=name
        self.__uuid = uuid.uuid1()
        self.ownergid = ownergid
        self.playersLimit = playersLimit
        self.__players: Set[mafia.PlayerRAW] = set()
        self.__started=False
        self.__game=None
        rooms.add(self)

    def __repr__(self):
        return "Room %s,has %s players" % (self.name,len(self.__players))

    def __del__(self):
        rooms.remove(self)

    def purgeIter(self):
        if len(self.__players)<=0:
            del self
    @property
    def isStarted(self):
        return self.__started

    def join(self, player: mafia.PlayerRAW):
        if not player in self.__players:
            self.__players.add(player)

    def leave(self, gid:mafia.PLAYERID):
        self.__players.remove(self.playerByGid(gid))
        if self.ownergid == gid:
            rooms.remove(self)
            

    def playerByGid(self, gid:mafia.PLAYERID)->mafia.PlayerRAW:
        for player in self.__players:
            if player.id == gid:
                return player
        raise mafia.PlayerNotFoundError(gid)

    def stat(self):
        return {
            "rid":str(self.UUID),
            "name":self.name,
            "isStarted":self.isStarted,
            "players":[[x.name,x.avatar] for x in self.__players]}
        
    async def start(self, gid:mafia.PLAYERID):
        if self.ownergid == gid:
            if len(self.__players) >= mafia.playersMin:
                self.__started=True
                self.__game=mafia.GameMainloop(self.__players)
                asyncio.ensure_future(self.__game.startMainloop(self))
                await wsconnector.clients.broadcast({"pck": "GameStarted", "rid": str(self.UUID)})
                return
            else:
                raise NoEnoughPlayersError(self.UUID,len(self.__players))    
        raise PermissionDeniedError(gid)

    async def send(self,data:dict):
        data["pck"]="GameCast"
        await wsconnector.clients.multicast(data,self.UUID)

    async def sendany(self,data:dict,player:mafia.PLAYERID):
        data["pck"]="GameCast"
        await wsconnector.clients.anycast(data,player)

    def performRole(self,gid:mafia.PLAYERID,pid:mafia.TARGETID):
        self.game.performData(gid,pid)