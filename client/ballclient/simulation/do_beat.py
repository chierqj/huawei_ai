# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math
import Queue
from ballclient.simulation.my_action import Action


class DoBeat(Action):
    def __init__(self):
        super(DoBeat, self).__init__()

    def init(self):
        pass

    '''
    match做条件判断相关
    1. 判断player是否需要逃跑
    2. 判断(x, y)是否在敌人的视野中
    3. 判断(x, y)是否在我的视野中
    4. 判断(x, y)的连接父节点有没有我看不到的
    5. 判断(x, y)是不是敌人比我快
    6. 判断(x, y)是不是虫洞，是虫洞看看敌人是不是比我快
    7. 判断(x, y)是不是虫洞，是虫洞看看是不是在敌人的视野中
    '''

    def match_need_escape(self, player):
        for k, enemy in othPlayers.iteritems():
            if enemy.visiable == False:
                continue
            # if self.judge_in_vision(enemy.x, enemy.y, player.x, player.y):
            #     return True
            dis = mLegStart.get_short_length(
                enemy.x, enemy.y, player.x, player.y)
            if dis <= 5:
                return True
        return False

    def match_enemy_can_say(self, x, y):
        for k, enemy in othPlayers.iteritems():
            if enemy.visiable == False:
                continue
            if True == self.judge_in_vision(enemy.x, enemy.y, x, y):
                return True
        return False

    def match_self_can_say(self, x, y):
        for k, mfish in mPlayers.iteritems():
            if mfish.sleep == True:
                continue
            if True == self.judge_in_vision(mfish.x, mfish.y, x, y):
                return True
        return False

    def match_father_self_can_not_say(self, x, y):
        uid = mLegStart.get_cell_id(x, y)
        fathers = mLegStart.FATHER.get(uid, None)
        if None == fathers:
            mLogger.warning("[没有父亲] [uid: {}; point: ({}, {})]".format(
                uid, x, y
            ))
            return False
        for fax, fay in fathers:
            if False == self.match_self_can_say(fax, fay):
                return True
        return False

    def match_enemy_fast(self, x, y, step):
        for k, enemy in othPlayers.iteritems():
            if enemy.visiable == False:
                continue
            dis = mLegStart.get_short_length(enemy.x, enemy.y, x, y)
            if dis <= step:
                return True
        return False

    def match_wormhole_enemy_fast(self, x, y, step):
        if False == mLegStart.match_wormhole(x, y):
            return False
        alp = mLegStart.get_graph_cell(x, y)
        alpid = mLegStart.do_wormhole(alp)
        ux, uy = mLegStart.get_x_y(alpid)
        return self.match_enemy_fast(ux, uy, step)

    def match_wormhole_enemy_can_say(self, x, y):
        if False == mLegStart.match_wormhole(x, y):
            return False
        alp = mLegStart.get_graph_cell(x, y)
        alpid = mLegStart.do_wormhole(alp)
        ux, uy = mLegStart.get_x_y(alpid)
        return self.match_enemy_can_say(ux, uy)

    '''
    逃跑
    '''

    def escape(self, player):
        q = Queue.Queue()
        vis = set()
        start = mLegStart.get_cell_id(player.x, player.y)
        q.put(("", start, 0))
        vis.add(start)

        move_distance = dict()
        move_distance[""] = dict()
        move_distance["left"] = dict()
        move_distance["right"] = dict()
        move_distance["up"] = dict()
        move_distance["down"] = dict()

        while False == q.empty():
            move, uid, ustep = q.get()
            errx, erry = mLegStart.get_x_y(uid)

            if ustep >= 8:
                break

            st = move_distance[move].get(ustep, [])
            st.append((errx, erry))
            move_distance[move][ustep] = st

            sons = mLegStart.SONS.get(uid, None)
            if sons == None:
                mLogger.warning("[没有儿子] [uid: {}; point: ({}, {})]".format(
                    uid, errx, erry
                ))
                continue

            '''
            1. 敌人比我快，我就不走 (走过去的nx, ny可能是虫洞)
            2. 视野看不到我就不走
            3. 要走的点的父亲看不到，我就不走
            '''
            for mv, nx, ny in sons:
                cell = mLegStart.get_cell_id(nx, ny)
                if cell in vis:
                    continue
                if True == self.match_enemy_fast(nx, ny, ustep + 1):
                    continue
                if True == self.match_wormhole_enemy_fast(nx, ny, ustep + 1):
                    continue

                if ustep == 0:
                    move = mv

                vis.add(cell)
                q.put((move, cell, ustep + 1))

        max_step, max_count, ret_move = None, None, ""
        for move, step_dict in move_distance.iteritems():
            for step, point_ary in step_dict.iteritems():
                count = len(point_ary)
                if max_step == None:
                    max_step, max_count, ret_move = step, count, move
                    continue
                if step > max_step or (step == max_step and count > max_count):
                    max_step, max_count, ret_move = step, count, move
        player.move = ret_move


        d = ["", "up", "down", "left", "right"]
        info = "各个方向位置信息\n"
        for it in d:
            info += "---------------- {} --------------\n".format(it)
            for k, v in move_distance[it].iteritems():
                info += "[dis: {}] [num: {}] [point: {}]\n".format(k, len(v), v)
        mLogger.info(info)
        self.record_detial(player, "逃跑")

    '''
    不用逃跑
    1. 吃能量，并且能量在我的视野范围内
    2. 越远越好
    '''

    def find_power(self, player):
        powers = self.mRoundObj.msg['msg_data'].get('power', None)
        if None == powers:
            return None
        power_area = set()
        for power in powers:
            cell = mLegStart.get_cell_id(power['x'], power['y'])
            power_area.add(cell)

        q = Queue.Queue()
        vis = set()
        start = mLegStart.get_cell_id(player.x, player.y)
        q.put(("", start, 0))
        vis.add(start)

        move_distance = dict()
        while False == q.empty():
            move, uid, ustep = q.get()
            errx, erry = mLegStart.get_x_y(uid)
            if uid in power_area:
                return move
            sons = mLegStart.SONS.get(uid, None)
            if sons == None:
                mLogger.warning("[没有儿子] [uid: {}; point: ({}, {})]".format(
                    uid, errx, erry
                ))
                continue
            move_distance[move] = (errx, erry, ustep)
            '''
            1. 敌人能看到，我不走 (注意虫洞)
            2. 我自己都看不到，我不走
            3. 要走的点的父亲看不到，我不走
            '''
            for mv, nx, ny in sons:
                cell = mLegStart.get_cell_id(nx, ny)
                if cell in vis:
                    continue
                if True == self.match_enemy_can_say(nx, ny):
                    continue
                if True == self.match_wormhole_enemy_can_say(nx, ny):
                    continue
                if False == self.match_self_can_say(nx, ny):
                    continue
                if True == self.match_father_self_can_not_say(nx, ny):
                    continue
                if ustep == 0:
                    move = mv
                vis.add(cell)
                q.put((move, cell, ustep + 1))

    def find_faraway(self, player):
        '''
        1. 敌人能看到，我不走 (注意虫洞)
        2. 我自己都看不到，我不走
        3. 要走的点的父亲看不到，我不走
        '''
        q = Queue.Queue()
        vis = set()
        start = mLegStart.get_cell_id(player.x, player.y)
        q.put(("", start, 0))
        vis.add(start)

        ans_move = None
        while False == q.empty():
            move, uid, ustep = q.get()
            ans_move = move
            if ustep >= 10:
                break
            errx, erry = mLegStart.get_x_y(uid)
            sons = mLegStart.SONS.get(uid, None)
            if sons == None:
                mLogger.warning("[没有儿子] [uid: {}; point: ({}, {})]".format(
                    uid, errx, erry
                ))
                continue
            for mv, nx, ny in sons:
                cell = mLegStart.get_cell_id(nx, ny)
                if cell in vis:
                    continue
                if ustep == 0:
                    if True == self.match_enemy_can_say(nx, ny):
                        continue
                    if True == self.match_wormhole_enemy_can_say(nx, ny):
                        continue
                    if False == self.match_self_can_say(nx, ny):
                        continue
                    if True == self.match_father_self_can_not_say(nx, ny):
                        continue
                    if ustep == 0:
                        move = mv
                vis.add(cell)
                q.put((move, cell, ustep + 1))
        return ans_move

    def do_excute(self):
        self.USED_VISION_POINT.clear()
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if True == self.match_need_escape(player):
                self.escape(player)
            else:
                self.travel(player)


mDoBeat = DoBeat()
