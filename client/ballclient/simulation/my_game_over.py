# coding: utf-8

from ballclient.simulation.my_leg_end import mLegEnd
from ballclient.auth import config


class GameOver(object):
    def __init__(self):
        self.msg = ""

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        for key, point in mLegEnd.tolPoint.iteritems():
            # team = "我方" if key == str(config.team_id) else "敌方"
            # print("[Team: {}, 上半场: {}, 下半场: {}, 总分: {}]".format(
            #     team, point[0], point[1], point[0] + point[1]))

            team = "My" if key == str(config.team_id) else "Oth"
            print("[Team: {}, First: {}, Second: {}, Total: {}]".format(
                team, point[0], point[1], point[0] + point[1]))
        mLegEnd.tolPoint.clear()


mGameOver = GameOver()
