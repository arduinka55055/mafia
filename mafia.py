from __future__ import annotations
import asyncio
from roomHandler import PermissionDeniedError
from typing import Callable, Dict, Generator, Iterable, List, Literal, Tuple, Union
from dataclasses import dataclass
import datetime
import random
import uuid
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from roomHandler import Room

PLAYERID = str
ROOMID = uuid.UUID
TARGETID = uuid.UUID
ROLES = {
    "m": "Мафія",
    "p": "Мирний",
    "d": "Доктор",
    "k": "Маніяк",
    "s": "Шериф",
    "g": "Путана"
}
TIMINGS = {
    "perform":40,
    "vote":40,
    "connect":20
} 

LOC = {
    "mafwin": "Мафія виграла",
    "mafdefeat": "Мирні перемогли мафію",
    "perform": "Ніч",
    "vote": "Голосування"
}
playersMin = 6


class PlayerNotFoundError(Exception):
    def __init__(self, UUID):
        self.uuid = UUID
        super().__init__(f"Error! Player with UUID:${self.uuid} not found!")

    def __repr__(self):
        return f"Error! Player with UUID:${self.uuid} not found!"


class PlayerRAW:
    # на просто id мы обосремося
    def __init__(self, name: str, gid: PLAYERID, avatar: str = None, *args, **kwargs):
        self.name = name
        self.id = gid  # ця штука заповнюється даними реєстрації на стороні серверу
        self.avatar = avatar  # only for other players. doesnt impact logic
    def __repr__(self):
        return "Player %s,id: %s" % (self.name,self.id)
    def __hash__(self):
        return hash(self.id)


class Player(PlayerRAW):
    def __init__(self, raw: PlayerRAW, role: str):
        self.__name = raw.name
        self.avatar = raw.avatar
        self.__id = raw.id  # ебкое ООП
        self.__role = role  # инкапсуляция в действии
        self.__killed = False
        self.__whore = False  # путана
        self.__uuid = uuid.uuid4()

    def __unicode__(self):
        return "Player:%s, Role:%s" % (self.name, self.role)

    def __str__(self):
        return "Player:%s, Role:%s" % (self.name, self.role)

    def __repr__(self):
        return "Player:%s, Role:%s" % (self.name, self.role)

    @property
    def role(self) -> str:
        return self.__role

    @property
    def roleNameFull(self) -> str:
        """
        Returns:
            str: [description of role in Russian]
        """
        return ROLES[self.__role]

    @property
    def id(self) -> PLAYERID:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def UUID(self) -> TARGETID:
        return self.__uuid

    @property
    def isKilled(self) -> bool:
        return self.__killed

    @property
    def isFucked(self) -> bool:
        return self.__whore

    @property
    def jsonable(self) -> dict:  # TODO: добавить role если игрок сдох
        ret={
            "name": self.name,
            "avatar": self.avatar,
            "id": str(self.UUID),
            "isKilled": self.isKilled
        }
        if self.isKilled:
            ret["role"]=self.roleNameFull
        return ret

    @property
    def jsonableP(self) -> dict:
        """It is reply to getme
        Returns:
            dict: id, role,desc(role name), isKilled
        """
        return {
            "id": str(self.UUID),
            "role": self.__role,
            "desc": self.roleNameFull,
            "isKilled": self.isKilled
        }

    @property
    def isPerformable(self) -> bool:
        """
        Returns True if gamer can perform (if gamer is not regular person)
        """
        return False if self.__role == 'p' else True

    def setKilled(self, state: bool):
        self.__killed = state

    def setWhore(self, state: bool):
        self.__whore = state

    def checkUser(self, id, role) -> bool:
        return True if (self.id == id and self.role == role) else False

    def canDo(self, id, role) -> bool:  # TODO:обрезание
        return True if (not self.__whore and self.checkUser(id, role)) else False


class Players(object):
    """
    Player container with sweet methods
    """

    def __init__(self, data: set[PlayerRAW]):
        cardlist = [
            ['m', 'p', 'p', 'p', 'p', 's'],  # 6
            ['m','p','s','k','d','m','g'],#debug only!
            #['m', 'm', 'p', 'p', 'p', 'p', 's'],
            ['m', 'm', 'p', 'p', 'p', 'p', 'p', 's'],
            ['m', 'm', 'p', 'p', 'p', 'p', 'p', 's', 'k'],
            ['m', 'm', 'p', 'p', 'p', 'p', 'p', 'p', 's', 'k'],  # 10
            ['m', 'm', 'p', 'p', 'p', 'p', 'p', 'p', 's', 'k', 'd'],
            ['m', 'm', 'm', 'p', 'p', 'p', 'p', 'p', 'p', 's', 'k', 'd'],
            ['m', 'm', 'm', 'p', 'p', 'p', 'p', 'p', 'p', 'p', 's', 'k', 'd'],
            ['m', 'm', 'm', 'p', 'p', 'p', 'p', 'p',
                'p', 'p', 's', 'k', 'd', 'g'],  # 14
            # Mafia Person Doctor Killer Sheriff Girl
            # x means killed
        ]
        self.players: set[Player] = set()
        choosed = cardlist[len(data)-playersMin]
        random.shuffle(choosed)
        for x, y in zip(data, choosed):
            self.players.add(Player(x, y))

    @property
    def jsonable(self) -> List[Dict]:
        return [x.jsonable for x in self.players]

    def getMafias(self) -> Generator[Player, None, None]:
        for player in self.players:
            if player.isKilled:pass
            elif player.role == "m":
                yield player

    def getMafiasCount(self) -> int:
        return len(list(self.getMafias()))

    def getGood(self) -> Generator[Player, None, None]:
        for player in self.players:
            if player.isKilled:pass
            elif player.role in ["p", "s", "d", "g"]:
                yield player
    def getAlive(self) -> Generator[Player, None, None]:
        for player in self.players:
            if not player.isKilled:
                yield player
    def getAliveCount(self) -> int:
        return len(list(self.getAlive()))
    
    def getGoodCount(self) -> int:
        return len(list(self.getGood()))

    def getPerformable(self,countKilled=False) -> Generator[Player, None, None]:
        for player in self.players:
            if player.isKilled and not countKilled:pass
            elif player.role in ['m', 's', 'k', 'd', 'g']:
                yield player

    def getPerformableCount(self,countKilled=False) -> int:
        return len(list(self.getPerformable(countKilled)))

    def getByTID(self, UUID: TARGETID) -> Player:
        for player in self.players:
            if str(player.UUID) == str(UUID):
                return player
        raise PlayerNotFoundError(UUID)

    def getByGID(self, UUID: PLAYERID) -> Player:
        for player in self.players:
            if str(player.id) == str(UUID):
                return player
        raise PlayerNotFoundError(UUID)

    def getByRole(self, role: str) -> Player:
        for player in self.getPerformable(countKilled=True):
            if player.role == role:
                return player
        raise PlayerNotFoundError(role)

    def kill(self, player: Player):
        player.setKilled(True)

    def heal(self, player: Player):
        player.setKilled(False)

    def whore(self, player: Player):
        player.setWhore(True)


class Doings(Players):
    def do_mafkill(self, targets: List[TARGETID]):
        # все засыпают, просипается мафия. кого убить /////////////////////////////////////////////////////////////////////////////////////////////////////
        if self.getMafiasCount() > 1:  # голосовалка, не соблазнят компанию
            random.shuffle(targets)
        elif next(self.getMafias()).isFucked:
            return
        self.kill(self.getByTID(targets[0]))

    def do_sherif(self, target: TARGETID) -> str:
        # мафия сделала вибор, просипается шериф ////////////////////////////////////////////////////////////////////////////////////////////////////////////
        if self.getByRole("s").isFucked:
            return "BLOCKED"
        return self.getByTID(target).role

    def do_killer(self, target: TARGETID):
        # просипается маньяк
        if self.getByRole("k").isFucked:
            return
        self.kill(self.getByTID(target))

    def do_doctor(self, target: TARGETID):
        if self.getByRole("d").isFucked:
            return
        self.heal(self.getByTID(target))

    def do_girl(self, target: TARGETID):
        # а теперь путана, она действует всегда
        self.whore(self.getByTID(target))

    @property
    def isFinished(self) -> Union[bool, None]:
        """
        Returns:
            False if mafia won, True if players won, None if game is still available
        """
        if self.getMafiasCount() == 0:
            return False
        elif self.getGoodCount() == 0:
            return True
        else:
            return None


@dataclass
class PerformOne:
    player: Player
    targetid: TARGETID


class PerformResult:
    sherifflock=False
    def __init__(self):  # List потомушо вонючая мафия может выбрать ≥1 игрока
        self.__data: Dict[str, Union[List[TARGETID]]] = {}

    def set(self, value: PerformOne):
        if value.player.role in self.__data:
            self.__data[value.player.role].append(value.targetid)
        else:
            self.__data[value.player.role] = [value.targetid]

    def __getitem__(self, role: str) -> Union[List[TARGETID], None]:
        return self.__data.get(role)

    def __len__(self) -> int:
        return len(self.__data)


class Timer:
    begin: float
    duration: int

    def currtime(self) -> float:
        "i hate long names"
        return datetime.datetime.timestamp(datetime.datetime.now())

    def start(self, duration: int) -> Timer:
        """duration: seconds"""
        self.begin = self.currtime()
        self.duration = duration
        return self
    @property
    def expiredate(self):
        return self.begin+self.duration
    @property
    def isExpired(self) -> bool:
        if self.currtime() >= self.expiredate:
            return True
        return False

    def onExpire(self, callback: Callable):
        asyncio.ensure_future(self.aonExpire(callback))

    async def aonExpire(self, callback: Callable):
        await asyncio.sleep(self.duration + (self.currtime()-self.begin))
        callback()


class Game(Doings):
    __result:Union[PerformResult,None]
    __vote:Union[Dict,None]
    __timer:Timer
    __status:Union[Literal["perform"],Literal["vote"],Literal["pause"]]
    @property
    def status(self)->Tuple[Union[Literal["perform"],Literal["vote"],Literal["pause"]],int]:
        return self.__status,int(self.__timer.expiredate)
    @property
    def result(self)->PerformResult:
        if self.__result==None:
            raise PermissionDeniedError("not allowed perform")
        return self.__result
    @property
    def vote(self)->Dict:
        if self.__vote==None:
            raise PermissionDeniedError("not allowed vote")
        return self.__vote

    def performData(self, gid: PLAYERID, pid: TARGETID)->Union[None,str]:
        """returns role for sheriff. """
        self.result.set(PerformOne(self.getByGID(gid), pid))
        if self.getByGID(gid).role=="s" and not self.result.sherifflock:
            self.result.sherifflock=True
            return self.do_sherif(pid)

    def voteData(self, gid: PLAYERID, pid: TARGETID):
        self.vote[gid] = pid

    async def getPerformData(self):
        self.__status="perform"
        self.__timer=Timer().start(TIMINGS["perform"])
        await self.__room.send({"msg": "Update"})
        self.__result = PerformResult()
        pc = self.getPerformableCount()
        while len(self.result) < pc and not self.__timer.isExpired:
            await asyncio.sleep(1)  # TODO: зафигачить таймер
        return self.result

    async def getVoteData(self):
        self.__status="vote"
        self.__timer=Timer().start(TIMINGS["vote"])
        await self.__room.send({"msg": "Update"})
        self.__vote = dict()
        while len(self.vote.values()) < self.getAliveCount() and not self.__timer.isExpired:
            await asyncio.sleep(1)  # TODO: зафигачить таймер
        return self.vote

    def parsePerform(self):
        data: PerformResult = self.result
        if data["g"]:
            self.do_girl(data["g"][0])
        if data["k"]:
            self.do_killer(data["k"][0])

        mafias = data["m"]
        if mafias != None:  # TODO:Settings
            self.do_mafkill(mafias)
        if data["d"]:
            self.do_doctor(data["d"][0])

    def parseVote(self):
        values_list = list(self.vote.values())
        if len(values_list)<=0:
            return
        self.kill(self.getByTID(max(set(values_list), key=values_list.count)))

    def finishCheck(self):
        if self.isFinished != None:
            self.__room.finish(self.isFinished)

    async def startMainloop(self, room: Room):
        self.__room = room

        
        super(Game, self).__init__(self.__room.players)
        # room.познакомитьИгроков()
        while self.isFinished == None:
            await room.checkConnectivity()
            await room.send({"msg": "DoPerform"})
            result = await self.getPerformData()
            print(result)
            self.parsePerform()
            self.__result=None
            self.finishCheck()
            
            await room.send({"msg": "DoVote"})
            result = await self.getVoteData()
            print(result)
            self.parseVote()
            self.__vote=None
            self.finishCheck()
