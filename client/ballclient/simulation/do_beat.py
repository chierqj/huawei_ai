# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math
from ballclient.simulation.my_action import Action


class DoBeat(Action):
    def __init__(self):
        super(DoBeat, self).__init__()

    def init(self):
        self.HAVE_RET_POINT.clear()

    # 敌人能不能看到
    def match_enemy_can_say(self, x, y):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            if True == self.judge_in_vision(oth_player.x, oth_player.y, x, y):
                mLogger.info("[point: ({}, {})] [敌人: {}; point: ({}, {})]".format(
                    x, y, oth_player.id, oth_player.x, oth_player.y
                ))
                return True
        return False

    # 自己能不能看到
    def match_self_can_say(self, x, y):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if True == self.judge_in_vision(player.x, player.y, x, y):
                return True
        return False

    # 这个点的father是不是有自己看不到的;True表示有看不到的father
    def match_father_self_cannot_say(self, x, y):
        cell = mLegStart.get_cell_id(x, y)
        fathers = mLegStart.FATHER.get(cell, set())
        for it in fathers:
            nx, ny = mLegStart.get_x_y(it)
            if False == self.match_self_can_say(nx, ny):
                return True
        return False

    # 正常情况下敌人到达x, y会不会比你快
    def judge_enemy_fast(self, x, y, step):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.visiable == False:
                continue
            dis = mLegStart.get_short_length(oth_player.x, oth_player.y, x, y)
            # mLogger.info("[point: ({}, {}); 距离{}] [敌人: {}; point: ({}, {}); 距离: {}]".format(
            #     x, y, step, oth_player.id, oth_player.x, oth_player.y, dis
            # ))
            if dis <= step:
                return True
        return False

    # 判断有没有可能是虫洞
    def judge_danger_wormhole_fast(self, x, y, step):
        cell = mLegStart.get_graph_cell(x, y)
        if True == mLegStart.match_wormhole(cell):
            go_x, go_y = mLegStart.get_x_y(mLegStart.do_wormhoe(cell))
            return self.judge_enemy_fast(go_x, go_y, step)
        return False

    def judge_danger_wormhole_can_say(self, x, y):
        cell = mLegStart.get_graph_cell(x, y)
        if True == mLegStart.match_wormhole(cell):
            go_x, go_y = mLegStart.get_x_y(mLegStart.do_wormhoe(cell))
            return self.match_enemy_can_say(go_x, go_y)
        return False

    # 逃跑
    def escape(self, player):
        def bfs():
            import Queue
            q = Queue.Queue()
            vis = set()

            cell = mLegStart.get_cell_id(player.x, player.y)
            q.put((0, "", player.x, player.y))
            vis.add(cell)

            while False == q.empty():
                step, move, ux, uy = q.get()

                if step >= 7:
                    break

                player.move = move
                next_one_points = self.get_next_one_points(ux, uy)

                for mv, nx, ny in next_one_points:
                    v_cell = mLegStart.get_cell_id(nx, ny)
                    '''
                    1. 访问过
                    2. 敌人有可能比我走得快
                    3. 可能是虫洞，两个位置
                    '''
                    if v_cell in vis:
                        continue
                    if True == self.judge_enemy_fast(nx, ny, step + 1):
                        continue
                    if True == self.judge_danger_wormhole_fast(nx, ny, step):
                        continue

                    if step == 0:
                        move = mv

                    vis.add(v_cell)
                    q.put((step+1, move, nx, ny))
        bfs()

    # 找能量

    def find_power(self, player):
        powers = self.mRoundObj.msg['msg_data'].get('power', [])

        if len(powers) == 0:
            return None

        have_power = set()
        for it in powers:
            cell = mLegStart.get_cell_id(it['x'], it['y'])
            have_power.add(cell)

        import Queue
        q = Queue.Queue()
        vis = set()

        cell = mLegStart.get_cell_id(player.x, player.y)
        q.put((0, "", player.x, player.y))
        vis.add(cell)

        while False == q.empty():
            step, move, ux, uy = q.get()
            u_cell = mLegStart.get_cell_id(ux, uy)

            if u_cell in have_power:
                return move

            next_one_points = self.get_next_one_points(ux, uy)
            for mv, nx, ny in next_one_points:
                v_cell = mLegStart.get_cell_id(nx, ny)
                '''
                1. 访问过
                2. 敌人能看到
                3. 我所有的鱼都看不到
                4. 能到这个点的点，有我的所有鱼看不到的
                '''
                if v_cell in vis:
                    continue
                if True == self.match_enemy_can_say(nx, ny):
                    continue
                if False == self.match_self_can_say(nx, ny):
                    continue
                if True == self.match_father_self_cannot_say(nx, ny):
                    continue
                if True == self.judge_danger_wormhole_can_say(nx, ny):
                    continue

                if step == 0:
                    move = mv

                vis.add(v_cell)
                q.put((step+1, move, nx, ny))
        return None

    def find_faraway(self, player):
        import Queue
        q = Queue.Queue()
        vis = set()

        cell = mLegStart.get_cell_id(player.x, player.y)
        q.put((0, "", player.x, player.y))
        vis.add(cell)

        ans_move = None
        while False == q.empty():
            step, move, ux, uy = q.get()

            if step >= 15:
                break

            ans_move = move
            next_one_points = self.get_next_one_points(ux, uy)
            for mv, nx, ny in next_one_points:
                v_cell = mLegStart.get_cell_id(nx, ny)
                if v_cell in vis:
                    continue

                if step == 0:
                    if True == self.match_enemy_can_say(nx, ny):
                        continue
                    if False == self.match_self_can_say(nx, ny):
                        continue
                    if True == self.match_father_self_cannot_say(nx, ny):
                        continue
                    if True == self.judge_danger_wormhole_can_say(nx, ny):
                        continue
                    move = mv
                vis.add(v_cell)
                q.put((step+1, move, nx, ny))
        return ans_move

    def random_walk(self, player):
        move = self.find_power(player)
        if move != None:
            player.move = move
            mLogger.info("[能量] [player: {}; point: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.move
            ))
            return

        move = self.find_faraway(player)
        if move != None:
            player.move = move
            mLogger.info("[最长路] [player: {}; point: ({}, {}); move: {}]".format(
                player.id, player.x, player.y, player.move
            ))
            return
        player.move = ""
        mLogger.info("[原地不动] [player: {}; point: ({}, {}); move: {}]".format(
            player.id, player.x, player.y, player.move
        ))

    def do_excute(self):
        self.update_predict()
        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue

            if True == self.match_enemy_can_say(player.x, player.y):
                self.escape(player)
                mLogger.info("[逃跑] [player: {}; point: ({}, {}); move: {}]".format(
                    player.id, player.x, player.y, player.move
                ))
            else:
                self.random_walk(player)

            # players.append(player)
        # self.eat_power_or_travel(players)


mDoBeat = DoBeat()
