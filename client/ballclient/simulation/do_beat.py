# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math


class DoBeat():
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
    def get_next_one_points(self, player):
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
            result.append((move, go_x, go_y))
        return result

    # 获取这个位置的联通的出口有几个
    def get_exit_num(self, player, go_x, go_y):
        tmp_player = Player(-1, -1, -1)
        tmp_player.x, tmp_player.y = go_x, go_y
        tmp_next = self.get_next_one_points(tmp_player)
        ans = 0
        for it in tmp_next:
            if it[1] == go_x and it[2] == go_y:
                continue
            if it[1] == player.x and it[2] == player.y:
                continue
            ans += 1
        return ans

    # 初始化评分
    def initial_weight_moves(self):
        self.weight_moves.clear()

    '''
    奖励评分：
    1. 金币
    2. 虫洞
    3. 其他玩家
    '''

    def reward_power(self, player, move, px, py):
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            dis = mLegStart.get_short_length(px, py, power.x, power.y)
            dis += power.last_appear_dis * config.ALPHA

            weight = 1.0 / math.exp(dis)
            nweight = self.weight_moves.get(move, 0)

            self.weight_moves[move] = float(
                "%.10f" % (nweight + weight * config.BEAT_POWER_WEIGHT))

    def reward_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.reward_power(player, move, go_x, go_y)

    '''
    惩罚评分：
    1. 其他玩家
    2. 之前是否走过（很小的权重，避免原地打转用的） 
    3. 障碍物
    4. 金币周围情况
    '''

    def punish_player(self, player, move, px, py):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.x == -1 or oth_player.y == -1:
                continue

            dis = mLegStart.get_short_length(
                oth_player.x, oth_player.y, px, py)
            # exit_num = self.get_exit_num(player, px, py)

            dis += oth_player.last_appear_dis * config.ALPHA
            dis -= config.DELTA
            # dis -= 0.8 * (4 - exit_num)

            weight = 1.0 / math.exp(dis)
            nweight = self.weight_moves.get(move, 0)

            mLogger.debug("my_id: {}; my_point: ({}, {}); move: {}; oth_fish_id: {}; oth_point: ({}, {}); dis: {}".format(
                player.id, px, py, move, oth_player.id, oth_player.x, oth_player.y, dis))

            # self.weight_moves[move] = float(
            #     "%.10f" % (nweight - weight * config.BEAT_PLAYER_WEIGHT))
            self.weight_moves[move] = float(
                "%.10f" % min(nweight,  -weight * config.BEAT_PLAYER_WEIGHT))

    def punish_cell(self, move, px, py):
        cell_id = mLegStart.get_cell_id(px, py)
        vis_cnt = mLegStart.cell_vis_cnt.get(cell_id, 0)

        weight = vis_cnt
        nweight = self.weight_moves.get(move, 0)

        self.weight_moves[move] = float(
            "%.10f" % (nweight - weight * config.CELL_WEIGHT))

    def punish_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.punish_player(player, move, go_x, go_y)
            self.punish_cell(move, go_x, go_y)

    # 挑选一个评分最高的move
    def select_best_move(self):
        max_weight, ret_move = None, None
        for move, weight in self.weight_moves.iteritems():
            if max_weight == None or weight > max_weight:
                max_weight, ret_move = weight, move
        return ret_move

    # 对每一个玩家开始执行
    def do_excute(self, player):
        next_one_points = self.get_next_one_points(player)
        self.initial_weight_moves()
        self.reward_weight(player, next_one_points)
        self.punish_weight(player, next_one_points)

        ret_move = self.select_best_move()
        self.record_detial(player, ret_move)
        return ret_move

    def excute(self, mRoundObj):
        self.mRoundObj = mRoundObj
        action = list()
        for k, player in mPlayers.iteritems():
            action.append({
                "team": player.team,
                "player_id": player.id,
                "move": [self.do_excute(player)]
            })
        return action


mDoBeat = DoBeat()
