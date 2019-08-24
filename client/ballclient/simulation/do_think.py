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
        self.need_log_run = False
        self.if_predict_right = False

    def init(self):
        self.grab_player = None
        self.need_log_run = False
        self.if_predict_right = False

    # 选择被抓的鱼
    def select_grab_player(self):
        max_score, max_key = None, None
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            if max_score == None or oth_player.score > max_score:
                max_score, max_key = max_score, k
        if max_key == None:
            return None
        return othPlayers[max_key]

    # 获取一个鱼四个方向离目标点最近的dis, move, cell
    def get_min_dis(self, player, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(
            player.x, player.y, vis_point)
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
        1. 选取几个矿区，收益最大。矿区的数目根据players的数目决定。
        2. 每个player去找最近的矿区挖矿
        3. 挖矿
            3.1 矿区内有能量，就去找最近的去挖矿
            3.2 矿区内没能量，就去固定收益点呆着
        '''
        # power_area = [(10, 9), (4, 3), (14, 3), (14, 16)]     # 图三
        # power_area = [(10, 5), (10, 15), (4, 2), (15, 2)]       # 图四
        power_area = [(10, 5), (10, 15), (3, 15), (16, 16)]       # 图五
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
            min_dis, min_move = None, None
            for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
                if power.visiable == False:
                    continue
                vision = mLegStart.msg['msg_data']['map']['vision']
                if power.x > player.target_power_x + vision or power.x < player.target_power_x - vision:
                    continue
                if power.y > player.target_power_y + vision or power.y < player.target_power_y - vision:
                    continue

                dis, move, _ = self.get_min_dis(player, power.x, power.y)
                if min_dis == None or dis < min_dis:
                    min_dis, min_move = dis, move

            if min_move != None:
                player.move = min_move
                continue

            if player.x == player.target_power_x and player.y == player.target_power_y:
                player.move = ""
            else:
                dis, min_move, _ = self.get_min_dis(
                    player, player.target_power_x, player.target_power_y)
                player.move = min_move

            mLogger.info(">吃能量< [player: {}; point: ({}, {}); target: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.target_power_x, player.target_power_y, player.move))

    # 获取三个抓鱼的鱼以及吃能量的鱼
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

    # 距离不是很近的时候，预判敌方鱼逃跑的位置
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

    # 获取所有可能情况
    # def get_enums(self, follow_players):
    #     '''
    #     1. 抓鱼的鱼的枚举位置不能重复，包括原地不动
    #     2. 敌人的移动位置不能包括我的鱼这一回合在的位置
    #     '''
    #     vis_point = set()
    #     next_one_points_ary = []
    #     for player in follow_players:
    #         tmp = self.get_next_one_points(player.x, player.y)
    #         tmp.append(("", player.x, player.y))
    #         next_one_points_ary.append(tmp)
    #         cell = mLegStart.get_cell_id(player.x, player.y)
    #         vis_point.add(cell)

    #     grab_player_next = self.get_next_one_points(
    #         self.grab_player.predict_x, self.grab_player.predict_y, vis_point)
    #     grab_player_next.append(
    #         ("", self.grab_player.predict_x, self.grab_player.predict_y))

    #     all_enums = []
    #     for m1, x1, y1 in next_one_points_ary[0]:
    #         for m2, x2, y2 in next_one_points_ary[1]:
    #             if x1 == x2 and y1 == y2:
    #                 continue
    #             for m3, x3, y3 in next_one_points_ary[2]:
    #                 if x1 == x3 and y1 == y3:
    #                     continue
    #                 if x2 == x3 and y2 == y3:
    #                     continue
    #                 all_enums.append(
    #                     [(m1, x1, y1), (m2, x2, y2), (m3, x3, y3)])
    #     return all_enums, grab_player_next

    # vis_point是有鱼的位置，不能走
    def get_safe_num(self, grab_next_points, vis_point):
        safe_num, safe_points = len(grab_next_points), []
        for mv, nx, ny in grab_next_points:
            flag = True
            for cell in vis_point:
                x, y = mLegStart.get_x_y(cell)
                dis = mLegStart.get_short_length(x, y, nx, ny)
                if dis <= 1:
                    safe_num -= 1
                    flag = False
                    break
            if True == flag:
                safe_points.append((mv, nx, ny))

        return safe_num, safe_points

    # 判断是不是需要暴力枚举，只有在视野范围内才暴力

    def match_need_force_enum(self, follow_players, vis_point, safe_num):
        grab_next_points = self.get_next_one_points(
            self.grab_player.x, self.grab_player.y, vis_point)

        return True

    def get_init_vis_point(self, follow_players):
        vis_point = set()
        for player in follow_players:
            cell = mLegStart.get_cell_id(player.x, player.y)
            vis_point.add(cell)
        return vis_point

    def get_weight_dis(self, follow_players, enum, x, y):
        m1, x1, y1 = enum[0]
        m2, x2, y2 = enum[1]
        m3, x3, y3 = enum[2]

        vis_point = set()
        for i, player in enumerate(follow_players):
            cell = mLegStart.get_cell_id(player.x, player.y)
            vis_point.add(cell)
            cell = mLegStart.get_cell_id(enum[i][1], enum[i][2])
            vis_point.add(cell)

        weight = self.get_next_one_num(x, y, vis_point)
        return weight

    # 暴力枚举位置
    def force_enum(self, follow_players):
        '''
        1. vis_point: 表示我的鱼现在在的位置；敌人一定不能走
        2. grab_bext_points: 看看敌人可以走的位置
        3. init_safe_num: 敌人在可以走的这几个位置中，安全的位置有几个
        '''
        vis_point = self.get_init_vis_point(follow_players)
        grab_next_points = self.get_next_one_points(
            self.grab_player.predict_x, self.grab_player.predict_y, vis_point)
        init_safe_num, init_safe_points = self.get_safe_num(
            grab_next_points, vis_point)
        init_can_go_num = len(grab_next_points)

        if init_safe_num > 2:
            return False

        mLogger.info("> 敌人 < [player: {}; point: ({}, {})]".format(
            self.grab_player.id, self.grab_player.predict_x, self.grab_player.predict_y
        ))
        mLogger.info("{}".format(self.get_next_one_points(1, 19)))
        mLogger.info("[敌人可行位置: {}; {}]".format(
            init_can_go_num, grab_next_points))
        mLogger.info("[敌人安全位置: {}; {}]".format(
            init_safe_num, init_safe_points))

        # return False

        next_one_points_ary = []
        for player in follow_players:
            next_one_points = self.get_next_one_points(player.x, player.y)
            next_one_points_ary.append(next_one_points)
        all_enums = self.get_all_enums(next_one_points_ary)

        min_safe_num, min_can_go_num, ans_move = None, None, None
        for enum in all_enums:
            import copy
            # tmp_vis_point = copy.deepcopy(vis_point)
            tmp_vis_point = set()
            for enm, enx, eny in enum:
                cell = mLegStart.get_cell_id(enx, eny)
                tmp_vis_point.add(cell)
            safe_num, _ = self.get_safe_num(grab_next_points, tmp_vis_point)
            can_go_num = self.get_next_one_num(
                self.grab_player.predict_x, self.grab_player.predict_y, tmp_vis_point)

            if safe_num > init_safe_num:
                continue
            if min_safe_num == None:
                min_safe_num, min_can_go_num = safe_num, can_go_num
                ans_move = [enum[0][0], enum[1][0], enum[2][0]]
                continue
            if safe_num < min_safe_num or (safe_num == min_safe_num and can_go_num < min_can_go_num):
                min_safe_num, min_can_go_num = safe_num, can_go_num
                ans_move = [enum[0][0], enum[1][0], enum[2][0]]

        if ans_move == None:
            return False

        for index in range(3):
            follow_players[index].move = ans_move[index]
            mLogger.info("> 枚举 < [player: {}; point: ({}, {}); move: {}]".format(
                follow_players[index].id, follow_players[index].x, follow_players[index].y, ans_move[index]
            ))
        return True

    # 抓鱼部分
    def follow_grab_player(self, follow_players):
        '''
        1. 如果到了可以暴力枚举的条件，就暴力枚举
        2. 不能暴力枚举，就尽量往敌人靠
        '''
        if True == self.force_enum(follow_players):
            return

        vis_point = set()
        self.get_runaway_point(follow_players)

        min_dis, min_index, ret_move, ret_cell = None, None, None, None

        for index, player in enumerate(follow_players):
            dis, move, cell_id = self.get_min_dis(
                player, self.grab_player.predict_x, self.grab_player.predict_y)
            # dis, move, cell_id = self.get_min_dis(
            #     player, self.grab_player.runx, self.grab_player.runy)

            if min_dis == None or dis < min_dis:
                min_dis, ret_move, ret_cell, min_index = dis, move, cell_id, index

        follow_players[min_index].move = ret_move
        vis_point.add(ret_cell)

        for index, player in enumerate(follow_players):
            if index == min_index:
                continue

            dis, move, cell_id = self.get_min_dis(
                player, self.grab_player.runx, self.grab_player.runy, vis_point)
            # dis, move, cell_id = self.get_min_dis(
            #     player, self.grab_player.predict_x, self.grab_player.predict_y)
            vis_point.add(cell_id)

            player.move = move

        for player in follow_players:
            mLogger.info(">抓鱼< [player: {}; point: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.move))

    # 判断有没有抓住鱼
    def match_catch_grab(self, follow_players):
        for player in follow_players:
            if player.x == self.grab_player.predict_x and player.y == self.grab_player.predict_y:
                mLogger.info("假装追到了，或者视野预判失误")
                return True
        return False

    # 记录预判位置次数
    def log_catch_num(self):
        if self.grab_player == None:
            return

        if self.need_log_run == False:
            return

        self.need_log_run = False
        self.if_predict_right = False

        if self.grab_player.x == self.grab_player.runx and self.grab_player.y == self.grab_player.runy:
            mLegEnd.catch_run += 1
            self.if_predict_right = True
        else:
            mLogger.info("上一回合预判位置错误")
            mLegEnd.not_catch_run += 1

    # 入口调用
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
            self.predict_player_point(self.grab_player)

        follow_players, power_player = self.get_follow_power_player()

        # 假装追到鱼了，或者视野预判失误
        if True == self.match_catch_grab(follow_players):
            self.grab_player = None
            players = [p for k, p in mPlayers.iteritems() if p.sleep == False]
            self.eat_power(players)
        else:
            self.follow_grab_player(follow_players)
            self.eat_power(power_player)


mDoThink = DoThink()
