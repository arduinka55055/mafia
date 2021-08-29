
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
    def __init__(self,role=None):
        self.role=role
        super().__init__("Error! Player can't do that!")

    def __repr__(self):
        return "Error! Player can't do that!"

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
        return str(room.UUID)

    def stat(self:Set[Room],gid):
        data={"pck":"RoomData","rooms":[]}
        for room in self:
            data["rooms"].append(room.stat(gid))
        return data

    def purgeIter(self):
        removed=[]
        for x in self:
            if len(x.players)<=0 and not x.isStarted:
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
        if player!=None and room!=None:
            room.leave(player)

                    
        
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
        if self.gamers!=None:
            for x in self.gamers:
                if x.id==id:
                    return True
        return False

    @property
    def isStarted(self):
        return self.__started

    def join(self, player: mafia.PlayerRAW):
        if self.isStarted:
            if self.hasPlayer(player.id):
                self.players.add(player)
                print("reconnected player!",len(self.players))
        else:
            if not self.hasPlayer(player.id):
                rooms.kick(player.id)
                rooms.purgeIter()
                self.players.add(player)

    def leave(self, player:mafia.PlayerRAW):
        self.players.remove(player)
        if not self.isStarted:
            if self.ownergid == player.id:
                if len(self.players)>=1:
                    self.ownergid=next(iter(self.players)).id
                else:
                    rooms.remove(self)
            try:
                self.playerByGid(self.ownergid)
            except mafia.PlayerNotFoundError:
                self.ownergid=next(iter(self.players)).id
        
        

    def playerByGid(self, gid:mafia.PLAYERID)->mafia.PlayerRAW:
        for player in self.players:
            if player.id == gid:
                return player
        if self.gamers!=None:
            for player in self.gamers:
                if player.id == gid:
                    return mafia.PlayerRAW(player.name,player.id,player.avatar)
        raise mafia.PlayerNotFoundError(gid)

    def stat(self,gid):
        return {
            "rid":str(self.UUID),
            "name":self.name,
            "isStarted":self.isStarted,
            "maxplayers":self.playersLimit,
            "areyouowner":self.ownergid==gid,
            "players":[[x.name,x.avatar,self.ownergid==x.id,x.id==gid] for x in self.players]}
        
    async def checkConnectivity(self):
        await asyncio.sleep(2)
        self._players=set()
        while 1:
            if len(self.players)==len(self.game.players):
                return
            await asyncio.sleep(1)
        #TODO:
    async def start(self, gid:mafia.PLAYERID):
        if self.ownergid == gid:
            if len(self.players) >= mafia.playersMin:
                self.__started=True
                self.__game=mafia.Game(self.players)
                #self.__players=set()
                asyncio.ensure_future(self.__game.startMainloop(self))
                await wsconnector.clients.broadcast({"pck": "GameStarted", "rid": str(self.UUID)})
                return
            else:
                raise NoEnoughPlayersError(self.UUID,len(self.players))    
        raise PermissionDeniedError()
    def finish(self,data):
        self.__game=None
        self.__started=False
        asyncio.ensure_future(self.send({"msg": "GameFinished", "data": [
                                  data, mafia.LOC["mafwin" if False else "mafdefeat"]]}))
    async def send(self,data:dict):
        data["pck"]="GameCast"
        await wsconnector.clients.multicast(data,self.UUID)

    async def sendto(self,data:dict,player:mafia.PLAYERID):
        data["pck"]="GameCast"
        await wsconnector.clients.anycast(data,player)

    async def sendchat(self,player:mafia.PlayerRAW,txt:str):
        await self.send({
            "pck":"GameCast","msg":"Chat","data":txt,
            "nick":player.name,"ava":player.avatar
        })
    async def performRole(self,gid:mafia.PLAYERID,pid:mafia.TARGETID):
        data={"msg":"Error","spec":"PermissionDenied"}
        if self.game.getByGID(gid).isPerformable:
            if not self.game.getByGID(gid).isKilled:
                if not self.game.getByTID(pid).isKilled:
                    ret=self.game.performData(gid,pid)
                    if ret:
                        data={"msg": "Sheriff", "player":pid,"data": [ret, mafia.ROLES[ret]]}
                    else:
                        return None
                else:
                    data={"msg":"Error","spec":"Пж не насилуйте труп!"}
            else:
                data={"msg":"Error","spec":"You're dead!"}
        data["pck"]="GameCast"
        return data

    async def doVote(self,gid:mafia.PLAYERID,pid:mafia.TARGETID):
        data={"msg":"Error","spec":"You're dead!"}
        if not self.game.getByGID(gid).isKilled:
            if not self.game.getByTID(pid).isKilled:
                self.game.voteData(gid,pid)
                return None
            else:
                data={"msg":"Error","spec":"Пж не насилуйте труп!"}
        data["pck"]="GameCast"
        return data