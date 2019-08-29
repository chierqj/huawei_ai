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
        self.RANDOM_TRAVEL = 0.3  # 随机数超过这个才开始吃金币，增加随机率


    # 打印详细log
    def record_detial(self, player):
        if False == config.record_detial:
            return

        mLogger.info(self.weight_moves)
        mLogger.info('[fish: {}, from: ({}, {}), move: {}]'.format(
            player.id, player.x, player.y, player.move))

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
        if rd <= 0.3:
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
            next_one_points = self.get_next_one_points(player.x, player.y)
            min_cnt, ret_move = None, None
            for mv, nx, ny in next_one_points:
                cell = mLegStart.get_cell_id(nx, ny)
                cnt = self.mRoundObj.VIS_POWER_COUNT.get(cell, 0)
                if min_cnt == None or cnt < min_cnt:
                    min_cnt, ret_move = cnt, mv
            player.move = ret_move
            mLogger.info("[巡航] [player: {}; point: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.move
            ))
        else:
            dis, move, cell = self.get_min_dis(
                player.x, player.y, ret_x, ret_y)
            player.move = move

            mLogger.info("[巡航] [player: {}; point: ({}, {}); move: {}; power: ({}, {})]".format(
                player.id, player.x, player.y, player.move, ret_x, ret_y
            ))
        self.add_have_go(player)

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
