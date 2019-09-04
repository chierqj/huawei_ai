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
            team = "My" if key == str(config.team_id) else "Oth"
            print("[Team: {}, First: {}, Second: {}, Total: {}]".format(
                team, point[0], point[1], point[0] + point[1]))

        print("--------------------------------------")
        tol_eated_count, tol_eated_score = 0, 0
        for k, v in mLegEnd.eated_info.iteritems():
            print("[玩家: {}, 睡眠总次数: {}, 被吃了: {}, 睡眠丢分: {}, 丢分: {}]".format(
                k, v['count'], v['count'] / 3, v['score'], v['score'] / 3
            ))
            tol_eated_count += v['count'] / 3
            tol_eated_score += v['score'] / 3
        print("[被吃合计: {}, 丢分合计: {}]".format(tol_eated_count, tol_eated_score))
        mLegEnd.tolPoint.clear()


mGameOver = GameOver()
