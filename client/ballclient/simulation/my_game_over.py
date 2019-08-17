# coding: utf-8

from ballclient.simulation.my_leg_end import mLegEnd


class GameOver(object):
    def __init__(self):
        self.msg = ""

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        print("-------------------------------------------------")
        for key in mLegEnd.tolPoint:
            point = mLegEnd.tolPoint[key]
            print("[Team: {}, 上半场: {}, 下半场: {}, 总分: {}]".format(
                key, point[0], point[1], point[0] + point[1]))
mGameOver = GameOver()
