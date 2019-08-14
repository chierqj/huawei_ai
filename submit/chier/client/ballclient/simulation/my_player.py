# coding: utf-8

from ballclient.utils.logger import mLogger


class Player(object):
    def __init__(self, fish_id, team_id, force, score, sleep, x, y, visiable, last_appear_dis):
        # 在legstart更新的变量
        self.id = fish_id
        self.team = team_id
        self.force = force

        # 在每一个round自身需要改变的
        self.score = score
        self.sleep = sleep
        self.x = x
        self.y = y
        self.visiable = visiable
        self.target = None

        # 奖惩相关的变量
        self.last_appear_dis = last_appear_dis

        # 走过的路
        self.vis_cell = set()

        # 要去哪一个矿区吃金币
        self.target_power_x = None
        self.target_power_y = None

        # 每一时刻的move
        self.move = ""

        # 追击的鱼
        self.grab_fish = None

        # 预测的位置
        self.predict_x = None
        self.predict_y = None

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
