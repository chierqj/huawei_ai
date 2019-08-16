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

    def select_grab_player(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            if oth_player.score < 5:
                continue
            return oth_player
        return None

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

            # mLogger.info("[player: {}; point: ({}, {}); target: ({}, {})]".format(
            #     player.id, player.x, player.y, player.target_power_x, player.target_power_y))

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

    def get_runaway_point(self):
        direction = ["up", "down", "left", "right"]

        min_dis, runx, runy = None, None, None
        for d in direction:
            go_x, go_y = self.mRoundObj.real_go_point(
                self.grab_player.predict_x, self.grab_player.predict_y, d)

            if go_x == None:
                continue

            sum_dis = 0
            for k, player in mPlayers.iteritems():
                dis = mLegStart.get_short_length(
                    player.x, player.y, go_x, go_y)
                sum_dis += float("%.5f" % (1.0 / math.exp(dis)))

            if min_dis == None or sum_dis < min_dis:
                min_dis, runx, runy = sum_dis, go_x, go_y

        if runx == None:
            mLogger.info("[player: {}, point: ({}, {})] 无路可逃".format(
                self.grab_player.id, self.grab_player.predict_x, self.grab_player.predict_y))

        return runx, runy

    def get_min_dis(self, player, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(player, vis_point)
        min_dis, min_move, min_cell, min_url_dis = None, None, None, None
        # next_one_points.append(("", player.x, player.y))

        for move, go_x, go_y in next_one_points:
            dis = mLegStart.get_short_length(go_x, go_y, tx, ty)
            url_dis = (go_x - tx) ** 2 + (go_y - ty) ** 2

            if min_dis == None or dis < min_dis or (dis == min_dis and url_dis < min_url_dis):
                min_dis, min_move, min_url_dis = dis, move, url_dis
                cell_id = mLegStart.get_cell_id(go_x, go_y)
                min_cell = cell_id

        if min_dis == None:
            mLogger.warning("[player: {}; point: ({}, {})] 无路可走".format(
                player.id, player.x, player.y))
            return -1, "", -1

        return min_dis, min_move, min_cell

    def follow_grab_player(self, follow_players):
        vis_point = set()
        runx, runy = self.get_runaway_point()

        min_dis, min_index, ret_move, ret_cell = None, None, None, None

        for index, player in enumerate(follow_players):
            if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
                mLogger.info("假装追到了，或者视野预判失误")
                return True

            dis, move, cell_id = self.get_min_dis(
                player, self.grab_player.predict_x, self.grab_player.predict_y)
            # dis, move, cell_id = self.get_min_dis(player, runx, runy)


            if min_dis == None or dis < min_dis:
                min_dis, ret_move, ret_cell, min_index = dis, move, cell_id, index

        follow_players[min_index].move = ret_move


        mLogger.info("[player: {}; point: ({}, {}); run: ({}, {})]".format(
            self.grab_player.id, self.grab_player.predict_x, self.grab_player.predict_y, runx, runy))

        for index, player in enumerate(follow_players):
            if index == min_index:
                continue

            dis, move, cell_id = self.get_min_dis(player, runx, runy)
            # dis, move, cell_id = self.get_min_dis(
            #     player, self.grab_player.predict_x, self.grab_player.predict_y)

            player.move = move

    def predict_grab_player(self):
        vision = mLegStart.msg['msg_data']['map']['vision']
        next_one_points = self.get_next_one_points(self.grab_player, set())

        for move, go_x, go_y in next_one_points:
            have_view = False
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
