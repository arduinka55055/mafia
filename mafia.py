from typing import Union
import random
import uuid

playersMin = 6


class PlayerRAW:
    def __init__(self, name: str, gid: str):  # на просто id мы обосремося
        self.name = name
        self.id = gid  # ця штука заповнюється даними реєстрації на стороні серверу


class Player(PlayerRAW):
    def __init__(self, raw: PlayerRAW, role: str):
        self.__name = raw.name
        self.__id = raw.id  # ебкое ООП
        self.__role = role  # инкапсуляция в действии
        self.__killed = False
        self.__whore = False  # путана
        self.__uuid = uuid.uuid1()

    def __unicode__(self):
        return "Player:%s, Role:%s" % (self.getName(), self.getRole())

    def __str__(self):
        return "Player:%s, Role:%s" % (self.getName(), self.getRole())

    def __repr__(self):
        return "Player:%s, Role:%s" % (self.getName(), self.getRole())

    def getRole(self) -> Union[str, None]:
        return None if self.__killed else self.__role

    def getId(self) -> str:
        return self.__id

    def getName(self) -> str:
        return self.__name

    def getUUID(self):
        return self.__uuid

    def setKilled(self, state: bool):
        self.__killed = state

    def setWhore(self, state: bool):
        self.__whore = state

    def checkUser(self, id, role) -> bool:
        return True if (self.getId() == id and self.getRole() == role) else False

    def canDo(self, id, role) -> bool:
        return True if (not self.__whore and self.checkUser(id, role)) else False


class Players:
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
        ]
        self.players = []
        choosed = cardlist[len(data)-playersMin]
        random.shuffle(choosed)
        for x, y in zip(data, choosed):
            self.players.append(Player(x, y))

    def getMafias(self):
        for player in self.players:
            if player.getRole() == "m":
                yield player

    def getMafiasCount(self) -> int:
        counter = 0
        for _ in self.getMafias():
            counter += 1
        return counter

    def getGood(self):
        for player in self.players:
            if player.getRole() in ["p", "s", "d", "g"]:
                yield player

    def getGoodCount(self) -> int:
        counter = 0
        for _ in self.getGood():
            counter += 1
        return counter

    def getByUUID(self, UUID: str) -> Union[Player, None]:
        for player in self.players:
            if player.getUUID() == UUID:
                return player
        return None

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
        return self.getByUUID(target).getRole()

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
class GameMainloop(Game):
    async def startMainloop(self):
        pass #TODO

a = Game([
    PlayerRAW("a", random.random()),
    PlayerRAW("ba", random.random()),
    PlayerRAW("ca", random.random()),
    PlayerRAW("da", random.random()),
    PlayerRAW("ea", random.random()),
    PlayerRAW("fa", random.random()),
    PlayerRAW("ga", random.random())
])
for x in a.getMafias():
    print(x.getName())
for x in a.getGood():
    print(x.getName())

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
