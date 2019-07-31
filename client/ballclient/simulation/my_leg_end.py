# coding: utf-8


class LegEnd(object):
    def __init__(self):
        self.msg = ""
        self.tolPoint = dict()

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        teams = msg["msg_data"]['teams']
        for team in teams:
            point = self.tolPoint.get(str(team['id']), 0)
            self.tolPoint[str(team['id'])] = point + team["point"]


mLegEnd = LegEnd()
