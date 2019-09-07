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
        self.USED_VISION_POINT = set()

    # 根据move改变坐标
    def go_next(self, x, y, move):
        if move == "":
            return x, y
        if move == 'up':
            return x, y - 1
        if move == 'down':
            return x, y + 1
        if move == 'left':
            return x - 1, y
        if move == 'right':
            return x + 1, y

    # 打印详细log
    def record_detial(self, player, text):
        mLogger.info('[{}] [player: {}, point: ({}, {}), move: {}]'.format(
            text, player.id, player.x, player.y, player.move))

    # 判断是否在(x, y)是否在(px, py)视野当中
    def judge_in_vision(self, px, py, x, y):
        vision = mLegStart.msg['msg_data']['map']['vision']
        if x < px - vision or x > px + vision:
            return False
        if y < py - vision or y > py + vision:
            return False
        return True

    # 获取players的所有可能的情况
    def get_all_enums(self, players):
        result = []
        up = len(players)

        def dfs(dep, enum=[]):
            if dep == up:
                import copy
                result.append(copy.deepcopy(enum))
                return

            pid = players[dep].id
            uid = mLegStart.get_cell_id(players[dep].x, players[dep].y)
            sons = mLegStart.SONS.get(uid, None)

            if True == self.error_no_sons(sons, uid):
                return

            for mv, nx, ny in sons:
                dfs(dep + 1, enum + [(pid, mv, nx, ny)])
        dfs(0)

        return result

    # 当鱼视野丢失的时候，预判他行走的位置
    def predict_player_point(self, pre_player):
        px, py = pre_player.x, pre_player.y
        if pre_player.predict_x != None:
            px, py = pre_player.predict_x, pre_player.predict_y

        uid = mLegStart.get_cell_id(px, py)
        sons = mLegStart.SONS.get(uid, [])

        for move, go_x, go_y in sons:
            have_view = False
            for k, player in mPlayers.iteritems():
                if player.sleep == True:
                    continue
                if True == self.judge_in_vision(px, py, go_x, go_y):
                    have_view = True
                    break
            if have_view == False:
                pre_player.predict_x, pre_player.predict_y = go_x, go_y

    # 更新每个鱼是不是需要预测位置
    def update_predict(self):
        mLogger.info("开始预判位置......")
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                self.predict_player_point(oth_player)
            else:
                oth_player.predict_x, oth_player.predict_y = oth_player.x, oth_player.y,
            mLogger.info("[player: {}; point: ({}, {}); predict: ({}, {}); lost_vision_num: {}]".format(
                oth_player.id, oth_player.x, oth_player.y, oth_player.predict_x, oth_player.predict_y, oth_player.lost_vision_num
            ))

    # 四个方位最近的
    def get_min_dis(self, ux, uy, vx, vy, vis_point=set()):
        uid = mLegStart.get_cell_id(ux, uy)

        if ux == vx and uy == vy:
            return 0, "", uid

        import copy
        sons = copy.deepcopy(mLegStart.SONS.get(uid, []))
        sons.append(("", ux, uy))

        ret_dis, ret_move, ret_cell = None, None, None
        for move, go_x, go_y in sons:
            vid = mLegStart.get_cell_id(go_x, go_y)
            if vid in vis_point:
                continue
            dis = mLegStart.get_short_length(go_x, go_y, vx, vy) + 1
            if ret_dis == None or dis < ret_dis:
                ret_dis, ret_move, ret_cell = dis, move, vid

        if ret_move == None:
            mLogger.warning("[player: {}; point: ({}, {})] 无路可走".format(
                player.id, player.x, player.y))
            return -1, "", -1
        return ret_dis, ret_move, ret_cell

    # 吃能量
    def eat_power(self, player):
        powers = self.mRoundObj.msg['msg_data'].get('power', None)
        if None == powers:
            return False

        ret_dis, ret_move = None, None
        for power in powers:
            if True == self.judge_in_vision(player.x, player.y, power['x'], power['y']):
                dis, move, cell = self.get_min_dis(
                    player.x, player.y, power['x'], power['y'])
                if ret_dis == None or dis < ret_dis:
                    ret_dis, ret_move = dis, move
        if ret_move == None:
            return False
        player.move = ret_move
        self.record_detial(player, "能量")
        return True

    # 巡航
    def travel(self, player):
        if True == self.eat_power(player):
            return

        def find_travel_point():
            vision_points = [(3, 4), (16, 4), (3, 14), (16, 14)]
            for vx, vy in vision_points:
                vid = mLegStart.get_cell_id(vx, vy)
                if vid in self.USED_VISION_POINT:
                    continue
                if False == self.judge_in_vision(player.x, player.y, vx, vy):
                    dis, move, cell = self.get_min_dis(
                        player.x, player.y, vx, vy)
                    player.move = move
                    player.travel_point = vid
                    self.USED_VISION_POINT.add(vid)
                    return
            for vx, vy in vision_points:
                vid = mLegStart.get_cell_id(vx, vy)
                if False == self.judge_in_vision(player.x, player.y, vx, vy):
                    dis, move, cell = self.get_min_dis(
                        player.x, player.y, vx, vy)
                    player.move = move
                    player.travel_point = vid
                    self.USED_VISION_POINT.add(vid)

        if player.travel_point == None:
            find_travel_point()
        else:
            tx, ty = mLegStart.get_x_y(player.travel_point)
            if player.x != tx or player.y != ty:
                dis, move, cell = self.get_min_dis(player.x, player.y, tx, ty)
                player.move = move
                self.USED_VISION_POINT.add(player.travel_point)
            else:
                find_travel_point()

    # 清空掉追击固定视野
    def init_vision_point(self):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            player.travel_point = None
        self.USED_VISION_POINT.clear()

    def error_no_sons(self, sons, uid):
        ux, uy = mLegStart.get_x_y(uid)
        if sons == None:
            mLogger.warning(
                "[没有儿子] [uid: {}; point: ({}, {})]".format(uid, ux, uy))
            return True
        return False

    def get_vision_set(self, px, py):
        width, height = mLegStart.width, mLegStart.height
        vision = mLegStart.msg['msg_data']['map']['vision']
        x1, y1 = max(0, px - vision), max(0, py - vision)
        x2 = min(width - 1, px + vision)
        y2 = min(height - 1, py + vision)
        vision_count = set()
        for i in range(x1, x2 + 1):
            for j in range(y1, y2 + 1):
                if False == mLegStart.match_border(i, j):
                    continue
                cell = mLegStart.get_cell_id(i, j)
                vision_count.add(cell)
        return vision_count

    def get_players_vision_set(self, players):
        vision_set = set()
        for player in players:
            tmp = self.get_vision_set(player.x, player.y)
            vision_set = vision_set.union(tmp)
        return vision_set

    # 入口
    def excute(self, mRoundObj):
        self.mRoundObj = mRoundObj
        self.update_predict()
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
