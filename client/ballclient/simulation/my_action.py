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
        self.dinger_dirs = [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]
        self.weight_moves = dict()

    # 打印详细log
    def record_detial(self, player):
        if False == config.record_detial or None == player.move:
            return

        mLogger.info(self.weight_moves)
        mLogger.info('[fish: {}, from: ({}, {}), move: {}]'.format(
            player.id, player.x, player.y, player.move))

    # 获取下一步移动的位置，仅判断是不是合法
    def get_next_one_points(self, x, y, vis_point=set()):
        moves = ['up', 'down', 'left', 'right']
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
