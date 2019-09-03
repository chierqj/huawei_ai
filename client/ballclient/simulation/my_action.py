# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math


class Action(object):
    def __init__(self):
        self.mRoundObj = ""
        self.weight_moves = dict()
        self.HAVE_RET_POINT = set()
        self.RANDOM_TRAVEL = 0.1  # 随机数超过这个才开始吃金币，增加随机率
        self.LIMIT_LOST_VISION = 2  # 小于等于这个数字，才算能抓

    # 打印详细log
    def record_detial(self, player):
        if False == config.record_detial:
            return

        mLogger.info(self.weight_moves)
        mLogger.info('[player: {}, point: ({}, {}), move: {}]'.format(
            player.id, player.x, player.y, player.move))

    # 获取一个鱼四个方向离目标点最近的dis, move, cell
    def get_min_dis(self, x, y, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(x, y, vis_point)
        next_one_points.append(("", x, y))
        min_dis, min_move, min_cell, min_url_dis = None, None, None, None
        for move, go_x, go_y in next_one_points:
            dis = mLegStart.get_short_length(go_x, go_y, tx, ty) + 1
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
    
    # 获取一个鱼四个方向离目标点最远的dis, move, cell
    def get_max_dis(self, x, y, tx, ty, vis_point=set()):
        next_one_points = self.get_next_one_points(x, y, vis_point)
        min_dis, min_move, min_cell, min_url_dis = None, None, None, None
        for move, go_x, go_y in next_one_points:
            dis = mLegStart.get_short_length(go_x, go_y, tx, ty) + 1
            url_dis = (go_x - tx) ** 2 + (go_y - ty) ** 2
            if min_dis == None or dis > min_dis or (dis == min_dis and url_dis > min_url_dis):
                min_dis, min_move, min_url_dis = dis, move, url_dis
                cell_id = mLegStart.get_cell_id(go_x, go_y)
                min_cell = cell_id

        if min_dis == None:
            mLogger.warning("[player: {}; point: ({}, {})] 无路可走".format(
                player.id, player.x, player.y))
            return -1, "", -1

        return min_dis, min_move, min_cell

    # 判断是否在(x, y)是否在(px, py)视野当中
    def judge_in_vision(self, px, py, x, y):
        vision = mLegStart.msg['msg_data']['map']['vision']
        if x < px - vision or x > px + vision:
            return False
        if y < py - vision or y > py + vision:
            return False
        return True

    # 获取下一步移动的位置，仅判断是不是合法
    def get_next_one_points(self, x, y, vis_point=set()):
        moves = ['up', 'down', 'left', 'right']
        rd = random.random()
        if rd <= 0.9:
            random.shuffle(moves)
        result = []
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(x, y, move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if go_x == x and go_y == y:
                continue
            go_cell_id = mLegStart.get_cell_id(go_x, go_y)
            # vis_point 控制多条鱼尽量不重叠
            if go_cell_id in vis_point:
                continue
            result.append((move, go_x, go_y))
        return result

    # 获取x, y的可行位置的数目
    def get_next_one_num(self, x, y, vis_point=set()):
        moves = ['up', 'down', 'left', 'right']
        result = 0
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(x, y, move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if go_x == x and go_y == y:
                continue
            go_cell_id = mLegStart.get_cell_id(go_x, go_y)
            # vis_point 控制多条鱼尽量不重叠
            if go_cell_id in vis_point:
                continue
            result += 1
        return result

    # 扩展两层会有哪些点
    def get_extend_points(self, x, y):
        import Queue

        q = Queue.Queue()
        vis = set()

        start = mLegStart.get_cell_id(x, y)

        q.put((start, 0))
        vis.add(start)

        result = [(0, x, y)]
        while False == q.empty():
            uid, step = q.get()

            if step >= 2:
                continue

            ux, uy = mLegStart.get_x_y(uid)
            next_one_points = self.get_next_one_points(ux, uy)

            for mv, nx, ny in next_one_points:
                cell_id = mLegStart.get_cell_id(nx, ny)
                if cell_id in vis:
                    continue
                result.append((step, nx, ny))
                vis.add(cell_id)
                q.put((cell_id, step + 1))

        return result

    # 获取players的所有可能的情况
    def get_all_enums(self, next_one_points):
        result = []
        up = len(next_one_points)

        def dfs(dep, enum=[]):
            if dep == up:
                import copy
                result.append(copy.deepcopy(enum))
                return
            for pid, mv, nx, ny in next_one_points[dep]:
                dfs(dep + 1, enum + [(pid, mv, nx, ny)])
        dfs(0)

        return result

    # 当鱼视野丢失的时候，预判他行走的位置
    def predict_player_point(self, pre_player):
        vision = mLegStart.msg['msg_data']['map']['vision']

        px, py = pre_player.x, pre_player.y
        if pre_player.predict_x != None:
            px, py = pre_player.predict_x, pre_player.predict_y

        next_one_points = self.get_next_one_points(px, py)

        for move, go_x, go_y in next_one_points:
            have_view = False
            for k, player in mPlayers.iteritems():
                if go_x < px - vision or go_x > px + vision:
                    continue
                if go_y < py - vision or go_y > py + vision:
                    continue
                have_view = True
                break
            if have_view == False:
                pre_player.predict_x, pre_player.predict_y = go_x, go_y

        # if pre_player.predict_x == None:
        #     mLogger.warning("> 预判没有位置 < [player: {}; point: ({}, {})]".format(
        #         pre_player.id, pre_player.x, pre_player.y,
        #     ))
        # else:
        #     mLogger.info(">预判< [player: {}; point: ({}, {}); predict: ({}, {})]".format(
        #         pre_player.id, pre_player.x, pre_player.y, pre_player.predict_x, pre_player.predict_y
        #     ))

    # 添加访问过得点
    def add_have_go(self, player):
        GX, GY = self.mRoundObj.real_go_point(player.x, player.y, player.move)
        GP = mLegStart.get_cell_id(GX, GY)
        self.HAVE_RET_POINT.add(GP)

    # 探路巡航
    def travel(self, player):
        min_vis_count, ret_x, ret_y = None, None, None

        rd = random.random()
        if rd > self.RANDOM_TRAVEL:
            for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
                cell = mLegStart.get_cell_id(power.x, power.y)
                num = self.mRoundObj.VIS_POWER_COUNT.get(cell, 0)
                if min_vis_count == None or num < min_vis_count:
                    min_vis_count, ret_x, ret_y = num, power.x, power.y

        if min_vis_count == None:
            # 在视野中离得最近的x,y
            ret_dis, ret_x, ret_y = None, None, None
            for k, p in mPlayers.iteritems():
                if p.sleep == True:
                    continue
                if p.id == player.id:
                    continue
                if self.judge_in_vision(player.x, player.y, p.x, p.y):
                    dis, move, cell = self.get_min_dis(player.x, player.y, p.x, p.y)
                    if ret_dis == None or dis < ret_dis:
                        ret_dis, ret_x, ret_y = dis, p.x, p.y
            if ret_dis == None:
                next_one_points = self.get_next_one_points(player.x, player.y)
                min_cnt, ret_move = None, None
                for mv, nx, ny in next_one_points:
                    cell = mLegStart.get_cell_id(nx, ny)
                    cnt = self.mRoundObj.VIS_POWER_COUNT.get(cell, 0)
                    if min_cnt == None or cnt < min_cnt:
                        min_cnt, ret_move = cnt, mv
                player.move = ret_move
            else:
                dis, move, cell = self.get_max_dis(player.x, player.y, ret_x, ret_y)
                player.move = move

            mLogger.info("[巡航] [player: {}; point: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.move
            ))
        else:
            dis, move, cell = self.get_min_dis(
                player.x, player.y, ret_x, ret_y, self.HAVE_RET_POINT)
            player.move = move

            mLogger.info("[巡航] [player: {}; point: ({}, {}); move: {}; power: ({}, {})]".format(
                player.id, player.x, player.y, player.move, ret_x, ret_y
            ))
        # self.add_have_go(player)

    # 更新每个鱼是不是需要预测位置
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

    # 吃能量或者巡航
    def eat_power_or_travel(self, players):
        used_player_id = self.many_players_eat_power(players)
        for player in players:
            if player.sleep == True:
                continue
            if player.id in used_player_id:
                continue
            self.travel(player)

    # 多个人吃能量
    def many_players_eat_power(self, players):
        powers = self.mRoundObj.msg['msg_data'].get('power', [])
        vis_player_id = set()

        for player in players:
            vis_power_index = set()
            min_dis, min_move, min_index = None, None, None
            for index, power in enumerate(powers):
                if index in vis_power_index:
                    continue

                near = None
                for i in vis_power_index:
                    d = mLegStart.get_short_length(
                        powers[i]['x'], players[i]['y'])
                    if near == None or d < near:
                        near = d

                dis, move, cell = self.get_min_dis(
                    player.x, player.y, power['x'], power['y'], self.HAVE_RET_POINT)

                if near != None and dis > d:
                    continue

                if min_dis == None or dis < min_dis:
                    min_dis, min_move, min_index = dis, move, index

            if min_index != None:
                vis_power_index.add(index)
                player.move = min_move
                # self.add_have_go(player)
                vis_player_id.add(player.id)
                mLogger.info("[能量] [player: {}; point: ({}, {}); move: {}]".format(
                    player.id, player.x, player.y, player.move
                ))
        return vis_player_id

    # 入口
    def excute(self, mRoundObj):
        self.mRoundObj = mRoundObj
        self.do_excute()
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
