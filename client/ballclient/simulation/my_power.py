# coding: utf-8


class Power(object):
    def __init__(self, last_appear_dis, x, y, point, visiable):
        self.last_appear_dis = last_appear_dis
        self.x = x
        self.y = y
        self.point = point
        self.visiable = visiable

    def assign(self, last_appear_dis, x, y, point, visiable):
        self.last_appear_dis = last_appear_dis
        self.x = x
        self.y = y
        self.point = point
        self.visiable = visiable

    def update_last_appear(self):
        self.last_appear_dis += 1
        self.visiable = False
