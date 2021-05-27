
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
        removed=[]
        for x in self:
            if len(x.players)<=0:
                removed.append(x)
        for x in removed:
            self.remove(x)
    def kick(self:Set[Room],id:mafia.PLAYERID):
        player=None
        room=None
        for x in self:
            for p in x.players:
                if p.id==id:
                    player=p
                    room=x
                    break
        if player!=None:
            room.players.remove(player)

                    
        
rooms = Rooms()

class Room:
    @property
    def UUID(self)->mafia.ROOMID:
        return self.__uuid
    @property
    def players(self)->set[mafia.PlayerRAW]:
        return self.__players
    @property
    def game(self)->mafia.Game:
        if self.__game==None:
            raise GameNotStartedError(self.UUID)
        return self.__game
    @property
    def gamers(self)->Union[set[mafia.Player],None]:
        if self.__game != None:
            return self.__game.players
        else:
            return None
    def __init__(self, name,owner:mafia.PlayerRAW, playersLimit):
        rooms.kick(owner.id)
        rooms.purgeIter()
        self.name=name
        self.__uuid = uuid.uuid4()
        self.ownergid = owner.id
        self.playersLimit = playersLimit
        if playersLimit<mafia.playersMin:
            raise NoEnoughPlayersError(self.__uuid,playersLimit)
        self.__players: Set[mafia.PlayerRAW] = set()
        self.__players.add(owner)
        self.__started=False
        self.__game=None
        rooms.add(self)

    def __repr__(self):
        return "Room %s,has %s players" % (self.name,len(self.players))

    def __del__(self):
        rooms.remove(self)

    def hasPlayer(self,id:mafia.PLAYERID):
        for x in self.players:
            if x.id==id:
                return True
        if self.__started:
            for x in self.gamers:
                if x.id==id:
                    return True
        return False

    @property
    def isStarted(self):
        return self.__started

    def join(self, player: mafia.PlayerRAW):
        if not self.hasPlayer(player.id):
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
            "maxplayers":self.playersLimit,
            "players":[[x.name,x.avatar] for x in self.players]}
        
    async def start(self, gid:mafia.PLAYERID):
        if self.ownergid == gid:
            if len(self.players) >= mafia.playersMin:
                self.__started=True
                self.__game=mafia.Game(self.players)
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
            if not self.game.getByGID(gid).isKilled:
                if not self.game.getByTID(pid).isKilled:
                    self.game.performData(gid,pid)
                else:
                    data={"pck":"GameCast","msg":"Error","spec":"Пж не насилуйте труп!"}
                    await wsconnector.clients.anycast(data,gid)
            else:
                data={"pck":"GameCast","msg":"Error","spec":"You're dead!"}
                await wsconnector.clients.anycast(data,gid)
        else:
            data={"pck":"GameCast","msg":"Error","spec":"PermissionDenied"}
            await wsconnector.clients.anycast(data,gid)