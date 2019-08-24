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
        self.all_enums = None

    def init(self):
        pass

    # 逼近策略
    @msimulog()
    def approach_grab_player(self):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            player.move = self.eat_power(player)

    # vis_point是有鱼的位置，不能走
    def get_safe_num(self, grab_next_points, vis_point):
        safe_num, safe_points = len(grab_next_points), []
        danger_points = set()
        for mv, nx, ny in grab_next_points:
            flag = True
            for cell in vis_point:
                x, y = mLegStart.get_x_y(cell)
                dis = mLegStart.get_short_length(x, y, nx, ny)
                if dis <= 1:
                    safe_num -= 1
                    danger_points.add(cell)
                    flag = False
                    break
            if True == flag:
                safe_points.append((mv, nx, ny))

        return safe_num, safe_points, danger_points

    # 满足不满足围捕条件
    def match_grab(self, grab_player, grab_next_points, vis_point, param):
        '''
        1. 视野丢失好几个回合，不满足
        2. 安全位置超过阈值，不满足
        '''
        if grab_player.lost_vision_num > 3:
            return False
        limit_safe_num, safe_points, danger_points = self.get_safe_num(
            grab_next_points, vis_point)

        param["limit_safe_num"] = limit_safe_num
        param["safe_points"] = safe_points
        param["danger_points"] = danger_points

        if limit_safe_num >= 3:
            return False
        return True

    # 获取一个鱼四个方向离目标点最近的dis, move, cell
    def get_min_dis(self, x, y, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(x, y, vis_point)
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

    # 敌人的安全位置为0，增员
    def increase_player(self, grab_player, danger_points):
        ret_dis, ret_key, ret_move = None, None, None
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            cell = mLegStart.get_cell_id(player.x, player.y)
            if cell in danger_points:
                player.move = ""
                continue

            dis, move, cell = self.get_min_dis(
                player.x, player.y, grab_player.predict_x, grab_player.predict_y, danger_points)
            if ret_dis == None or dis < ret_dis:
                ret_dis, ret_key, ret_move = dis, k, move

        if ret_key != None:
            mLogger.info("[增员] [player: {}; point: ({}, {})]".format(
                mPlayers[ret_key].id, mPlayers[ret_key].x, mPlayers[ret_key].y
            ))
            mPlayers[ret_key].move = ret_move

    # 实施抓捕(被抓的鱼，被抓的鱼下一个可以行走的位置，被抓的鱼这一回合的安全位置数目)

    def force_grab(self, grab_player, grab_next_points, limit_safe_num):
        '''
        1. 所有的鱼的枚举状态
        2. 枚举某一个状态的时候
            a. 安全位置数目
            b. 我的鱼到敌人的鱼的总距离
            b. 满足的时候，找出限制走位的鱼，不限制的就不算
        '''

        result = None
        for enum in self.all_enums:
            vis_point = set()
            for pid, em, ex, ey in enum:
                cell = mLegStart.get_cell_id(ex, ey)
                vis_point.add(cell)

            flag = True
            for move, go_x, go_y in grab_next_points:
                new_next = self.get_next_one_points(go_x, go_y, vis_point)
                safe_num, safe_points, danger_points = self.get_safe_num(
                    new_next, vis_point)
                if safe_num > limit_safe_num:
                    flag = False
                    break
            if flag == False:
                continue

            sum_dis, action = 0, []
            for pid, em, ex, ey in enum:
                cell = mLegStart.get_cell_id(ex, ey)
                if cell in danger_points:
                    action.append((pid, em, ex, ey))
                    sum_dis += mLegStart.get_short_length(
                        ex, ey, grab_player.predict_x, grab_player.predict_y)

            if result == None:
                result = {
                    'safe_num': safe_num,
                    'sum_dis': sum_dis,
                    'action': action
                }
                continue
            if safe_num < result['safe_num'] or (safe_num == result['safe_num'] and sum_dis < result['sum_dis']):
                result = {
                    'safe_num': safe_num,
                    'sum_dis': sum_dis,
                    'action': action
                }

        return result

    def select_best_result(self, results):
        return results[0]

    def eat_power(self, player):
        next_one_points = self.get_next_one_points(player.x, player.y)
        rd = random.randint(0, len(next_one_points) - 1)
        return next_one_points[rd][0]

    # 围捕策略
    def force_grab_player(self):
        '''
        1. 敌人四条鱼，找能抓的鱼，暴力枚举
        2. 每一条被抓的鱼，暴力枚举会返回一个结果
            a. 敌人的可行位置
            b. 敌人的安全位置
            c. 抓捕的鱼的动作
            d. 抓捕之后敌人的安全位置
            e. 或者None
        3. 在所有的抓捕动作中，选择一个收益最大的
        '''
        vis_point = set()
        next_one_points_ary = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            cell = mLegStart.get_cell_id(player.x, player.y)
            vis_point.add(cell)
            next_one_points = self.get_next_one_points(player.x, player.y)
            next_one_points.append(("", player.x, player.y))
            next_one_points = [(player.id, it[0], it[1], it[2])
                               for it in next_one_points]

            next_one_points_ary.append(next_one_points)

        self.all_enums = self.get_all_enums(next_one_points_ary)

        success, results = False, []
        for k, oth_player in othPlayers.iteritems():
            if oth_player.predict_x == None:
                mLogger.info("[player: {} 预判不到位置]\n".format(oth_player.id))
                continue

            grab_next_points = self.get_next_one_points(
                oth_player.predict_x, oth_player.predict_y, vis_point)

            param = dict()
            if False == self.match_grab(oth_player, grab_next_points, vis_point, param):
                continue

            limit_safe_num = param['limit_safe_num']
            if limit_safe_num == 0:
                self.increase_player(oth_player, param['danger_points'])

            ret = self.force_grab(oth_player, grab_next_points, limit_safe_num)

            mLogger.info("[敌人] [player: {}; point: ({}, {}); grab_next: {}]".format(
                oth_player.id, oth_player.predict_x, oth_player.predict_y, grab_next_points
            ))
            mLogger.info("[初始] [{}]".format(param))
            mLogger.info("[结果] [{}]\n".format(ret))

            if ret == None:
                continue
            success = True
            results.append(ret)

        if False == success:
            return False

        best_result = self.select_best_result(results)
        mLogger.info("[最优] [{}]\n".format(best_result))
        ans_move = dict()
        for pid, em, ex, ey in best_result["action"]:
            ans_move[pid] = em

        for k, player in mPlayers.iteritems():
            if k in ans_move:
                player.move = ans_move[k]
            else:
                player.move = self.eat_power(player)
        return True

    def update_predict(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                self.predict_player_point(oth_player)
                oth_player.lost_vision_num += 1
            else:
                oth_player.predict_x, oth_player.predict_y = oth_player.x, oth_player.y,
                oth_player.lost_vision_num = 0
    # 执行入口

    def do_excute(self):
        self.update_predict()
        if True == self.force_grab_player():
            return
        self.approach_grab_player()


mDoThink = DoThink()
