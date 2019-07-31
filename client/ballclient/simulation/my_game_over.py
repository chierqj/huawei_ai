# coding: utf-8

from ballclient.simulation.my_leg_end import mLegEnd

class GameOver(object):
    def __init__(self):
        self.msg = ""

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        print(mLegEnd.tolPoint)

mGameOver = GameOver()
