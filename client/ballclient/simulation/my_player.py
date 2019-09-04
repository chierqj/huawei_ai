# coding: utf-8

from ballclient.utils.logger import mLogger


class Player(object):
    def __init__(self, fish_id=-1, team_id=-1, force="", score=0, sleep=True, x=-1, y=-1, visiable=False, last_appear_dis=300):
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


        # 每一时刻的move
        self.move = ""

        # 预测的位置
        self.predict_x = None
        self.predict_y = None

        # 丢失视野连续多少回合
        self.lost_vision_num = 0



mPlayers = dict()
othPlayers = dict()
