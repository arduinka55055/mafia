
from __future__ import annotations
import uuid
import asyncio
from typing import Any, Set
import mafia

class RoomNotFoundError(Exception):
    def __init__(self,UUID):
        self.uuid=UUID
        super().__init__("Error! Room with RID:${self.uuid} not found!")

    def __repr__(self):
        return "Error! Room with RID:${self.uuid} not found!"

class PermissionDeniedError(Exception):
    def __init__(self,UUID,role=None):
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
    def __init__(self, name,ownergid, playersLimit):
        rooms.purgeIter()
        self.name=name
        self.__uuid = uuid.uuid1()
        self.ownergid = ownergid
        self.playersLimit = playersLimit
        self.players: Set[mafia.PlayerRAW] = set()
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

    def isStarted(self):
        return self.__started

    def join(self, player: mafia.PlayerRAW):
        if not player in self.players:
            self.players.add(player)

    def leave(self, gid):
        self.players.remove(self.playerByGid(gid))
        if self.ownergid == gid:
            rooms.remove(self)
            

    def playerByGid(self, gid)->mafia.PlayerRAW:
        for player in self.players:
            if player.id == gid:
                return player
        raise mafia.PlayerNotFoundError(gid)

    def getUUID(self):
        return self.__uuid

    def stat(self):
        return {"rid":str(self.getUUID()),"name":self.name,"players":[[x.name,x.avatar] for x in self.players]}
        
    def start(self, gid):
        if self.ownergid == gid:
            if len(self.players) >= mafia.playersMin:
                self.__started=True
                self.__game=mafia.GameMainloop(self.players)
                asyncio.ensure_future(self.__game.startMainloop())
                return
            else:
                raise NoEnoughPlayersError(self.getUUID(),len(self.players))    
        raise PermissionDeniedError(self.getUUID())

        
    def performRole(self,gid):
        pass
        #self.game