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
        self.dinger_dirs = [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]
        self.weight_moves = dict()

    # 打印详细log
    def record_detial(self, player, move):
        if False == config.record_detial or None == move:
            return

        mLogger.info(self.weight_moves)
        mLogger.info('[fish: {}, from: ({}, {}), move: {}]'.format(
            player.id, player.x, player.y, move))

    # 获取下一步移动的位置，仅判断是不是合法
    def get_next_one_points(self, player, vis_point=set()):
        moves = ['up', 'down', 'left', 'right']
        result = []
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(player.x, player.y, move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if go_x == player.x and go_y == player.y:
                continue
            go_cell_id = mLegStart.get_cell_id(go_x, go_y)
            # vis_point 控制多条鱼尽量不重叠
            if go_cell_id in vis_point:
                continue
            result.append((move, go_x, go_y))
        return result

    # 获取以predict为出发点下一步移动的位置，仅判断是不是合法
    def get_predict_next_one_points(self, player, vis_point=set()):
        moves = ['up', 'down', 'left', 'right']
        result = []
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(
                player.predict_x, player.predict_y, move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if go_x == player.x and go_y == player.y:
                continue
            go_cell_id = mLegStart.get_cell_id(go_x, go_y)
            # vis_point 控制多条鱼尽量不重叠
            if go_cell_id in vis_point:
                continue
            result.append((move, go_x, go_y))
        return result

    # 获取x, y的可行位置的数目
    def get_next_one_num(self, x, y, vis_point=set()):
        moves = ['up', 'down', 'left', 'right']
        result = 0
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(x, y, move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if go_x == x and go_y == y:
                continue
            go_cell_id = mLegStart.get_cell_id(go_x, go_y)
            # vis_point 控制多条鱼尽量不重叠
            if go_cell_id in vis_point:
                continue
            result += 1
        return result

    # 初始化评分
    def initial_weight_moves(self):
        self.weight_moves.clear()

    # 奖励评分
    def reward_weight(self, player, next_one_points):
        pass

    # 惩罚评分
    def punish_weight(self, player, next_one_points):
        pass

    # 挑选一个评分最高的move
    def select_best_move(self):
        max_weight, ret_move = None, None
        for move, weight in self.weight_moves.iteritems():
            if max_weight == None or weight > max_weight:
                max_weight, ret_move = weight, move
        return ret_move

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
