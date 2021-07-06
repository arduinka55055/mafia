import asyncio
from typing import List, Set
import unittest
import uuid
import mafia
import roomHandler
import websockets
import warnings
# Test cases to test Calulator methods
# You always create  a child class derived from unittest.TestCase


def genPlayers(count: int = 6) -> Set[mafia.PlayerRAW]:
    returning = set()
    for n in range(1, count+1):
        returning.add(mafia.PlayerRAW("Player_%s" % n, str(uuid.uuid4())))
    return returning


class roomMock:
    def __init__(self,players:Set[mafia.PlayerRAW]):
        self.players=players
    async def send(self,data:dict):
        data["pck"]="GameCast"
        print(data)

    async def sendto(self,data:dict,player:mafia.PLAYERID):
        data["pck"]="GameCast"
        print(data,player)


class TestMafiaLogic(unittest.IsolatedAsyncioTestCase):
    # setUp method is overridden from the parent class TestCase
    def setUp(self):
        self.playersRAW = genPlayers(count=14)
        self.game=mafia.Game(self.playersRAW)
    # Each test method starts with the keyword test_
    def getp(self,role):
        for x in self.game.players:
            if x.role==role:
                return x
        raise mafia.PlayerNotFoundError(role)
    async def test_rolecheck(self):
        for x in self.game.getMafias():
            self.assertTrue(x.checkUser(x.id, "m"))     
    def reset(self):
        self.game=mafia.Game(self.playersRAW)
    async def test_mkill(self):
        self.reset()
        human=self.getp("p")
        self.game.do_mafkill([human.UUID])
        self.assertTrue(human.isKilled)

    async def test_kill(self):
        self.reset()
        human=self.getp("p")
        self.game.do_killer(human.UUID)
        self.assertTrue(human.isKilled)
    async def test_healing(self):
        self.reset()
        human=self.getp("p")
        self.game.do_killer(human.UUID)
        self.assertTrue(human.isKilled)
        self.game.do_doctor(human.UUID)
        self.assertFalse(human.isKilled)
    async def test_whore_vs_1mafia(self):
        self.reset()
        self.playersRAW = genPlayers(count=6)
        self.game=mafia.Game(self.playersRAW)
        human=self.getp("p")
        mafiap=self.getp("m")
        self.game.whore(mafiap)
        self.assertTrue(mafiap.isFucked)
        self.game.do_mafkill([human.UUID])
        
        self.assertFalse(human.isKilled)
    async def test_whore_vs_2mafias(self):
        self.reset()
        self.playersRAW = genPlayers(count=13)
        self.game=mafia.Game(self.playersRAW)
        human=self.getp("p")
        mafiap=self.getp("m")
        self.game.whore(mafiap)
        self.assertTrue(mafiap.isFucked)
        self.game.do_mafkill([human.UUID])
        
        self.assertTrue(human.isKilled)
    async def test_whore_vs_doctor(self):
        self.reset()
        self.playersRAW = genPlayers(count=14)
        self.game=mafia.Game(self.playersRAW)

        human=self.getp("p")
        doctor=self.getp("d")
        mafiap=self.getp("m")
        self.game.whore(doctor)
        self.assertTrue(doctor.isFucked)
        self.game.do_mafkill([human.UUID])
        self.game.do_doctor(human.UUID)

        self.assertTrue(human.isKilled)
# Executing the tests in the above test case class
if __name__ == "__main__":
    unittest.main()
