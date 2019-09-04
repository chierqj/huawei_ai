# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math


class Action(object):
    def __init__(self):
        self.mRoundObj = ""

    # 根据move改变坐标
    def go_next(self, x, y, move):
        if move == "":
            return x, y
        if move == 'up':
            return x, y - 1
        if move == 'down':
            return x, y + 1
        if move == 'left':
            return x - 1, y
        if move == 'right':
            return x + 1, y

    # 打印详细log
    def record_detial(self, player, text):
        mLogger.info('[{}] [player: {}, point: ({}, {}), move: {}]'.format(
            text, player.id, player.x, player.y, player.move))

    # 判断是否在(x, y)是否在(px, py)视野当中
    def judge_in_vision(self, px, py, x, y):
        vision = mLegStart.msg['msg_data']['map']['vision']
        if x < px - vision or x > px + vision:
            return False
        if y < py - vision or y > py + vision:
            return False
        return True

    # 获取players的所有可能的情况
    def get_all_enums(self, next_one_points):
        result = []
        up = len(next_one_points)

        def dfs(dep, enum=[]):
            if dep == up:
                import copy
                result.append(copy.deepcopy(enum))
                return
            for pid, mv, nx, ny in next_one_points[dep]:
                dfs(dep + 1, enum + [(pid, mv, nx, ny)])
        dfs(0)

        return result

    # 当鱼视野丢失的时候，预判他行走的位置
    def predict_player_point(self, pre_player):
        vision = mLegStart.msg['msg_data']['map']['vision']

        px, py = pre_player.x, pre_player.y
        if pre_player.predict_x != None:
            px, py = pre_player.predict_x, pre_player.predict_y

        next_one_points = self.get_next_one_points(px, py)

        for move, go_x, go_y in next_one_points:
            have_view = False
            for k, player in mPlayers.iteritems():
                if go_x < px - vision or go_x > px + vision:
                    continue
                if go_y < py - vision or go_y > py + vision:
                    continue
                have_view = True
                break
            if have_view == False:
                pre_player.predict_x, pre_player.predict_y = go_x, go_y

    # 更新每个鱼是不是需要预测位置
    def update_predict(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                self.predict_player_point(oth_player)
            else:
                oth_player.predict_x, oth_player.predict_y = oth_player.x, oth_player.y,
            mLogger.info("[player: {}; point: ({}, {}); predict: ({}, {}); lost_vision_num: {}]".format(
                oth_player.id, oth_player.x, oth_player.y, oth_player.predict_x, oth_player.predict_y, oth_player.lost_vision_num
            ))

    # 入口
    def excute(self, mRoundObj):
        self.mRoundObj = mRoundObj
        self.do_excute()
        action = list()
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            action.append({
                "team": player.team,
                "player_id": player.id,
                "move": [player.move]
            })
        return action
