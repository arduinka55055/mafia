
from __future__ import annotations
import uuid
import asyncio
from typing import Any, Set, Union
import wsconnector
import mafia

class RoomNotFoundError(Exception):
    def __init__(self,UUID:Union[mafia.ROOMID,str]):
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

class GameNotStartedError(Exception):
    def __init__(self,RID:mafia.ROOMID):
        self.uuid=RID
        super().__init__("Error! Room with UUID:${self.uuid}, game not started!")
    def __repr__(self):
        return "Error! Room with UUID:${self.uuid}, game not started!"

class ServerPizdecError(Exception):
    def __init__(self):
        super().__init__("Server Error!")

    def __repr__(self):
        return "Server Error!"

class Rooms(set):
    def fromUUID(self, UUID:Union[str,mafia.ROOMID])->Room:
        for room in self:
            if str(room.UUID)==str(UUID):
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
    def game(self)->mafia.GameMainloop:
        if self.__game==None:
            raise GameNotStartedError(self.UUID)
        return self.__game
    @property
    def gamers(self)->set[mafia.Player]:
        return self.__game.players

    def __init__(self, name,ownergid:mafia.PLAYERID, playersLimit):
        rooms.purgeIter()
        self.name=name
        self.__uuid = uuid.uuid4()
        self.ownergid = ownergid
        self.playersLimit = playersLimit
        self.__players: Set[mafia.PlayerRAW] = set()
        self.__started=False
        self.__game=None
        rooms.add(self)

    def __repr__(self):
        return "Room %s,has %s players" % (self.name,len(self.players))

    def __del__(self):
        rooms.remove(self)

    def purgeIter(self):
        if len(self.players)<=0:
            del self
    @property
    def isStarted(self):
        return self.__started

    def join(self, player: mafia.PlayerRAW):
        if not player in self.players:
            self.players.add(player)

    def leave(self, gid:mafia.PLAYERID):
        self.players.remove(self.playerByGid(gid))
        if self.ownergid == gid:
            rooms.remove(self)
            

    def playerByGid(self, gid:mafia.PLAYERID)->mafia.PlayerRAW:
        for player in self.players:
            if player.id == gid:
                return player
        raise mafia.PlayerNotFoundError(gid)

    def stat(self):
        return {
            "rid":str(self.UUID),
            "name":self.name,
            "isStarted":self.isStarted,
            "players":[[x.name,x.avatar] for x in self.players]}
        
    async def start(self, gid:mafia.PLAYERID):
        if self.ownergid == gid:
            if len(self.players) >= mafia.playersMin:
                self.__started=True
                self.__game=mafia.GameMainloop(self.players)
                asyncio.ensure_future(self.__game.startMainloop(self))
                await wsconnector.clients.broadcast({"pck": "GameStarted", "rid": str(self.UUID)})
                return
            else:
                raise NoEnoughPlayersError(self.UUID,len(self.players))    
        raise PermissionDeniedError(gid)

    async def send(self,data:dict):
        data["pck"]="GameCast"
        await wsconnector.clients.multicast(data,self.UUID)

    async def sendto(self,data:dict,player:mafia.PLAYERID):
        data["pck"]="GameCast"
        await wsconnector.clients.anycast(data,player)

    async def performRole(self,gid:mafia.PLAYERID,pid:mafia.TARGETID):
        if self.game.getByGID(gid).isPerformable:
            self.game.performData(gid,pid)
        else:
            data={"pck":"GameCast","msg":"Error","spec":"PermissionDenied"}
            await wsconnector.clients.anycast(data,gid)