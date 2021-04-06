from typing import List, Set
import unittest
import uuid
import mafia
import roomHandler
import websockets
# Test cases to test Calulator methods
# You always create  a child class derived from unittest.TestCase


def genPlayers(count: int = 6) -> Set[mafia.PlayerRAW]:
    returning = set()
    for n in range(1, count+1):
        returning.add(mafia.PlayerRAW("Player_%s" % n, str(uuid.uuid4())))
    return returning


class TestMafiaLogic(unittest.TestCase):
    # setUp method is overridden from the parent class TestCase
    def setUp(self):
        players = genPlayers(count=10)
        self.game = mafia.Game(players)
    # Each test method starts with the keyword test_

    def test_rolecheck(self):
        for x in self.game.getMafias():
            self.assertTrue(x.checkUser(x.id, "m"))        


class TestRoomConnection(unittest.TestCase):
    # setUp method is overridden from the parent class TestCase
    def setUp(self):
        self.room = roomHandler.Room("myroom", "123", 100)

    def testSomething(self):
        # Each test method starts with the keyword test_
        self.assertEqual(self.room.isStarted, False)

class TestWSConnection(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        print("hello")
    async def testSomething(self):
        self.ws=await websockets.connect("ws://localhost:8000/pool")
        await self.ws.send('''{"gid":0.32286137191177533,"nick":"gamer","avatar":"http://example.com","pck":"GetInfo"}''')
        greeting = await self.ws.recv()
        print(greeting)
        await self.ws.close()

# Executing the tests in the above test case class
if __name__ == "__main__":
    unittest.main()
