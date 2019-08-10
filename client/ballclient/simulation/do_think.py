# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers
import random
import math


class DoThink():
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
    def get_next_one_points(self, player, vis_point):
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
            if go_cell_id in vis_point:
                continue
            result.append((move, go_x, go_y))
        return result

    # # 获取这个位置的联通的出口有几个
    # def get_exit_num(self, player, go_x, go_y):
    #     tmp_player = Player(-1, -1, -1)
    #     tmp_player.x, tmp_player.y = go_x, go_y
    #     tmp_next = self.get_next_one_points(tmp_player)
    #     ans = 0
    #     for it in tmp_next:
    #         if it[1] == go_x and it[2] == go_y:
    #             continue
    #         if it[1] == player.x and it[2] == player.y:
    #             continue
    #         ans += 1
    #     return ans

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
        max_weight, sum_weight = 0, 0
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            if power.visiable == False:
                continue
            # 我到金币的
            dis = mLegStart.get_short_length(px, py, power.x, power.y)

            dis += power.last_appear_dis * config.ALPHA

            weight = 1.0 / math.exp(dis)

            max_weight = max(max_weight, weight)
            sum_weight += weight

        max_weight *= config.THINK_POWER_WEIGHT
        sum_weight *= config.THINK_POWER_WEIGHT

        nweight = self.weight_moves.get(move, 0)
        self.weight_moves[move] = float("%.10f" % (nweight + sum_weight))

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
        if self.mRoundObj.my_alive_player_num < 3:
            return
        max_weight, sum_weight = 0, 0
        for k, oth_player in othPlayers.iteritems():
            # 我到敌人的，我要吃它
            dis = mLegStart.get_short_length(
                px, py, oth_player.x, oth_player.y)
            dis += oth_player.last_appear_dis * config.ALPHA

            weight = 1.0 / math.exp(dis)

            max_weight = max(max_weight, weight)
            sum_weight += weight

            # mLogger.debug("my_id: {}; my_point: ({}, {}); move: {}; oth_fish_id: {}; oth_point: ({}, {}); dis: {}".format(
            #     player.id, px, py, move, oth_player.id, oth_player.x, oth_player.y, dis))

        max_weight *= config.THINK_PLAYER_WEIGHT
        sum_weight *= config.THINK_PLAYER_WEIGHT

        nweight = self.weight_moves.get(move, 0)
        self.weight_moves[move] = float("%.10f" % (nweight + sum_weight))

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
    def do_excute(self, player, vis_point):
        next_one_points = self.get_next_one_points(player, vis_point)
        if len(next_one_points) == 0:
            return ""

        self.initial_weight_moves()
        self.reward_weight(player, next_one_points)
        self.punish_weight(player, next_one_points)

        ret_move = self.select_best_move()
        ret_x, ret_y = self.mRoundObj.real_go_point(
            player.x, player.y, ret_move)
        ret_cell_id = mLegStart.get_cell_id(ret_x, ret_y)
        vis_point.add(ret_cell_id)
        self.record_detial(player, ret_move)
        return ret_move

    def excute(self, mRoundObj):
        self.mRoundObj = mRoundObj
        action = list()
        vis_point = set()
        for k, player in mPlayers.iteritems():
            action.append({
                "team": player.team,
                "player_id": player.id,
                "move": [self.do_excute(player, vis_point)]
            })
        return action


mDoThink = DoThink()
