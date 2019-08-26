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
        self.answer_point = set()

    def init(self):
        pass

    # 逼近策略
    def approach_grab_player(self):
        for k, grab_player in othPlayers.iteritems():
            if grab_player.predict_x == None:
                continue
            if grab_player.visiable == False and grab_player.lost_vision_num > 2:
                continue
            for k, player in mPlayers.iteritems():
                if player.sleep == True:
                    continue
                dis, move, cell = self.get_min_dis(
                    player.x, player.y, grab_player.predict_x, grab_player.predict_y)
                player.move = move
                mLogger.info("[逼近] [player: {}; point: ({}, {}); move: {}]".format(
                    player.id, player.x, player.y, player.move
                ))
            return True
        return False

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
    def increase_player(self, grab_player, used_players):
        ret_dis, ret_key, ret_move = None, None, None
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in used_players:
                continue

            dis, move, cell = self.get_min_dis(
                player.x, player.y, grab_player.predict_x, grab_player.predict_y)
            if ret_dis == None or dis < ret_dis:
                ret_dis, ret_key, ret_move = dis, k, move

        mLogger.info("开始增员以及吃能量......")
        mPlayers[ret_key].move = ret_move
        mLogger.info("[增员] [player: {}; point: ({}, {}); move: {}]".format(
            mPlayers[ret_key].id, mPlayers[ret_key].x, mPlayers[ret_key].y, mPlayers[ret_key].move
        ))

        eat_power_players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in used_players:
                continue
            if k == ret_key:
                continue
            eat_power_players.append(player)
        self.eat_power(eat_power_players)

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
            danger_points = set()
            max_safe_num = None
            for move, go_x, go_y in grab_next_points:
                new_next = self.get_next_one_points(go_x, go_y, vis_point)
                safe_num, safe_points, tmp_danger_points = self.get_safe_num(
                    new_next, vis_point)
                if safe_num > limit_safe_num:
                    flag = False
                    break

                
                danger_points = danger_points.union(tmp_danger_points)
                if max_safe_num == None or safe_num > max_safe_num:
                    max_safe_num = safe_num
            if flag == False:
                continue
            # safe_num, safe_points, danger_points = self.get_safe_num(grab_next_points, vis_point)
            # if safe_num > limit_safe_num:
            #     continue
            # max_safe_num = safe_num

            sum_dis, action = 0, []
            sum_url_dis = 0
            for pid, em, ex, ey in enum:
                cell = mLegStart.get_cell_id(ex, ey)
                if cell in danger_points:
                    action.append((pid, em, ex, ey))
                    sum_dis += mLegStart.get_short_length(
                        ex, ey, grab_player.predict_x, grab_player.predict_y)
                    sum_url_dis += (ex - grab_player.predict_x) ** 2 + (ey - grab_player.predict_y) ** 2

            if result == None:
                result = {
                    'max_safe_num': max_safe_num,
                    'sum_dis': sum_dis,
                    'sum_url_dis': sum_url_dis,
                    'action': action
                }
                continue

            # 安全位置小
            if max_safe_num < result['max_safe_num']:
                result = {
                    'max_safe_num': max_safe_num,
                    'sum_dis': sum_dis,
                    'sum_url_dis': sum_url_dis,
                    'action': action
                }
            elif max_safe_num == result['max_safe_num']:
                # 安全位置一样但是sumdis小或者sumdis一样但是欧式距离小
                if sum_dis < result['sum_dis'] or (sum_dis == result['sum_dis'] and sum_url_dis < result['sum_url_dis']):
                    result = {
                        'max_safe_num': max_safe_num,
                        'sum_dis': sum_dis,
                        'sum_url_dis': sum_url_dis,
                        'action': action
                    }

        return result

    # 选择一个最优的决策
    def select_best_result(self, results):
        def cmp(it1, it2):
            if it1['limit_safe_num'] == it2['limit_safe_num']:
                if it1['init_go_num'] == it2['init_go_num']:
                    if it1['sum_dis'] == it2['sum_dis']:
                        if it1['sum_url_dis'] < it2['sum_url_dis']:
                            return -1
                        return 1
                    if it1['sum_dis'] < it2['sum_dis']:
                        return -1
                    return 1
                if it1['init_go_num'] < it2['init_go_num']:
                    return -1
                return 1
            if it1['limit_safe_num'] < it2['limit_safe_num']:
                return -1
            return 1
        results = sorted(results, cmp)

        best_result = results[0]

        if best_result['limit_safe_num'] == 0:
            used_players = set()
            for it in best_result['action']:
                used_players.add(it[0])
            self.increase_player(best_result['grab_player'], used_players)            

        mLogger.info("[最优] [{}]\n".format(best_result))
        return best_result

    # 判断是否在(x, y)是否在(px, py)视野当中
    def judge_in_vision(self, px, py, x, y):
        vision = mLegStart.msg['msg_data']['map']['vision']
        if x < px - vision or x > px + vision:
            return False
        if y < py - vision or y > py + vision:
            return False
        return True

    # 吃能量
    def eat_power(self, players):
        powers = self.mRoundObj.msg['msg_data'].get('power', [])
        vis_index = set()
        for power in powers:
            min_dis, ret_index, ret_move = None, None, None
            for index, player in enumerate(players):
                if player.sleep == True:
                    continue
                if index in vis_index:
                    continue
                dis, move, cell = self.get_min_dis(
                    player.x, player.y, power['x'], power['y'])
                if min_dis == None or dis < min_dis:
                    min_dis, ret_index, ret_move = dis, index, move
            if ret_index != None:
                players[ret_index].move = ret_move
                mLogger.info("[能量] [player: {}; point: ({}, {}); move: {}]".format(
                    players[ret_index].id, players[ret_index].x, players[ret_index].y, players[ret_index].move
                ))
                vis_index.add(ret_index)
        for index, player in enumerate(players):
            if index in vis_index:
                continue
            self.travel(player)

    # 探路巡航
    def travel(self, player):
        next_one_points = self.get_next_one_points(player.x, player.y)
        min_cnt, ret_move = None, None
        for mv, nx, ny in next_one_points:
            cell = mLegStart.get_cell_id(nx, ny)
            cnt = player.vis_point_count.get(cell, 0)
            if min_cnt == None or cnt < min_cnt:
                min_cnt, ret_move = cnt, mv
        player.move = ret_move

        mLogger.info("[巡航] [player: {}; point: ({}, {}); move: {}]".format(
            player.id, player.x, player.y, player.move
        ))

    # 直接吃，对面无路可走
    def just_eat_player(self, grab_player):
        min_dis, min_key, min_move = None, None, None
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            dis, move, cell = self.get_min_dis(player.x, player.y, grab_player.predict_x, grab_player.predict_y)
            if min_dis == None or dis < min_dis:
                min_dis, min_key, min_move = dis, k, move
        mPlayers[min_key].move = move
    
        mLogger.info("[直接吃] [player: {}; point: ({}, {}); move: {}]".format(
            mPlayers[min_key].id, mPlayers[min_key].x, mPlayers[min_key].y, mPlayers[min_key].move
        ))

        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if k != min_key:
                players.append(player)
        self.eat_power(players)            

    # 围捕策略
    def force_grab_player(self):
        '''
        1. 敌人四条鱼，找能抓的鱼，暴力枚举
        2. 每一条被抓的鱼，暴力枚举会返回一个结果
            a. 抓捕的鱼的动作
            b. 抓捕之后敌人的安全位置
            c. 或者None
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
                mLogger.info(
                    "[敌人] [player: {} 预判不到位置; 不符合]".format(oth_player.id))
                continue

            grab_next_points = self.get_next_one_points(
                oth_player.predict_x, oth_player.predict_y, vis_point)
            grab_next_points.append(("", oth_player.predict_x, oth_player.predict_y))

            mLogger.info("[敌人] [player: {}; point: ({}, {}); grab_next: {}]".format(
                oth_player.id, oth_player.predict_x, oth_player.predict_y, grab_next_points
            ))

            if len(grab_next_points) == 0:
                mLogger.info("[结果] [可行位置为0，找个最近的直接吃]")
                self.just_eat_player(oth_player)
                return True


            param = dict()
            flag = self.match_grab(
                oth_player, grab_next_points, vis_point, param)
            mLogger.info("[初始] [{}]".format(param))

            if False == flag:
                mLogger.info("[结果] [不符合]\n".format(oth_player.id))
                continue

            limit_safe_num = param['limit_safe_num']
            # if limit_safe_num == 0:
            #     mLogger.info("[结果] [安全位置为0，增员或者直接干掉]\n".format(oth_player.id))
            #     self.increase_player(oth_player, param['danger_points'])
            #     return True

            ret = self.force_grab(
                oth_player, grab_next_points, limit_safe_num)
            mLogger.info("[结果] [{}]\n".format(ret))

            if ret == None:
                continue
            success = True
            ret['init_go_num'] = len(grab_next_points)
            ret['limit_safe_num'] = limit_safe_num
            ret['grab_player'] = oth_player
            results.append(ret)

        if False == success:
            return False

        best_result = self.select_best_result(results)
        ans_move = dict()
        for pid, em, ex, ey in best_result["action"]:
            ans_move[pid] = em

        eat_power_players = []
        for k, player in mPlayers.iteritems():
            if k in ans_move:
                player.move = ans_move[k]
            else:
                eat_power_players.append(player)
        self.eat_power(eat_power_players)
        return True

    def update_predict(self):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                self.predict_player_point(oth_player)
                oth_player.lost_vision_num += 1
            else:
                oth_player.predict_x, oth_player.predict_y = oth_player.x, oth_player.y,
                oth_player.lost_vision_num = 0
            mLogger.info("[player: {}; point: ({}, {}); predict: ({}, {}); lost_vision_num: {}]".format(
                oth_player.id, oth_player.x, oth_player.y, oth_player.predict_x, oth_player.predict_y, oth_player.lost_vision_num
            ))

    def all_eat_or_travel(self):
        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            players.append(player)
        self.eat_power(players)

    # 执行入口
    def do_excute(self):
        mLogger.info("开始预判位置......")
        self.update_predict()
        mLogger.info("开始进行围剿......")
        if True == self.force_grab_player():
            return
        mLogger.info("围剿失败，开始逼近......")
        if True == self.approach_grab_player():
            return
        mLogger.info("逼近失败，全员吃能量或者巡航......")
        self.all_eat_or_travel()


mDoThink = DoThink()
