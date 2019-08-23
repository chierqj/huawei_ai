# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math
from ballclient.simulation.my_action import Action


class DoBeat(Action):
    def __init__(self):
        super(DoBeat, self).__init__()

    '''
    # 能量值奖励评分
    def reward_power(self, player, move, px, py):
        max_weight, sum_weight = 0, 0
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            # 我到金币的
            dis = mLegStart.get_short_length(px, py, power.x, power.y)
            weight = float("%.5f" % (1.0 / math.exp(dis)))

            if power.visiable == False:
                dis = config.POWER_ALPHA * dis + config.POWER_BELAT * power.last_appear_dis
                weight = 0.0 if dis == 0 else float(
                    "%.5f" % (1.0 / math.exp(dis)))

            max_weight = max(max_weight, weight)
            sum_weight += weight

            if config.record_weight == True:
                mLogger.info("{} [my_fish: {}; point: ({}, {});] [power_value: {}; point: ({}, {})] [dis: {}] [weight: {:.5f}]".format(
                    move, player.id, player.x, player.y, power.point, power.x, power.y, dis, weight))

        max_weight *= config.BEAT_POWER_WEIGHT
        sum_weight *= config.BEAT_POWER_WEIGHT

        nweight = self.weight_moves.get(move, 0)
        self.weight_moves[move] = float("%.5f" % (nweight + sum_weight))

    # 奖励评分
    def reward_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.reward_power(player, move, go_x, go_y)

    # 访问过的节点的惩罚评分，防止逛街
    def punish_vis_cell(self, player, move, px, py):
        cell_id = mLegStart.get_cell_id(px, py)
        if cell_id in player.vis_cell:
            nweight = self.weight_moves.get(move, 0)

            self.weight_moves[move] = float(
                "%.5f" % (nweight - config.CELL_WEIGHT))

            if config.record_weight == True:
                mLogger.info("{} [my_fish: {}; point: ({}, {});] [vis_cell_point: ({}, {})] [weight: {:.5f}]".format(
                    move, player.id, player.x, player.y, px, py, config.CELL_WEIGHT))

    # 敌人的惩罚评分
    def punish_player(self, player, move, px, py):
        max_weight, sum_weight = 0, 0
        for k, oth_player in othPlayers.iteritems():
            # 敌人到我的，敌人要吃我
            dis = mLegStart.get_short_length(
                oth_player.x, oth_player.y, px, py)
            weight = float("%.5f" % (1.0 / math.exp(dis)))

            if oth_player.visiable == False:
                dis = config.PLAYER_ALPHA * dis + config.PLAYER_BELTA * oth_player.last_appear_dis
                weight = 0.0 if dis == 0 else float(
                    "%.5f" % (1.0 / math.exp(dis)))

            max_weight = max(max_weight, weight)
            sum_weight += weight

            if config.record_weight == True:
                mLogger.info("{} [my_fish: {}; point: ({}, {});] [othfish: {}; point: ({}, {})] [dis: {}] [weight: {:.5f}]".format(
                    move, player.id, player.x, player.y, oth_player.id, oth_player.x, oth_player.y, dis, weight))

        max_weight *= config.BEAT_PLAYER_WEIGHT
        sum_weight *= config.BEAT_PLAYER_WEIGHT

        nweight = self.weight_moves.get(move, 0)
        self.weight_moves[move] = float("%.5f" % (nweight + sum_weight))

    # 惩罚评分
    def punish_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.punish_player(player, move, go_x, go_y)
            self.punish_vis_cell(player, move, go_x, go_y)

    # 入口调用
    def do_excute(self):
        vis_point = set()
        for k, player in mPlayers.iteritems():
            round_id = self.mRoundObj.msg['msg_data']['round_id']
            # if round_id > 140 and round_id <= 150:
            #     player.move = ""
            #     self.record_detial(player, "")
            #     continue

            next_one_points = self.get_next_one_points(player, vis_point)
            if len(next_one_points) == 0:
                player.move = ""
                continue

            self.initial_weight_moves()
            self.reward_weight(player, next_one_points)
            self.punish_weight(player, next_one_points)

            ret_move = self.select_best_move()
            player.move = ret_move

            ret_x, ret_y = self.mRoundObj.real_go_point(
                player.x, player.y, ret_move)
            ret_cell_id = mLegStart.get_cell_id(ret_x, ret_y)
            vis_point.add(ret_cell_id)

            self.record_detial(player, ret_move)
    '''

    def reward_power(self, px, py):
        max_weight, sum_weight = 0, 0
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            # 我到金币的
            dis = mLegStart.get_short_length(px, py, power.x, power.y)
            weight = float("%.2f" % (1.0 / math.exp(dis)))
            if power.visiable == False:
                dis = config.POWER_ALPHA * dis + config.POWER_BELAT * power.last_appear_dis
                weight = 0.0 if dis == 0 else float(
                    "%.2f" % (1.0 / math.exp(dis)))
            max_weight = max(max_weight, weight)
            sum_weight += weight

        max_weight *= config.BEAT_POWER_WEIGHT
        sum_weight *= config.BEAT_POWER_WEIGHT

        return sum_weight

    def eat_power(self, next_one_points, player):
        min_dis, max_score, minx, miny = None, None, None, None
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            if power.visiable == False:
                continue
            dis = mLegStart.get_short_length(
                player.x, player.y, power.x, power.y)
            if min_dis == None or dis < min_dis or (dis == min_dis and power.point > max_score):
                min_dis, max_score, minx, miny = dis, power.point, power.x, power.y
        if min_dis == None:
            return False

        min_dis = None
        for mv, nx, ny in next_one_points:
            dis = mLegStart.get_short_length(nx, ny, minx, miny)
            if min_dis == None or dis < min_dis:
                min_dis, player.move = dis, mv
        return True

    def in_player_vision(self, px, py, x, y):
        vision = mLegStart.msg['msg_data']['map']['vision']
        if x < px - vision or x > px + vision:
            return False
        if y < py - vision or y > py + vision:
            return False
        return True

    def get_weight(self, enum, x, y):
        dead_area = [(1, 0), (17, 19)]
        if (x, y) in dead_area:
            return -3.0

        weight = 0
        for mv, nx, ny in enum:
            dis = mLegStart.get_short_length(nx, ny, x, y)
            if dis <= 4 and True == self.in_player_vision(nx, ny, x, y):
                weight -= float("%.2f" % (1.0 / math.exp(dis)))

        weight = float("%.2f" % weight)
        return weight

    def do_excute(self):
        next_one_points_ary = []
        vis_point = set()
        for k, player in othPlayers.iteritems():
            if player.visiable == False:
                self.predict_player_point(player)
                if player.predict_x == None:
                    continue
                next_one_points = self.get_next_one_points(
                    player.predict_x, player.predict_y)
            else:
                cell = mLegStart.get_cell_id(player.x, player.y)
                vis_point.add(cell)
                next_one_points = self.get_next_one_points(player.x, player.y)

            next_one_points_ary.append(next_one_points)

        all_enums = self.get_all_enums(next_one_points_ary)
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            next_one_points = self.get_next_one_points(
                player.x, player.y, vis_point)
            next_one_points.append(("", player.x, player.y))

            # 最低最高
            max_weight, ret_move, ret_cell = None, None, None
            danger_weight = None
            self.weight_moves.clear()
            for mv, nx, ny in next_one_points:
                # mv这个方向上的最低评价
                min_weight = None
                for enum in all_enums:
                    weight = self.get_weight(enum, nx, ny)
                    if min_weight == None or weight < min_weight:
                        min_weight = weight

                if max_weight == None or min_weight > max_weight:
                    max_weight, ret_move = min_weight, mv
                    cell = mLegStart.get_cell_id(nx, ny)
                    ret_cell = cell

                self.weight_moves[mv] = min_weight
                if danger_weight == None or min_weight < danger_weight:
                    danger_weight = min_weight

            # 这个评分是安全的
            if danger_weight > self.mRoundObj.limit_dead_weight:
                if False == self.eat_power(next_one_points, player):
                    length = len(next_one_points)
                    player.move = next_one_points[random.randint(
                        0, length - 1)][0]
            else:
                player.move = ret_move
                # vis_point.add(ret_cell)
            player.dead_weight = max_weight
            self.record_detial(player)


mDoBeat = DoBeat()
