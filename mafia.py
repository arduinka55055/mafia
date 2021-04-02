from __future__ import annotations
import asyncio
from typing import Dict, Generator, Iterable, List, Union
from dataclasses import dataclass
import random
import uuid
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from roomHandler import Room
PLAYERID=str
ROOMID=uuid.UUID
TARGETID=uuid.UUID
playersMin = 6

class PlayerNotFoundError(Exception):
    def __init__(self,UUID:PLAYERID):
        self.uuid=UUID
        super().__init__("Error! Player with UUID:${self.uuid} not found!")
    def __repr__(self):
        return "Error! Player with UUID:${self.uuid} not found!"

class PlayerRAW:
    def __init__(self, name: str, gid: PLAYERID, avatar: str=None):  # на просто id мы обосремося
        self.name = name
        self.id = gid  # ця штука заповнюється даними реєстрації на стороні серверу
        self.avatar = avatar #only for other players. doesnt impact logic

class Player(PlayerRAW):
    def __init__(self, raw: PlayerRAW, role: str):
        self.__name = raw.name
        self.avatar = raw.avatar
        self.__id = raw.id  # ебкое ООП
        self.__role = role  # инкапсуляция в действии
        self.__killed = False
        self.__whore = False  # путана
        self.__uuid = uuid.uuid1()

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
    def setKilled(self, state: bool):
        self.__killed = state

    def setWhore(self, state: bool):
        self.__whore = state

    def checkUser(self, id, role) -> bool:
        return True if (self.id == id and self.role == role) else False

    def canDo(self, id, role) -> bool:
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
    def getPerformable(self)->Generator:
        for player in self.players:
            if player.role in ['m','s','k','d','g']:
                yield player
    def getPerformableCount(self)->int:
        counter = 0
        for _ in self.getPerformable():
            counter += 1
        return counter
    def getByUUID(self, UUID: str) -> Player:
        for player in self.players:
            if player.UUID == UUID:
                return player
        raise PlayerNotFoundError(UUID)

    def kill(self, player: Player):
        player.setKilled(True)

    def heal(self, player: Player):
        player.setKilled(False)

    def whore(self, player: Player):
        player.setWhore(True)


class Game(Players):
    def mafkill(self, targets):
        # все засыпают, просипается мафия. кого убить /////////////////////////////////////////////////////////////////////////////////////////////////////
        if self.getMafiasCount() > 1:  # голосовалка, не соблазнят компанию
            random.shuffle(targets)  # АЛГОРИТМ ГОВНО!!!! магия рандома!!!
            self.kill(targets[0])

        else:  # одного мафиози соблазнят
            self.kill(self.getByUUID(targets))

    def sherif(self, target) -> str:
        # мафия сделала вибор, просипается шериф ////////////////////////////////////////////////////////////////////////////////////////////////////////////
        return self.getByUUID(target).role

    def killer(self, target):
        # просипается маньяк
        self.kill(self.getByUUID(target))

    def doctor(self, target):
        self.heal(self.getByUUID(target))

    def girl(self, target):
        # а теперь путана
        self.whore(self.getByUUID(target))

    def endnight(self, data):
        # постобработка
        pass
@dataclass
class PerformOne:
    player: Player
    targetid: TARGETID

class PerformResult(dict):
    def __init__(self):
        self.__data:Dict[str,List]=dict()
    @property
    def data(self):
        return self.__data
    @data.setter
    def data(self,value:PerformOne):
        self.__data[value.player.role].append(value.targetid)

    def getByRole(self,role)->Union[List[str], None]:
        return self.get(role)
            


class GameMainloop(Game):
    def performData(self,gid:PLAYERID,pid:TARGETID):
        self.data=PerformOne(self.getByUUID(gid),pid)

    async def getPerformData(self):
        self.result=PerformResult()
        while len(self.result.data)<self.getPerformableCount():
            await asyncio.sleep(1)#TODO зафигачить таймер
        return self.result.data   

    async def startMainloop(self,room:Room):
        self.__room=room
        self.result=PerformResult()
        #room.checkConnectivity()
        super(Game,self).__init__(self.__room.players)
        #room.познакомитьИгроков()
        await room.send({"type":"Perform"})
        result = await self.getPerformData()


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
