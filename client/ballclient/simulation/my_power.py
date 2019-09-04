# coding: utf-8


class Power(object):
    def __init__(self, x, y, point, visiable=False, lost_vision_num=0):
        self.x = x
        self.y = y
        self.point = point
        self.visiable = visiable
        self.lost_vision_num = lost_vision_num