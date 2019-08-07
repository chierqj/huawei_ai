# coding: utf-8

from ballclient.utils.logger import mLogger


class Player(object):
    def __init__(self, fish_id, team_id, force):
        # 在legstart更新的变量
        self.id = fish_id
        self.team = team_id
        self.force = force

        # 在每一个round更新的变量
        self.score = 0
        self.sleep = True
        self.x = -1
        self.y = -1
        self.visibile = False

        self.bug_num = 0

        self.bug_move = []
        if self.id == 4:
            self.bug_move = [(7, 13), (8, 13), (9, 13),
                             (10, 13), (11, 13), (12, 13)]
        if self.id == 5:
            self.bug_move = [(7, 11), (8, 11), (9, 11),
                             (10, 11), (11, 11), (12, 11)]

        if self.id == 6:
            self.bug_move = [(7, 8), (8, 8), (9, 8),
                             (10, 8), (11, 8), (12, 8)]

        if self.id == 7:
            self.bug_move = [(7, 6), (8, 6), (9, 6),
                             (10, 6), (11, 6), (12, 6)]

        self.target = None

    def initialize(self):
        self.sleep = True
        self.visibile = False

    def assign(self, score, sleep, x, y):
        self.score = score
        self.sleep = (False if sleep == 0 else True)
        self.x = x
        self.y = y
        self.visibile = True


mPlayers = dict()
othPlayers = dict()
