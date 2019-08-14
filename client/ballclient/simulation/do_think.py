# coding: utf-8

import math
import random

from ballclient.auth import config
from ballclient.simulation.my_action import Action
from ballclient.simulation.my_leg_start import mLegStart
from ballclient.simulation.my_player import Player, mPlayers, othPlayers
from ballclient.simulation.my_power import Power
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog


class DoThink(Action):
    def __init__(self):
        super(DoThink, self).__init__()
        self.grab_player = None

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

        max_weight *= config.THINK_POWER_WEIGHT
        sum_weight *= config.THINK_POWER_WEIGHT

        nweight = self.weight_moves.get(move, 0)
        self.weight_moves[move] = float("%.5f" % (nweight + sum_weight))
        # self.weight_moves[move] = float("%.5f" % (nweight + max_weight))

    def reward_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.reward_power(player, move, go_x, go_y)

    def punish_vis_cell(self, player, move, px, py):
        cell_id = mLegStart.get_cell_id(px, py)
        if cell_id in player.vis_cell:
            nweight = self.weight_moves.get(move, 0)

            mLogger.info("{} [my_fish: {}; point: ({}, {});] [vis_cell_point: ({}, {})] [weight: {:.5f}]".format(
                move, player.id, player.x, player.y, px, py, config.CELL_WEIGHT))

            if config.record_weight == True:
                self.weight_moves[move] = float(
                    "%.5f" % (nweight - config.CELL_WEIGHT))

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

        max_weight *= config.THINK_PLAYER_WEIGHT
        sum_weight *= config.THINK_PLAYER_WEIGHT
        nweight = self.weight_moves.get(move, 0)
        self.weight_moves[move] = float("%.5f" % (nweight + sum_weight))
        # self.weight_moves[move] = float("%.5f" % (nweight + max_weight))

    def punish_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.punish_player(player, move, go_x, go_y)
            self.punish_vis_cell(player, move, go_x, go_y)

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

    @msimulog()
    def select_grab_player(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            return oth_player
        return None
        # min_dis, grab_ply, follow_plys, pow_ply = None, None, None, None
        # for k, oth_ply in othPlayers.iteritems():
        #     return oth_ply
        #     if oth_ply.visiable == False:
        #         continue
        #     distance = []
        #     for k, m_ply in mPlayers.iteritems():
        #         dis = mLegStart.get_short_length(
        #             m_ply.x, m_ply.y, oth_ply.x, oth_ply.y)
        #         distance.append((dis, m_ply))
        #     distance = sorted(distance, key=lambda it: it[0])
        #     tmp_dis = [it[0] for it in distance]
        #     print(tmp_dis)
        #     sum_dis = distance[0][0] + distance[1][0] + distance[2][0]
        #     if min_dis == None or sum_dis < min_dis:
        #         min_dis, grab_ply = sum_dis, oth_ply
        #         follow_plys = [distance[0][1], distance[1][1], distance[2][1]]
        #         pow_ply = distance[3][1]
        # return grab_ply, pow_ply, follow_plys

    @msimulog()
    def eat_power(self, players):
        '''
        lv1: (10, 9)
        lv2: (3, 2)
        lv3: (16, 17)
        lv4: (16, 2)
        '''
        power_area = [(10, 9), (4, 3), (14, 3), (14, 16)]
        vis = set()
        for area_x, area_y in power_area:
            min_dis, min_player_index = None, None

            for index, player in enumerate(players):
                if index in vis:
                    continue
                dis = mLegStart.get_short_length(
                    player.x, player.y, area_x, area_y)

                if min_dis == None or dis < min_dis:
                    min_dis, min_player_index = dis, index

            if min_player_index == None:
                continue
            players[min_player_index].target_power_x = area_x
            players[min_player_index].target_power_y = area_y
            vis.add(min_player_index)

        for player in players:
            mLogger.info("[ply: {}; point: ({}, {}); target: ({}, {})".format(
                player.id, player.x, player.y, player.target_power_x, player.target_power_y))

            flag = False

            for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
                if power.visiable == False:
                    continue

                if power.x == player.x and power.y == player.y:
                    player.move = ""
                    flag = True
                    break

                vision = mLegStart.msg['msg_data']['map']['vision']
                if power.x > player.target_power_x + vision or power.x < player.target_power_x - vision:
                    continue
                if power.y > player.target_power_y + vision or power.y < player.target_power_y - vision:
                    continue

                flag = True
                player.move = mLegStart.get_short_move(
                    player.x, player.y, power.x, power.y)
                break

            if False == flag:
                if player.x == player.target_power_x and player.y == player.target_power_y:
                    player.move = ""
                else:
                    player.move = mLegStart.get_short_move(
                        player.x, player.y, player.target_power_x, player.target_power_y)

    @msimulog()
    def get_follow_power_player(self):
        players = []

        for k, player in mPlayers.iteritems():
            dis = mLegStart.get_short_length(
                player.x, player.y, self.grab_player.x, self.grab_player.y)
            players.append((dis, player))

        players = sorted(players, key=lambda it: it[0])

        follow_players = [it[1] for it in players[:3]]
        power_player = [it[1] for it in players[3:]]

        return follow_players, power_player

    @msimulog()
    def follow_grab_player(self, follow_players):
        vis_point = set()
        for player in follow_players:
            if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
                mLogger.info("假装追到了，或者视野预判失误")
                return True

            next_one_points = self.get_next_one_points(
                player, vis_point)

            min_dis, ret, cell_id = None, "", ""

            for move, go_x, go_y in next_one_points:
                dis = mLegStart.get_short_length(
                    go_x, go_y, self.grab_player.predict_x, self.grab_player.predict_y)

                if min_dis == None or dis < min_dis:
                    min_dis, ret = dis, move
                    cell_id = mLegStart.get_cell_id(go_x, go_y)

            player.move = ret
            vis_point.add(cell_id)
        return False
        # for player in follow_players:
        #     if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
        #         mLogger.info("假装追到了，或者视野预判失误")
        #         return True

        #     move = mLegStart.get_short_move(
        #         player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
        #     player.move = move

        # return False

    @msimulog()
    def predict_grab_player(self):
        vision = mLegStart.msg['msg_data']['map']['vision']
        next_one_points = self.get_next_one_points(self.grab_player, set())

        for move, go_x, go_y in next_one_points:
            have_view = False
            mLogger.info(
                "[move: {}; pre_point: ({}， {})]".format(move, go_x, go_y))
            for k, player in mPlayers.iteritems():
                if go_x < player.x - vision or go_x > player.x + vision:
                    continue

                if go_y < player.y - vision or go_y > player.y + vision:
                    continue

                have_view = True
                break
            if have_view == False:
                self.grab_player.predict_x = go_x
                self.grab_player.predict_y = go_y

    def do_excute(self):
        # 自己的鱼不够四个，老实吃金币
        if self.mRoundObj.my_alive_player_num < 4:
            mLogger.info("alive_player < 4")
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
            return

        # 还没有追鱼的目标
        if self.grab_player == None:
            self.grab_player = self.select_grab_player()

        # 找不到一条鱼可以追，视野全部丢失
        if self.grab_player == None:
            mLogger.info("鱼全部丢失视野")
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
            return

        self.grab_player.predict_x = self.grab_player.x
        self.grab_player.predict_y = self.grab_player.y

        # 要追的鱼看不到了，预判位置
        if self.grab_player.visiable == False:
            self.predict_grab_player()
            mLogger.info("------ [grab_player: {}; point: ({}, {})".format(
                self.grab_player.id, self.grab_player.x, self.grab_player.y))
            mLogger.info("------ [grab_player: {}; predict_point: ({}, {})".format(
                self.grab_player.id, self.grab_player.predict_x, self.grab_player.predict_y))

        follow_players, power_player = self.get_follow_power_player()

        # mLogger.info("[被抓的鱼: {}; ({}, {})] [抓鱼的鱼: {}; ({}, {}) | {}; ({}, {}) | {}; ({}, {})] [吃金币的鱼: {}; ({}, {})]".format(
        #     self.grab_player.id, self.grab_player.x, self.grab_player.y,
        #     follow_players[0].id, follow_players[0].x, follow_players[0].y,
        #     follow_players[1].id, follow_players[1].x, follow_players[1].y,
        #     follow_players[2].id, follow_players[2].x, follow_players[2].y,
        #     power_player.id, power_player.x, power_player.y
        # ))

        # 假装追到鱼了，或者视野预判失误
        if True == self.follow_grab_player(follow_players):
            self.grab_player = None
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
        else:
            self.eat_power(power_player)

    @msimulog()
    def excute(self, mRoundObj):
        self.mRoundObj = mRoundObj

        self.do_excute()
        # players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
        # self.eat_power(players)

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


mDoThink = DoThink()
