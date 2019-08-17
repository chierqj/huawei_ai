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
from ballclient.simulation.my_leg_end import mLegEnd


class DoThink(Action):
    def __init__(self):
        super(DoThink, self).__init__()
        self.grab_player = None

    def init(self):
        self.grab_player = None

    # 选择被抓的鱼
    def select_grab_player(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            return oth_player
        return None

    # 获取一个鱼四个方向离目标点最近的dis, move, cell
    def get_min_dis(self, player, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(player, vis_point)
        min_dis, min_move, min_cell, min_url_dis = None, None, None, None

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

    # players去吃能量
    def eat_power(self, players):
        '''
        lv1: (10, 9)
        lv2: (3, 2)
        lv3: (16, 17)
        lv4: (16, 2)
        '''
        # power_area = [(10, 9), (4, 3), (14, 3), (14, 16)]     # 图三
        power_area = [(10, 5), (10, 15), (4, 2), (15, 2)]       # 图四
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

            mLogger.info(">吃能量< [player: {}; point: ({}, {}); target: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.target_power_x, player.target_power_y, player.move))

    # 获取抓鱼的鱼
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

    # 预判敌方鱼逃跑的位置
    def get_runaway_point(self, follow_players):
        info_ary = []
        for player in follow_players:
            # 假设我的鱼都朝向敌人走最短路径走了一步到达的位置是cell
            dis, move, cell = self.get_min_dis(
                player, self.grab_player.predict_x, self.grab_player.predict_y)
            info_ary.append((dis, move, cell))
            # info_ary.append(
            #     (dis, move, mLegStart.get_cell_id(player.x, player.y)))

            x, y = mLegStart.get_x_y(cell)
            mLogger.info(">我的鱼假设走一步< [player: {}; point: ({}, {}); move: {}; to: ({}, {})]".format(
                player.id, player.x, player.y, move, x, y
            ))

        max_dis, run_move, runx, runy = None, None, None, None
        direction = ["up", "down", "left", "right"]

        log_info = "\n> 敌人 < [grab_player: {}; point: ({}, {}); predict: ({}, {})]\n".format(
            self.grab_player.id, self.grab_player.x, self.grab_player.y, self.grab_player.predict_x, self.grab_player.predict_y
        )
        for d in direction:
            go_x, go_y = self.mRoundObj.real_go_point(
                self.grab_player.predict_x, self.grab_player.predict_y, d)

            if go_x == None:
                continue

            # weight = None
            weight = 0
            for _, _, cell in info_ary:
                # 根据cell来预判敌人逃跑的位置
                x, y = mLegStart.get_x_y(cell)
                dis = mLegStart.get_short_length(x, y, go_x, go_y)

                weight += float("%.3f" % (1.0 / math.exp(dis)))

                # if weight == None or dis >= weight:
                #     weight = float("%.3f" % (1.0 / math.exp(dis)))

            if max_dis == None or weight < max_dis:
                max_dis, run_move, runx, runy = weight, d, go_x, go_y

            log_info += "> {} < [go: ({}, {}); weight: {:.3f}]\n".format(
                d, go_x, go_y, weight
            )

        if runx == None:
            mLogger.info("[player: {}, point: ({}, {})] 无路可逃".format(
                self.grab_player.id, self.grab_player.predict_x, self.grab_player.predict_y))

        self.grab_player.runx, self.grab_player.runy = runx, runy

        log_info += "> 选择 < [move: {}; run: ({}, {})] \n".format(
            run_move, runx, runy
        )
        mLogger.info(log_info)

    def force_enum(self, follow_players):
        next_one_points_ary = []
        for player in follow_players:
            if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
                mLogger.info("假装追到了，或者视野预判失误")
                return True
            tmp = self.get_next_one_points(player)
            next_one_points_ary.append(tmp)

        grab_player_next = self.get_predict_next_one_points(self.grab_player)

        ans_weight, ans_move = None, None
        for m1, x1, y1 in next_one_points_ary[0]:
            for m2, x2, y2 in next_one_points_ary[1]:
                for m3, x3, y3 in next_one_points_ary[2]:
                    min_weight = None

                    # mLogger.info("[fish: {}; point: ({}, {}); move: {}; go: ({}, {})]".format(
                    #     follow_players[0].id, follow_players[0].x, follow_players[0].y,
                    #     m1, x1, y1
                    # ))
                    # mLogger.info("[fish: {}; point: ({}, {}); move: {}; go: ({}, {})]".format(
                    #     follow_players[1].id, follow_players[1].x, follow_players[1].y,
                    #     m2, x2, y2
                    # ))
                    # mLogger.info("[fish: {}; point: ({}, {}); move: {}; go: ({}, {})]".format(
                    #     follow_players[2].id, follow_players[2].x, follow_players[2].y,
                    #     m3, x3, y3
                    # ))

                    for m, x, y in grab_player_next:
                        dis1 = mLegStart.get_short_length(x1, y1, x, y)
                        dis2 = mLegStart.get_short_length(x2, y2, x, y)
                        dis3 = mLegStart.get_short_length(x3, y3, x, y)
                        weight = float("%.20f" % (1.0 / math.exp(dis1)))
                        weight += float("%.20f" % (1.0 / math.exp(dis2)))
                        weight += float("%.20f" % (1.0 / math.exp(dis3)))

                        if min_weight == None or weight < min_weight:
                            min_weight = weight

                    if ans_weight == None or min_weight < ans_weight:
                        ans_weight = min_weight
                        ans_move = [m1, m2, m3]

        for index in range(3):
            follow_players[index].move = ans_move[index]
        return False

    # 抓鱼部分
    def follow_grab_player(self, follow_players):
        # return self.force_enum(follow_players)
        vis_point = set()
        self.get_runaway_point(follow_players)

        min_dis, min_index, ret_move, ret_cell = None, None, None, None

        for index, player in enumerate(follow_players):
            if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
                mLogger.info("假装追到了，或者视野预判失误")
                return True

            dis, move, cell_id = self.get_min_dis(
                player, self.grab_player.predict_x, self.grab_player.predict_y)
            # dis, move, cell_id = self.get_min_dis(
            #     player, self.grab_player.runx, self.grab_player.runy)

            if min_dis == None or dis < min_dis:
                min_dis, ret_move, ret_cell, min_index = dis, move, cell_id, index

        follow_players[min_index].move = ret_move

        for index, player in enumerate(follow_players):
            if index == min_index:
                continue

            dis, move, cell_id = self.get_min_dis(
                player, self.grab_player.runx, self.grab_player.runy)
            # dis, move, cell_id = self.get_min_dis(
            #     player, self.grab_player.predict_x, self.grab_player.predict_y)

            player.move = move

        for player in follow_players:
            mLogger.info(">抓鱼< [player: {}; point: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.move))

    # 当鱼视野丢失的时候，预判他行走的位置
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

        mLogger.info(">预判< [player: {}; point: ({}, {}); predict: ({}, {})]".format(
            self.grab_player.id, self.grab_player.x, self.grab_player.y, self.grab_player.predict_x, self.grab_player.predict_y
        ))
        if self.grab_player.x == self.grab_player.predict_x and self.grab_player.y == self.grab_player.predict_y:
            return None

    def log_catch_num(self):
        if self.grab_player == None:
            return

        if self.grab_player.x == self.grab_player.runx and self.grab_player.y == self.grab_player.runy:
            mLegEnd.catch_run += 1
        else:
            mLegEnd.not_catch_run += 1

    def do_excute(self):
        # 自己的鱼不够四个，老实吃金币
        if self.mRoundObj.my_alive_player_num < 4:
            mLogger.info("alive_player < 4")
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
            self.grab_player = None
            return

        self.log_catch_num()

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

        follow_players, power_player = self.get_follow_power_player()

        # 假装追到鱼了，或者视野预判失误
        if True == self.follow_grab_player(follow_players):
            self.grab_player = None
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
        else:
            self.eat_power(power_player)


mDoThink = DoThink()
