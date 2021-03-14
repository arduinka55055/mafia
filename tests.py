from typing import List, Set
import unittest
import uuid
import mafia
#Test cases to test Calulator methods
#You always create  a child class derived from unittest.TestCase
def genPlayers(count:int=6)->Set[mafia.PlayerRAW]:
  returning=set()
  for n in range(1,count+1):
    returning.add(mafia.PlayerRAW("Player_%s" % n,uuid.uuid1()))
  return returning
class TestMafiaLogic(unittest.TestCase):
  #setUp method is overridden from the parent class TestCase
  def setUp(self):
    players=genPlayers(count=10)
    self.game=mafia.Game(players)
  #Each test method starts with the keyword test_
  def test_rolecheck(self):
    for x in self.game.getMafias():
      self.assertTrue(x.checkUser(x.getId(),"m"))
  
# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()