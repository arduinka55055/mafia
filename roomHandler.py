import uuid
import asyncio
from typing import Any, Union

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

rooms = Rooms()

class Room:
    def __init__(self, ownergid, playersLimit):
        self.__uuid = uuid.uuid1()
        self.ownergid = ownergid
        self.playersLimit = playersLimit
        self.players = set()
        self.__started=False
        self.__game=None
        rooms.add(self)

    def __del__(self):
        rooms.remove(self)
    def isStarted(self):
        return self.__started
    def join(self, player: mafia.PlayerRAW):
        self.players.add(player)

    def leave(self, gid):
        if self.ownergid == gid:
            del self
        else:
            self.players.remove(self.playerByGid(gid))

    def playerByGid(self, gid):
        for player in self.players:
            if player.id == gid:
                return player
        return None
    def getUUID(self):
        return self.__uuid
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