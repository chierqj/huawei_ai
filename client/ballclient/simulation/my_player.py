# coding: utf-8

from ballclient.utils.logger import mLogger


class Player(object):
    def __init__(self, fish_id, team_id, force):
        # 在legstart更新的变量
        self.id = fish_id
        self.team = team_id
        self.force = force

        # 在每一个round自身需要改变的
        self.score = 0
        self.sleep = True
        self.x = -1
        self.y = -1
        self.visiable = False
        self.target = None

        # 奖惩相关的变量
        self.last_appear_dis = 600

    def initialize(self):
        self.sleep = True

    def assign(self, last_appear_dis, score, sleep, x, y, visiable):
        self.last_appear_dis = last_appear_dis
        self.score = score
        self.sleep = sleep
        self.x = x
        self.y = y
        self.visiable = visiable

    def update_last_appear(self):
        self.last_appear_dis += 1
        self.visiable = False


mPlayers = dict()
othPlayers = dict()