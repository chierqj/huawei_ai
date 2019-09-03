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
        self.LIMIT_GRAB_DIS = 7  # 小于这个数字，才逼近
        self.LIMIT_ENUM = 2  # 四个方位最小距离小于等于这个，才算枚举
        self.LIMIT_GRAB_STEP = 20
        self.grab_player = None
        self.USED_PLAYER_ID = set()

    def init(self):
        self.all_enums = None
        self.HAVE_RET_POINT.clear()
        self.grab_player = None
        self.USED_PLAYER_ID.clear()

    # 确定要抓的鱼
    def confirm_grab_player(self):
        if self.grab_player != None and self.grab_player.lost_vision_num < self.LIMIT_LOST_VISION:
            return True
        ret_key = None
        for k, player in othPlayers.iteritems():
            if player.predict_x == None:
                continue
            # if player.score <= 10:
            #     continue
            if player.visiable == True:
                self.grab_player = player
                return True
            if player.lost_vision_num < self.LIMIT_LOST_VISION:
                ret_key = k
        if ret_key == None:
            self.grab_player = None
            return False
        self.grab_player = othPlayers[ret_key]
        return True

    # 判断x，y这个位置有没有我的鱼
    def judge_in_mplayer(self, x, y):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.x == x and player.y == y:
                return True
        return False

    def get_close(self, player):
        dis, move, cell = self.get_min_dis(
            player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y, self.HAVE_RET_POINT)
        player.move = move
        mLogger.info("[逼近] [player: {}; point: ({}, {}); move: {}]\n".format(
            player.id, player.x, player.y, player.move
        ))

    # 传送门是x, y,敌人到这里是step步，used_player_key是用过的鱼的key
    def get_near_player(self, x, y, step):
        '''
        针对每个传送门，都要找个我的人，要么堵门，要么逼近
        '''
        ret_dis, ret_key, ret_move = None, None, None
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            dis, move, cell = self.get_min_dis(
                player.x, player.y, x, y, self.HAVE_RET_POINT)

            if ret_dis == None or dis < ret_dis:
                ret_dis, ret_key, ret_move = dis, k, move

        if ret_key == None:
            return False
        self.USED_PLAYER_ID.add(ret_key)
        mLogger.info("[传送门: ({}, {}); 敌人的距离: {}]".format(x, y, step))
        # 逼近
        if step - ret_dis >= 2 or (False == self.judge_in_vision(player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)):
            self.get_close(mPlayers[ret_key])
        else:
            mPlayers[ret_key].move = ret_move
            mLogger.info("[卡门] [player: {}; point: ({}, {}); move: {}; 我的距离: {}]\n".format(
                mPlayers[ret_key].id, mPlayers[ret_key].x, mPlayers[ret_key].y, mPlayers[ret_key].move, ret_dis, step
            ))
        # self.add_have_go(mPlayers[ret_key])
        return True

    # 开始抓捕
    def start_grab(self):
        def bfs():
            import Queue
            q = Queue.Queue()
            vis = set()

            st = mLegStart.get_cell_id(
                self.grab_player.predict_x, self.grab_player.predict_y)
            q.put((0, self.grab_player.predict_x, self.grab_player.predict_y))
            vis.add(st)
            while False == q.empty():
                ustep, ux, uy = q.get()
                next_one_points = self.get_next_one_points(ux, uy)
                for mv, vx, vy in next_one_points:
                    vcell_id = mLegStart.get_cell_id(vx, vy)
                    if vcell_id in vis:
                        continue

                    # vell是ux，uy扩展一步之后地图上的元素，判断是不是传送门
                    gox, goy = self.mRoundObj.go_next(ux, uy, mv)
                    vcell = mLegStart.get_graph_cell(gox, goy)

                    if mLegStart.match_tunnel(vcell):
                        flag = self.get_near_player(vx, vy, ustep + 1)
                        if flag == False:
                            return
                        new_next = self.get_next_one_points(vx, vy)
                        for nm, nnx, nny in new_next:
                            ncell = mLegStart.get_cell_id(nnx, nny)
                            vis.add(ncell)
                    else:
                        if True == self.judge_in_mplayer(vx, vy):
                            continue
                        q.put((ustep + 1, vx, vy))
                    vis.add(vcell_id)
        bfs()
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            self.get_close(player)

    # vis_point是有鱼的位置，不能走
    def get_safe_num(self, grab_next_points, vis_point):
        safe_num, safe_points = len(grab_next_points), []
        danger_points = set()
        for mv, nx, ny in grab_next_points:
            flag = True
            for cell in vis_point:
                x, y = mLegStart.get_x_y(cell)
                dis1 = mLegStart.get_short_length(x, y, nx, ny)
                dis2 = mLegStart.get_short_length(nx, ny, x, y)
                up = 1
                if mv == "":
                    up = 2
                if dis1 <= up and dis2 <= up:
                    safe_num -= 1
                    danger_points.add(cell)
                    flag = False
                    break
            if True == flag:
                safe_points.append((mv, nx, ny))

        return safe_num, safe_points, danger_points

    # 直接吃，对面无路可走
    def just_eat_player(self):
        min_dis, min_key, min_move = None, None, None
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            dis, move, cell = self.get_min_dis(
                player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
            if min_dis == None or dis < min_dis:
                min_dis, min_key, min_move = dis, k, move

        mPlayers[min_key].move = move
        self.USED_PLAYER_ID.add(min_key)
        # self.add_have_go(mPlayers[min_key])

        mLogger.info("[直接吃] [player: {}; point: ({}, {}); move: {}]".format(
            mPlayers[min_key].id, mPlayers[min_key].x, mPlayers[min_key].y, mPlayers[min_key].move
        ))

        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            if k != min_key:
                players.append(player)
        self.many_players_eat_power(players)

    # 满足不满足围捕条件
    def match_grab(self, param):
        '''
        1. 视野丢失好几个回合，不满足
        2. 安全位置超过阈值，不满足
        '''
        vis_point = set()
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            cell = mLegStart.get_cell_id(player.x, player.y)
            vis_point.add(cell)
        grab_next_points = self.get_next_one_points(
            self.grab_player.predict_x, self.grab_player.predict_y, vis_point)
        grab_next_points.append(
            ("", self.grab_player.predict_x, self.grab_player.predict_y))

        limit_safe_num, safe_points, danger_points = self.get_safe_num(
            grab_next_points, vis_point)

        param["limit_safe_num"] = limit_safe_num
        param["grab_next_points"] = grab_next_points
        param["safe_points"] = safe_points
        param["danger_points"] = danger_points

        # if len(grab_next_points) == 1:
        #     return True
        # return False

        if limit_safe_num >= 3:
            return False
        return True

    # 获取每一个枚举情况的result
    def get_each_enum_result(self, enum, grab_next_points, limit_safe_num):
        # 第一步先标记不能走的位置，且我的鱼不重叠
        vis_point = set()
        for pid, em, ex, ey in enum:
            cell = mLegStart.get_cell_id(ex, ey)
            vis_point.add(cell)
            for pid1, em1, ex1, ey1 in enum:
                if pid == pid1:
                    continue
                if ex == ex1 and ey == ey1:
                    return None

        # 第二步获取敌人五个动作下的最大安全位置,不能超过现在的安全位置
        danger_points = set()
        max_safe_num = None
        for move, go_x, go_y in grab_next_points:
            new_next = self.get_next_one_points(go_x, go_y, vis_point)
            new_next.append(("", go_x, go_y))
            safe_num, safe_points, tmp_danger_points = self.get_safe_num(
                new_next, vis_point)
            if max_safe_num == None or safe_num > max_safe_num:
                max_safe_num = safe_num
        if max_safe_num == None or max_safe_num > limit_safe_num:
            return None

        # 第三部获取一些评分信息，用来排序
        sum_dis, sum_url_dis, action = 0, 0, []
        use_cell = set()
        for pid, em, ex, ey in enum:
            cell = mLegStart.get_cell_id(ex, ey)
            if cell in use_cell:
                continue
            if cell in danger_points:
                use_cell.add(cell)
                action.append((pid, em, ex, ey))
                sum_dis += mLegStart.get_short_length(
                    ex, ey, self.grab_player.predict_x, self.grab_player.predict_y)
                sum_url_dis += (ex - self.grab_player.predict_x) ** 2 + \
                    (ey - self.grab_player.predict_y) ** 2

        result = {
            'max_safe_num': max_safe_num,
            'sum_dis': sum_dis,
            'sum_url_dis': sum_url_dis,
            'action': action
        }
        return result

    # 判断是不是需要枚举
    def match_need_enum(self, player):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False and oth_player.lost_vision_num > self.LIMIT_LOST_VISION:
                continue
            if oth_player.predict_x == None:
                continue
            dis = mLegStart.get_short_length(
                player.x, player.y, oth_player.predict_x, oth_player.predict_y)
            if dis <= self.LIMIT_ENUM:
                return True
        return False

    # 暴力围剿敌人
    def force_grab(self, param):
        # 第一步先获取all_enums以及相关数据
        next_one_points_ary = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            if False == self.match_need_enum(player):
                continue
            next_one_points = self.get_next_one_points(player.x, player.y)
            next_one_points.append(("", player.x, player.y))
            next_one_points = [(player.id, it[0], it[1], it[2])
                               for it in next_one_points]
            next_one_points_ary.append(next_one_points)
        all_enums = self.get_all_enums(next_one_points_ary)

        # 敌人无路可走，直接吃
        if len(param['grab_next_points']) == 0:
            self.just_eat_player()

        result = None
        for enum in all_enums:
            ret = self.get_each_enum_result(
                enum, param['grab_next_points'], param['limit_safe_num'])
            if ret == None:
                ret = self.get_each_enum_result(
                    enum, param['safe_points'], param['limit_safe_num'])
            if ret == None:
                continue
            # 安全位置小
            if result == None:
                result = ret
                continue

            if ret['max_safe_num'] < result['max_safe_num']:
                result = ret
            elif ret['max_safe_num'] == result['max_safe_num']:
                # 安全位置一样但是sumdis小或者sumdis一样但是欧式距离小
                if ret['sum_dis'] < result['sum_dis'] or (ret['sum_dis'] == result['sum_dis'] and ret['sum_dis'] < result['sum_url_dis']):
                    result = ret

        if result == None:
            self.all_travel()
        else:
            for pid, em, ex, ey in result['action']:
                mPlayers[pid].move = em
                mLogger.info("[围剿] [player: {}; point: ({}, {}); move: {}]".format(
                    mPlayers[pid].id, mPlayers[pid].x, mPlayers[pid].y, mPlayers[pid].move
                ))
                self.USED_PLAYER_ID.add(pid)

    # 没啥事的鱼斗鱼吃金币或者游走
    def all_travel(self):
        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            players.append(player)
        self.eat_power_or_travel(players)

    # 入口
    def do_excute(self):
        self.HAVE_RET_POINT.clear()
        self.USED_PLAYER_ID.clear()
        mLogger.info("开始预判位置......")
        self.update_predict()
        mLogger.info("确认要抓的敌人......")
        flag = self.confirm_grab_player()
        if True == flag:
            mLogger.info("[敌人] [player: {}; point: ({}, {}); predict: ({}, {}); lost: {}]\n".format(
                self.grab_player.id,
                self.grab_player.x,
                self.grab_player.y,
                self.grab_player.predict_x,
                self.grab_player.predict_y,
                self.grab_player.lost_vision_num
            ))
            self.start_grab()
        else:
            mLogger.info("没有能抓的敌人。。。。。。")
            self.all_travel()

    # # 获取下一步移动的位置，仅判断是不是合法
    # def get_next_one_points(self, x, y, vis_point=set()):
    #     moves = ['up', 'down', 'left', 'right']
    #     rd = random.random()
    #     if rd <= 0.3:
    #         random.shuffle(moves)
    #     result = []
    #     for move in moves:
    #         # 获取move之后真正到达的位置
    #         go_x, go_y = self.mRoundObj.real_go_point(x, y, move)
    #         if False == self.mRoundObj.match_border(go_x, go_y):
    #             continue
    #         if True == self.mRoundObj.match_meteor(go_x, go_y):
    #             continue
    #         if go_x == x and go_y == y:
    #             continue
    #         go_cell_id = mLegStart.get_cell_id(go_x, go_y)
    #         # vis_point 控制多条鱼尽量不重叠
    #         if go_cell_id in vis_point or go_cell_id in self.HAVE_RET_POINT:
    #             continue
    #         result.append((move, go_x, go_y))
    #     return result

    # # 逼近策略;吃完能量之后used_player_id这些都吃了能量了；剩下的要么逼近要么巡航
    # def approach_grab_player(self, used_player_id):
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         if player.id in used_player_id:
    #             continue

    #         min_dis, min_move = None, None
    #         for k, grab_player in othPlayers.iteritems():
    #             if grab_player.predict_x == None:
    #                 continue
    #             if grab_player.visiable == False and grab_player.lost_vision_num > self.LIMIT_LOST_VISION:
    #                 continue

    #             dis, move, cell = self.get_min_dis(
    #                 player.x, player.y, grab_player.predict_x, grab_player.predict_y)

    #             if min_dis == None or dis < min_dis:
    #                 min_dis, min_move = dis, move

    #         if min_dis == None or min_dis > self.LIMIT_GRAB_DIS:
    #             self.travel(player)
    #         else:
    #             player.move = move
    #             self.add_have_go(player)
    #             mLogger.info("[逼近] [player: {}; point: ({}, {}); move: {}]".format(
    #                 player.id, player.x, player.y, player.move
    #             ))

    # # 敌人的安全位置为0，增员
    # def increase_player(self, grab_player, used_player_id):
    #     ret_dis, ret_key, ret_move = None, None, None
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         if player.id in used_player_id:
    #             continue

    #         dis, move, cell = self.get_min_dis(
    #             player.x, player.y, grab_player.predict_x, grab_player.predict_y)
    #         if ret_dis == None or dis < ret_dis:
    #             ret_dis, ret_key, ret_move = dis, k, move

    #     if ret_key != None:
    #         mLogger.info("开始增员以及吃能量......")
    #         mPlayers[ret_key].move = ret_move
    #         mLogger.info("[增员] [player: {}; point: ({}, {}); move: {}]".format(
    #             mPlayers[ret_key].id, mPlayers[ret_key].x, mPlayers[ret_key].y, mPlayers[ret_key].move
    #         ))

    #     eat_power_players = []
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         if player.id in used_player_id:
    #             continue
    #         if k == ret_key:
    #             continue
    #         eat_power_players.append(player)
    #     self.many_players_eat_power(eat_power_players)

    # # 实施抓捕(被抓的鱼，被抓的鱼下一个可以行走的位置，被抓的鱼这一回合的安全位置数目)
    # def force_grab(self, grab_player, grab_next_points, limit_safe_num):
    #     '''
    #     1. 所有的鱼的枚举状态
    #     2. 枚举某一个状态的时候
    #         a. 安全位置数目
    #         b. 我的鱼到敌人的鱼的总距离
    #         b. 满足的时候，找出限制走位的鱼，不限制的就不算
    #     '''
    #     if len(grab_next_points) == 0:
    #         return None
    #     result = None
    #     for enum in self.all_enums:
    #         vis_point = set()

    #         flag = True
    #         for pid, em, ex, ey in enum:
    #             cell = mLegStart.get_cell_id(ex, ey)
    #             vis_point.add(cell)
    #             for pid1, em1, ex1, ey1 in enum:
    #                 if pid == pid1:
    #                     continue
    #                 if ex == ex1 and ey == ey1:
    #                     flag = False
    #                     break
    #         if flag == False:
    #             continue

    #         flag = True
    #         danger_points = set()
    #         max_safe_num = None
    #         for move, go_x, go_y in grab_next_points:
    #             new_next = self.get_next_one_points(go_x, go_y, vis_point)
    #             new_next.append(("", go_x, go_y))
    #             safe_num, safe_points, tmp_danger_points = self.get_safe_num(
    #                 new_next, vis_point)
    #             if safe_num > limit_safe_num:
    #                 flag = False
    #                 break
    #             danger_points = danger_points.union(tmp_danger_points)
    #             if max_safe_num == None or safe_num > max_safe_num:
    #                 max_safe_num = safe_num
    #         if flag == False:
    #             continue

    #         sum_dis, action = 0, []
    #         sum_url_dis = 0
    #         for pid, em, ex, ey in enum:
    #             cell = mLegStart.get_cell_id(ex, ey)
    #             action.append((pid, em, ex, ey))
    #             sum_dis += mLegStart.get_short_length(
    #                 ex, ey, grab_player.predict_x, grab_player.predict_y)
    #             sum_url_dis += (ex - grab_player.predict_x) ** 2 + \
    #                 (ey - grab_player.predict_y) ** 2

    #         if result == None:
    #             result = {
    #                 'max_safe_num': max_safe_num,
    #                 'sum_dis': sum_dis,
    #                 'sum_url_dis': sum_url_dis,
    #                 'action': action
    #             }
    #             continue

    #         # 安全位置小
    #         if max_safe_num < result['max_safe_num']:
    #             result = {
    #                 'max_safe_num': max_safe_num,
    #                 'sum_dis': sum_dis,
    #                 'sum_url_dis': sum_url_dis,
    #                 'action': action
    #             }
    #         elif max_safe_num == result['max_safe_num']:
    #             # 安全位置一样但是sumdis小或者sumdis一样但是欧式距离小
    #             if sum_dis < result['sum_dis'] or (sum_dis == result['sum_dis'] and sum_url_dis < result['sum_url_dis']):
    #                 result = {
    #                     'max_safe_num': max_safe_num,
    #                     'sum_dis': sum_dis,
    #                     'sum_url_dis': sum_url_dis,
    #                     'action': action
    #                 }

    #     return result

    # # 选择一个最优的决策
    # def select_best_result(self, results):
    #     def cmp(it1, it2):
    #         if it1['limit_safe_num'] == it2['limit_safe_num']:
    #             if it1['init_go_num'] == it2['init_go_num']:
    #                 if it1['sum_dis'] == it2['sum_dis']:
    #                     if it1['sum_url_dis'] < it2['sum_url_dis']:
    #                         return -1
    #                     return 1
    #                 if it1['sum_dis'] < it2['sum_dis']:
    #                     return -1
    #                 return 1
    #             if it1['init_go_num'] < it2['init_go_num']:
    #                 return -1
    #             return 1
    #         if it1['limit_safe_num'] < it2['limit_safe_num']:
    #             return -1
    #         return 1
    #     results = sorted(results, cmp)

    #     best_result = results[0]
    #     mLogger.info("[最优] [{}]\n".format(best_result))

    #     if best_result['limit_safe_num'] == 0:
    #         used_player_id = set()
    #         ans_move = dict()
    #         for it in best_result['action']:
    #             used_player_id.add(it[0])
    #             ans_move[it[0]] = it[1]
    #         grab_player = othPlayers[best_result['grab_player_key']]
    #         self.increase_player(grab_player, used_player_id)
    #         for k, v, in ans_move.iteritems():
    #             mPlayers[k].move = v

    #         return None
    #     return best_result

    # # 判断是不是需要枚举
    # def match_need_enum(self, player):
    #     for k, oth_player in othPlayers.iteritems():
    #         if oth_player.visiable == False and oth_player.lost_vision_num > self.LIMIT_LOST_VISION:
    #             continue
    #         if oth_player.predict_x == None:
    #             continue
    #         dis = mLegStart.get_short_length(
    #             player.x, player.y, oth_player.predict_x, oth_player.predict_y)
    #         if dis <= self.LIMIT_ENUM:
    #             return True
    #     return False

    # # 围捕策略
    # def force_grab_player(self):
    #     '''
    #     1. 敌人四条鱼，找能抓的鱼，暴力枚举
    #     2. 每一条被抓的鱼，暴力枚举会返回一个结果
    #         a. 抓捕的鱼的动作
    #         b. 抓捕之后敌人的安全位置
    #         c. 或者None
    #     3. 在所有的抓捕动作中，选择一个收益最大的
    #     '''

    #     # 获取我方所有的枚举情况，距离超过5就不枚举了；包括原地不动的情况
    #     vis_point = set()
    #     next_one_points_ary = []
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         if False == self.match_need_enum(player):
    #             continue
    #         cell = mLegStart.get_cell_id(player.x, player.y)
    #         vis_point.add(cell)
    #         next_one_points = self.get_next_one_points(player.x, player.y)
    #         next_one_points.append(("", player.x, player.y))
    #         next_one_points = [(player.id, it[0], it[1], it[2])
    #                            for it in next_one_points]
    #         next_one_points_ary.append(next_one_points)

    #     self.all_enums = self.get_all_enums(next_one_points_ary)

    #     # 开始看敌方哪个鱼更可能被抓
    #     success, results = False, []
    #     for k, oth_player in othPlayers.iteritems():
    #         if oth_player.predict_x == None:
    #             mLogger.info(
    #                 "[敌人] [player: {} 预判不到位置; 不符合]".format(oth_player.id))
    #             continue

    #         # 获取地方这一轮可走位置，包括原地不动
    #         grab_next_points = self.get_next_one_points(
    #             oth_player.predict_x, oth_player.predict_y, vis_point)
    #         grab_next_points.append(
    #             ("", oth_player.predict_x, oth_player.predict_y))

    #         mLogger.info("[敌人] [player: {}; point: ({}, {}); grab_next: {}]".format(
    #             oth_player.id, oth_player.predict_x, oth_player.predict_y, grab_next_points
    #         ))

    #         # 敌人无路可走就派最近的鱼直接吃它
    #         if len(grab_next_points) == 0:
    #             mLogger.info("[结果] [可行位置为0，找个最近的直接干掉]")
    #             self.just_eat_player(oth_player)
    #             return True

    #         # 判断这个鱼能不能被抓，安全位置太多就抓不了
    #         param = dict()
    #         flag = self.match_grab(
    #             oth_player, grab_next_points, vis_point, param)
    #         mLogger.info("[初始] [{}]".format(param))

    #         if False == flag:
    #             mLogger.info("[结果] [不符合]\n".format(oth_player.id))
    #             continue

    #         # 先根据可走位置，看看能不能限制可走位置
    #         limit_safe_num = param['limit_safe_num']
    #         ret = self.force_grab(
    #             oth_player, grab_next_points, limit_safe_num)

    #         # 可走位置限制不了，就限制安全位置
    #         if ret == None:
    #             ret = self.force_grab(
    #                 oth_player, param['safe_points'], limit_safe_num)

    #         # 当返回结果为none的时候，先看一下这一回合安全位置是不是0，是的话就原地不动
    #         if ret == None:
    #             if limit_safe_num == 0:
    #                 success = True
    #                 sum_dis, sum_url_dis, action = 0, 0, []
    #                 vis_action = set()
    #                 for k, player in mPlayers.iteritems():
    #                     if player.sleep == True:
    #                         continue
    #                     cell = mLegStart.get_cell_id(player.x, player.y)
    #                     if cell in param['danger_points'] and cell not in vis_action:
    #                         vis_action.add(cell)
    #                         action.append((player.id, "", player.x, player.y))
    #                         sum_dis += mLegStart.get_short_length(
    #                             player.x, player.y, oth_player.predict_x, oth_player.predict_y)
    #                         sum_url_dis += (player.x - oth_player.predict_x) ** 2 + \
    #                             (player.y - oth_player.predict_y) ** 2
    #                 ret = {
    #                     'init_go_num': len(grab_next_points),
    #                     'limit_safe_num': limit_safe_num,
    #                     'grab_player_key': oth_player.id,
    #                     'max_safe_num': 0,
    #                     'sum_dis': sum_dis,
    #                     'sum_url_dis': sum_url_dis,
    #                     'action': action
    #                 }
    #                 results.append(ret)
    #         else:
    #             success = True
    #             ret['init_go_num'] = len(grab_next_points)
    #             ret['limit_safe_num'] = limit_safe_num
    #             ret['grab_player_key'] = k
    #             results.append(ret)

    #         mLogger.info("[结果] [{}]\n".format(ret))

    #     if False == success:
    #         return False

    #     # 选择一个最有可能抓住的敌人
    #     best_result = self.select_best_result(results)

    #     # None说明，敌人安全位置为0，我派人增员了，move已经确定，这个时候不用确定了
    #     if best_result == None:
    #         return True

    #     # 确定限制安全位置的鱼的move，其他的鱼要么吃金币，要么巡航
    #     ans_move = dict()
    #     for pid, em, ex, ey in best_result["action"]:
    #         ans_move[pid] = em

    #     eat_power_players = []
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         if player.id in ans_move:
    #             player.move = ans_move[player.id]
    #         else:
    #             eat_power_players.append(player)
    #     self.eat_power_or_travel(eat_power_players)
    #     return True

    # # 所有人去吃能量
    # def all_eat_powers(self):
    #     players = []
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         players.append(player)
    #     return self.many_players_eat_power(players)

    # # 执行入口
    # def do_excute(self):
    #     self.HAVE_RET_POINT.clear()
    #     mLogger.info("开始预判位置......")
    #     self.update_predict()
    #     mLogger.info("开始进行围剿......")
    #     if True == self.force_grab_player():
    #         return
    #     mLogger.info("................微操失败.............\n")
    #     self.do_grab_excute()
    #     # used_player_id = self.all_eat_powers()
    #     # mLogger.info("吃完能量了，逼近还是巡逻")
    #     # self.approach_grab_player(used_player_id)


mDoThink = DoThink()
