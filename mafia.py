from __future__ import annotations
import asyncio
from typing import Dict, Generator, Iterable, List, Literal, Union
from dataclasses import dataclass
import random
import uuid
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from roomHandler import Room

PLAYERID=str
ROOMID=uuid.UUID
TARGETID=uuid.UUID
ROLES={
    "m":"Мафия",
    "p":"Гражданин",
    "d":"Доктор",
    "k":"Маньяк",
    "s":"Шериф",
    "g":"Путана"
}
playersMin = 6

class PlayerNotFoundError(Exception):
    def __init__(self,UUID):
        self.uuid=UUID
        super().__init__("Error! Player with UUID:${self.uuid} not found!")
    def __repr__(self):
        return "Error! Player with UUID:${self.uuid} not found!"

class PlayerRAW(dict):
    def __init__(self, name: str, gid: PLAYERID, avatar: str=None,*args, **kwargs):  # на просто id мы обосремося
        self.name = name
        self.id = gid  # ця штука заповнюється даними реєстрації на стороні серверу
        self.avatar = avatar #only for other players. doesnt impact logic
    def items(self):
        return dict()

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
        return "x" if self.__killed else self.__role
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
        return True if self.role=="x" else False

    @property
    def isFucked(self) -> bool:
        return self.__whore
    @property
    def jsonable(self) -> dict:
        return {
            "name":self.name,
            "avatar":self.avatar,
            "id":str(self.UUID),
            "isKilled":self.isKilled
        }
    @property
    def jsonableP(self) -> dict:
        """It is reply to getme
        Returns:
            dict: id, role,desc(role name), isKilled
        """
        return {
            "id":str(self.UUID),
            "role":self.__role,
            "desc":self.roleNameFull,
            "isKilled":self.isKilled
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

    def canDo(self, id, role) -> bool:#TODO:обрезание
        return True if (not self.__whore and self.checkUser(id, role)) else False
    

class Players(object):
    """
    Player container with sweet methods
    """

    def __init__(self, data: set[PlayerRAW]):
        cardlist = [
            # ['m','p','s','k','d','m','g'],#debug only!
            ['m', 'p', 'p', 'p', 'p', 's'],  # 6
            ['m', 'm', 'p', 'p', 'p', 'p', 's'],
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
        self.players:set[Player]=set()
        choosed = cardlist[len(data)-playersMin]
        random.shuffle(choosed)
        for x, y in zip(data, choosed):
            self.players.add(Player(x, y))
    @property
    def jsonable(self)->List[Dict]:
        return [x.jsonable for x in self.players]

    def getMafias(self)->Generator[Player,None,None]:
        for player in self.players:
            if player.role == "m":
                yield player

    def getMafiasCount(self) -> int:
        counter = 0
        for _ in self.getMafias():
            counter += 1
        return counter

    def getGood(self)->Generator[Player,None,None]:
        for player in self.players:
            if player.role in ["p", "s", "d", "g"]:
                yield player

    def getGoodCount(self) -> int:
        counter = 0
        for _ in self.getGood():
            counter += 1
        return counter
    def getPerformable(self)->Generator[Player,None,None]:
        for player in self.players:
            if player.role in ['m','s','k','d','g']:
                yield player
    def getPerformableCount(self)->int:
        counter = 0
        for _ in self.getPerformable():
            counter += 1
        return counter
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
    def getByRole(self, role:str) -> Union[Player,None]:
        for player in self.getPerformable():
            if player.role==role:
                return player
    def kill(self, player: Player):
        player.setKilled(True)

    def heal(self, player: Player):
        player.setKilled(False)

    def whore(self, player: Player):
        player.setWhore(True)


class Doings(Players):
    def do_mafkill(self, targets:List[TARGETID]):
        # все засыпают, просипается мафия. кого убить /////////////////////////////////////////////////////////////////////////////////////////////////////
        if self.getMafiasCount() > 1:  # голосовалка, не соблазнят компанию
            random.shuffle(targets)
        elif next(self.getMafias()).isFucked:
            return
        self.kill(self.getByTID(targets[0]))

    def do_sherif(self, target:TARGETID) -> str:
        # мафия сделала вибор, просипается шериф ////////////////////////////////////////////////////////////////////////////////////////////////////////////
        return self.getByTID(target).role

    def do_killer(self, target:TARGETID):
        # просипается маньяк
        if self.getByRole("k").isFucked:
            return
        self.kill(self.getByTID(target))

    def do_doctor(self, target:TARGETID):
        if self.getByRole("d").isFucked:
            return
        self.heal(self.getByTID(target))

    def do_girl(self, target:TARGETID):
        # а теперь путана, она действует всегда
        self.whore(self.getByTID(target))
    @property
    def isFinished(self)->Union[bool,None]:
        """
        Returns:
            False if mafia won, True if players won, None if game is still available
        """
        if self.getMafiasCount()==0:
            return True
        elif self.getGoodCount()==0:
            return False
        else:
            return None
@dataclass
class PerformOne:
    player: Player
    targetid: TARGETID

class PerformResult:
    def __init__(self):#List потомушо вонючая мафия может выбрать ≥1 игрока
        self.__data:Dict[str,Union[List[TARGETID], None] ]={}

    def set(self,value:PerformOne):
        if value.player.role in self.__data:
            self.__data[value.player.role].append(value.targetid)
        else:
            self.__data[value.player.role]=[value.targetid]
    def __getitem__(self, role:str) -> Union[List[TARGETID], None]:
        return self.__data.get(role)
    def __len__(self) -> int:
        return len(self.__data)
            


class Game(Doings):
    def performData(self,gid:PLAYERID,pid:TARGETID):
        self.result.set(PerformOne(self.getByGID(gid),pid))

    async def getPerformData(self):
        self.result=PerformResult()
        pc=self.getPerformableCount()
        while len(self.result)<pc:
            await asyncio.sleep(1)#TODO: зафигачить таймер
        return self.result   

    def parsePerform(self):
        data:PerformResult=self.result
        if data["g"]:
            self.do_girl(data["g"][0])
        if data["k"]:
            self.do_killer(data["k"][0])

        if data["s"]:#TODO:Settings
            ret=self.do_sherif(data['s'][0])
            #TODO
        mafias=data["m"]
        if mafias != None:#TODO:Settings
            self.do_mafkill(mafias)
        if data["d"]:
            self.do_doctor(data["d"][0])
        #processing data
        #TODO:Организация отсылки данных назад клиентам

    async def startMainloop(self,room:Room):
        self.__room=room
        self.result=PerformResult()
        #room.checkConnectivity()
        super(Game,self).__init__(self.__room.players)
        #room.познакомитьИгроков()
        while self.isFinished==None:
            await room.send({"type":"DoPerform"})
            result = await self.getPerformData()
            print(result)
            self.parsePerform()
            await room.send({"type":"DoVote"})
            result = await self.getPerformData()
            print(result)
            self.parseVote()
'''0xDEADCODE
class Game:
    def __init__(self,players):#    m мафия p житель s шериф k маньяк d доктор g любовница
        self.players=players
        self.cardlist=[
        ['m','p','s','k','d','m'],#debug only!
        ['m','p','p','p','p','s'], #6
        ['m','m','p','p','p','p','s'],
        ['m','m','p','p','p','p','p','s'],
        ['m','m','p','p','p','p','p','s','k'],
        ['m','m','p','p','p','p','p','p','s','k'],#10
        ['m','m','p','p','p','p','p','p','s','k','d'],
        ['m','m','m','p','p','p','p','p','p','s','k','d'],
        ['m','m','m','p','p','p','p','p','p','p','s','k','d'],
        ['m','m','m','p','p','p','p','p','p','p','p','s','k','d'],#14
        ]
        print(len(players))
        #self.counted=self.cardlist[len(players)-6]#debug only
        self.counted=self.cardlist[0]
        random.shuffle(self.counted)
        print(self.counted)
        self.data={}
        for x,y in zip(self.counted,self.players):
            self.data[y[1]]={'type':x,'name':y[0],'healflag':None,'killflag':None,'freezeflag':False,'left':False,'vote':0}

    def countplayers(self,maf=0):
        retval=0
        if maf==1:
            for value in self.data:
                if self.data[value]['type']=='m' and self.data[value]['left']==False:
                    retval+=1
        elif maf==2:
            for value in self.data:
                    if self.data[value]['type']=='p' and self.data[value]['left']==False:
                        retval+=1
        elif maf ==0:
            for value in self.data:
                if self.data[value]['left']==False:
                    retval+=1
        return retval

    def indextype(self,type):
        for player in self.data:
            if self.data[player]['type']==type and self.data[player]['left']==False:
                return player
        return None
    
    def name2id(self,name):
        for data in self.data:
            if self.data[data]['name']==name:
                return data
        return 0
    
    def cheat(self):
        for x in self.data:
            print(self.data[x])
    def info(self,id):
        return self.data[id]
        
    def role2names(self,role):
        results=[]
        for data in self.data:
            if self.data[data]['type']==role and self.data[data]['left']==False:
                results.append(self.data[data]['name'])
        return results

    
    def mafkill(self,targets):
        #все засыпают, просипается мафия. кого убить /////////////////////////////////////////////////////////////////////////////////////////////////////
        if self.countplayers(1)>1:#голосовалка, не соблазнят компанию
        
            random.shuffle(targets)#АЛГОРИТМ ГОВНО!!!! магия рандома!!! 
            self.data[self.name2id(targets[0])]['killflag']=True
            
        else:    #одного мафиози соблазнят
            self.data[targets[0]]['killflag']=self.indextype('m')
            
    def sherif(self,target):        
        #мафия сделала вибор, просипается шериф ////////////////////////////////////////////////////////////////////////////////////////////////////////////
        return self.data[self.name2id(target)]['type']
        
    def killer(self,target):
        #просипается маньяк
        if not self.indextype('k')==None:
            self.data[self.name2id(target)]['killflag']=self.indextype('k')
            
    def doctor(self,target):
        if not self.indextype('d')==None:
            self.data[self.name2id(target)]['healflag']=self.indextype('d')
            
    def girl(self,target):
        #а теперь путана
        if not self.indextype('g')==None:
            self.data[self.name2id(target)]['freezeflag']=True
            
    def endnight(self):
        #постобработка
        for xraw in self.data:
            x=self.data[xraw]
            #доктора заняла путана
            if not x['healflag']==None:
                if self.data[x['healflag']]['freezeflag']==True:
                    x['healflag']=None
            #         хотели убить?                          убийца не занят?                                   доктор не лечил?                           
            if not x['killflag']==None and self.data[x['killflag']]['freezeflag']==False and x['healflag']==None:
                x['name']=x['name']+' (killed)'
                x['left']=True
                self.counted.remove(self.counted[self.data.index(x)])
        for xraw in self.data:
            x=self.data[xraw]
            x['killflag']=None
            x['healflag']=None
            x['freezeflag']=False
            
        print(self.countplayers(1),self.indextype('k'))
        print(self.countplayers(2),self.indextype('s'))
        if self.countplayers(1)==0 and self.indextype('k')==None:
            input('мафия слила!')
            exit()
        if self.countplayers(2)==0 and self.indextype('s')==None:
            input('мафия рулид!')
            exit()    
            
    def day(self,votes):
        #голосование (делаем функцию для разового голосования и другую для подсчета) 
        for player in range(0,self.countplayers(0)):
            self.data[int(votes[player])]['vote']+=1
        values=[]
        for x in self.data:
            values.append(x['vote'])
        maxval=max(values)
        indexes=[]
        for val,x in zip(values,range(0,len(values))):
            if val == maxval:
                indexes.append(x)
        random.shuffle(indexes)
        self.data[indexes[0]]['left']=True
        self.data[indexes[0]]['name']=self.data[indexes[0]]['name']+' (killed)'     
        for x in self.data:
            x['vote']=0
        if self.countplayers(1)==0 and self.indextype('k')==None:
            input('мафия слила!')
            exit()
        if self.countplayers(2)==0 and self.indextype('s')==None:
            input('мафия рулид!')
            exit()      
    
'''
