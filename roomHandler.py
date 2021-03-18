import uuid
import asyncio
from typing import Any, Set, Union

import mafia

Room=Any
class Rooms(set):
    def fromUUID(self, UUID)->Union[Room,None]:
        for room in self:
            return room
        return None
    def hasRoom(self,uuid) -> bool:
        if self.fromUUID(uuid)==None:
            return False
        else:
            return True
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
        self.players.add(player)

    def leave(self, gid):
        if self.ownergid == gid:
            del self
        else:
            self.players.remove(self.playerByGid(gid))

    def playerByGid(self, gid)->mafia.PlayerRAW:
        for player in self.players:
            if player.id == gid:
                return player
        raise mafia.PlayerNotFoundError(gid)
    def getUUID(self):
        return self.__uuid
    def stat(self):
        return {"name":self.name,"players":[[x.name,x.avatar] for x in self.players]}
        
    def start(self, gid) -> bool:
        if self.ownergid == gid:
            if len(self.players) > mafia.playersMin:
                self.__started=True
                self.__game=mafia.GameMainloop(self.players)
                asyncio.ensure_future(self.__game.startMainloop())
        return False
    def performRole(self,gid):
        pass
        #self.game