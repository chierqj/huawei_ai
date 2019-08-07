# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers
from ballclient.simulation.my_power import Power
import random
import math


class DoBeat():
    def __init__(self):
        self.mRoundObj = ""

        # 被吃的8个方向，顺带自己这个格子。总共9个
        # self.dinger_dirs = [(-1, -1), (0, -1), (1, -1), (-1, 0),
        #                     (1, 0), (-1, 1), (0, 1), (1, 1), (0, 0)]
        # 被吃的4个方向，顺带自己这个格子。总共5个
        self.dinger_dirs = [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]
        # 被吃的1个方向，即就是下一步在的位置
        # self.dinger_dirs = [(0, 0)]
        self.weight_moves = dict()

    # 获取两点的曼哈顿距离
    def get_dis(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    # 计算要吃的金币周围有几个空位
    def cal_empty_block(self, px, py):
        result = 0
        for adx, ady in self.dinger_dirs:
            x, y = px + adx, py + ady
            if px == x and py == y:
                continue
            if True == self.mRoundObj.match_border(x, y):
                if False == self.mRoundObj.match_meteor(x, y):
                    result += 1
        return result

    # 判断px, py这个位置能不能被吃，True表示能被吃
    def match_beat_eated(self, px, py):
        for player in self.mRoundObj.msg['msg_data']['players']:
            if player['team'] != config.team_id:
                for x, y in self.dinger_dirs:
                    nx, ny = player['x'] + x, player['y'] + y
                    if nx == px and ny == py:
                        return True
        return False

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
            result.append((move, go_x, go_y))
        return result

    def initial_weight_moves(self, next_one_points):
        self.weight_moves.clear()
        for move, go_x, go_y in next_one_points:
            self.weight_moves[move] = 0

    def reward_power(self, move, px, py):
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            dis = mLegStart.get_short_length(px, py, power.x, power.y)
            cell_id = mLegStart.get_cell_id(power.x, power.y)
            # if dis == 0:
            #     mLogger.info("我的鱼已经挨着金币了")
            #     dis = 0.5
            weight = 1 / math.exp(dis)
            nweight = self.weight_moves.get(move, 0)
            self.weight_moves[move] = float("%.4f" % (nweight + weight))

    def reward_wormhole(self, move, px, py):
        if False == self.mRoundObj.check_wormhole():
            return
        for wormhole in mLegStart.msg['msg_data']['map']['wormhole']:
            dis = mLegStart.get_short_length(
                px, py, wormhole['x'], wormhole['y'])
            cell_id = mLegStart.get_cell_id(wormhole['x'], wormhole['y'])
            # if dis == 0:
            #     mLogger.info("我的鱼身处虫洞上面")
            #     dis = 0.25
            weight = 1 / math.exp(dis)
            nweight = self.weight_moves.get(move, 0)
            self.weight_moves[move] = float("%.4f" % (nweight + weight))

    def reward_player(self, move, px, py):
        pass

    def reward_weight(self, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.reward_power(move, go_x, go_y)
            self.reward_player(move, go_x, go_y)
            self.reward_wormhole(move, go_x, go_y)

    def punish_power(self, move, px, py):
        pass

    def punish_player(self, move, px, py):
        for k, player in othPlayers.iteritems():
            if player.x == -1 or player.y == -1:
                continue
            dis = mLegStart.get_short_length(px, py, player.x, player.y)
            cell_id = mLegStart.get_cell_id(player.x, player.y)
            if dis == 0:
                mLogger.info("敌方的鱼已经挨着我的鱼了")
            if player.last_appear_dis == 0:
                weight = 1 / math.exp(dis)
            else:
                weight = 1 / math.exp(dis) + 1 / player.last_appear_dis
            nweight = self.weight_moves.get(move, 0)
            self.weight_moves[move] = float("%.4f" % (nweight - weight))

    def punish_weight(self, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.punish_power(move, go_x, go_y)
            self.punish_player(move, go_x, go_y)

    def select_best_move(self):
        max_weight, ret_move = None, None
        for move, weight in self.weight_moves.iteritems():
            if max_weight == None or weight > max_weight:
                max_weight, ret_move = weight, move
        mLogger.info("{}, {}".format(ret_move, max_weight))
        return ret_move

    def record_detial(self, player, move):
        if False == config.record_detial or None == move:
            return

        mLogger.info(self.weight_moves)
        mLogger.info('[fish: {}, from: ({}, {}), move: {}]'.format(
            player.id, player.x, player.y, move))

    def do_excute(self, player):
        next_one_points = self.get_next_one_points(player)
        self.initial_weight_moves(next_one_points)
        self.reward_weight(next_one_points)
        self.punish_weight(next_one_points)
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
