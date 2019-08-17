# coding: utf-8

from ballclient.simulation.my_player import mPlayers, othPlayers


class LegEnd(object):
    def __init__(self):
        self.msg = ""
        self.tolPoint = dict()
        self.catch_run = 0
        self.not_catch_run = 0
        self.catch_predict = 0
        self.tol_predict = 0

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        teams = msg["msg_data"]['teams']
        for team in teams:
            point = self.tolPoint.get(str(team['id']), [])
            point.append(team['point'])
            self.tolPoint[str(team['id'])] = point

        print("-------------------------------------------------")
        print(">预判逃跑位置< [正确: {}; 错误: {}]".format(
            self.catch_run, self.not_catch_run))
        # print(">预判视野丢失< [总计: {}; 正确: {}]".format(
        #     self.tol_predict, self.catch_predict))

        self.catch_run = 0
        self.not_catch_run = 0
        self.tol_predict = 0
        self.catch_predict = 0


mLegEnd = LegEnd()
