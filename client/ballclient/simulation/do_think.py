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
        self.grab_player_last_move = ""

    @msimulog()
    def select_grab_player(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            if oth_player.score < 5:
                continue
            return oth_player
        return None

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

            mLogger.info("[player: {}; point: ({}, {}); target: ({}, {})]".format(
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

                dis, min_move, _ = self.get_min_dis(player, power.x, power.y)
                player.move = min_move
                break

            if False == flag:
                if player.x == player.target_power_x and player.y == player.target_power_y:
                    player.move = ""
                else:
                    dis, min_move, _ = self.get_min_dis(
                        player, player.target_power_x, player.target_power_y)
                    player.move = min_move

    @msimulog()
    def get_follow_power_player(self):
        players = []

        for k, player in mPlayers.iteritems():
            dis = mLegStart.get_short_length(
                player.x, player.y, self.grab_player.x, self.grab_player.y)
            players.append((dis, player))

        players = sorted(players, key=lambda it: it[0])

        follow_num = 3
        follow_players = [it[1] for it in players[:follow_num]]
        power_player = [it[1] for it in players[follow_num:]]

        return follow_players, power_player

    @msimulog()
    def get_predict_go_point(self):
        direction = ["up", "down", "left", "right"]

        predict_go = []
        for d in direction:
            go_x, go_y = self.mRoundObj.real_go_point(
                self.grab_player.predict_x, self.grab_player.predict_y, d)

            if go_x == None:
                continue
            predict_go.append((d, go_x, go_y))

        return predict_go

    def get_min_dis(self, player, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(player, vis_point)
        min_dis, min_move, min_cell = None, None, None
        next_one_points.append(("", player.x, player.y))

        for move, go_x, go_y in next_one_points:
            dis = mLegStart.get_short_length(go_x, go_y, tx, ty)

            if min_dis == None or dis < min_dis:
                min_dis, min_move = dis, move
                cell_id = mLegStart.get_cell_id(go_x, go_y)
                min_cell = cell_id

        if min_dis == None:
            mLogger.warning("[player: {}; point: ({}, {})] 无路可走".format(
                player.id, player.x, player.y))
            return -1, "", -1

        return min_dis, min_move, min_cell

    @msimulog()
    def follow_grab_player(self, follow_players):
        vis_point = set()

        # predict_go = self.get_predict_go_point()

        predict_go = [("", self.grab_player.predict_x,
                       self.grab_player.predict_y)]

        min_dis, min_index, ret_move, ret_cell = None, None, None, None
        for index, player in enumerate(follow_players):
            if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
                mLogger.info("假装追到了，或者视野预判失误")
                return True

            dis, min_move, cell_id = self.get_min_dis(
                player, self.grab_player.predict_x, self.grab_player.predict_y, vis_point)

            if min_dis == None or dis < min_dis:
                min_dis, min_index, ret_move, ret_cell = dis, index, min_move, cell_id

        if min_dis <= 1:
            vis_point.add(ret_cell)
        follow_players[min_index].move = ret_move
        used_player, used_predict_go = set(), set()
        used_player.add(min_index)

        for index, player in enumerate(follow_players):
            if index in used_player:
                continue

            grab_x, grab_y = self.grab_player.predict_x, self.grab_player.predict_y
            min_dis, ret_move, ret_cell, set_index = None, None, None, None

            for move, go_x, go_y in predict_go:
                if move in used_predict_go:
                    continue

                dis, min_move, cell_id = self.get_min_dis(
                    player, go_x, go_y, vis_point)

                if min_dis == None or dis < min_dis:
                    min_dis, ret_move, ret_cell, set_index = dis, min_move, cell_id, move

            # used_predict_go.add(set_index)
            player.move = ret_move
            if min_dis <= 1:
                vis_point.add(ret_cell)
        return False

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

    def cal_last_move(self):
        if self.grab_player.predict_x == None:
            self.grab_player_last_move = ""
            return

        # predict_x 还没有更新，是上一轮的位置
        if self.grab_player.predict_x < self.grab_player.x:
            self.grab_player_last_move = "right"
            return
        if self.grab_player.predict_x > self.grab_player.x:
            self.grab_player_last_move = "left"
            return

        if self.grab_player.predict_y < self.grab_player.y:
            self.grab_player_last_move = "down"
            return
        if self.grab_player.predict_y > self.grab_player.y:
            self.grab_player_last_move = "up"
            return

        self.grab_player_last_move = ""

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

        self.cal_last_move()
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

        # 假装追到鱼了，或者视野预判失误
        if True == self.follow_grab_player(follow_players):
            self.grab_player = None
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
        else:
            self.eat_power(power_player)


mDoThink = DoThink()
