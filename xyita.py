from typing import List


class MyDict(dict):
    def __init__(self) -> None:
        self.shit=[]
    def q(self):
        pass
    #def __setitem__(self, k,v) -> None:
    #    return super().__setitem__(k, "shit")
    def append(self,shit):
        self.shit.append(shit)
a=MyDict()
a["foo"]=1
a["bar"]=1

for x in range(0,10):
    print(x)