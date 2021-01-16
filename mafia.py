import random
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
    
    
    