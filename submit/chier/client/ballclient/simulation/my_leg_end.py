# coding: utf-8

from ballclient.simulation.my_player import mPlayers, othPlayers


class LegEnd(object):
    def __init__(self):
        self.msg = ""
        self.tolPoint = dict()

    def initialize_msg(self, msg):
        self.msg = msg

    def info_score(self):
        return
        team, score = -1, 0
        for k, player in mPlayers.iteritems():
            team = player.team
            score += player.score

        team = str(team)
        point = self.tolPoint.get(team, [])
        point.append(score)
        self.tolPoint[team] = point

        team, score = -1, 0
        for k, player in othPlayers.iteritems():
            team = player.team
            score += player.score
        team = str(team)
        point = self.tolPoint.get(team, [])
        point.append(score)
        self.tolPoint[team] = point

    def excute(self, msg):
        self.initialize_msg(msg)
        teams = msg["msg_data"]['teams']
        for team in teams:
            point = self.tolPoint.get(str(team['id']), [])
            point.append(team['point'])
            self.tolPoint[str(team['id'])] = point


mLegEnd = LegEnd()
