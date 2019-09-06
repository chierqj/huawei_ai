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
            if self.judge_in_vision(enemy.x, enemy.y, player.x, player.y):
                return True
            dis = mLegStart.get_short_length(
                enemy.x, enemy.y, player.x, player.y)
            # if dis <= 5:
            #     return True
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
    1. 判断去(x, y)这个点会不会突然暴露视野
        a. 我看不到
        b. 敌人能看到
        c. 虫洞判断
    2. 判断去(x, y, ustep)这个点敌人会不会比我快
        a. 敌人原汁原味比你快
        b. 钻虫洞判断两个位置
    '''

    def judge_suddenly_dead(self, x, y):
        if False == self.match_self_can_say(x, y):
            return True
        if True == self.match_father_self_can_not_say(x, y):
            return True
        if True == self.match_wormhole_enemy_can_say(x, y):
            return True
        return False

    def judge_enemy_fast(self, x, y, step):
        if True == self.match_enemy_fast(x, y, step):
            return True
        if True == self.match_wormhole_enemy_fast(x, y, step - 1):
            return True
        return False

    '''
    逃跑
    '''

    def escape(self, player):
        move_distance = dict()
        move_distance[""] = dict()
        move_distance["left"] = dict()
        move_distance["right"] = dict()
        move_distance["up"] = dict()
        move_distance["down"] = dict()

        can_say_enemy_num = 0
        for k, enemy in othPlayers.iteritems():
            if enemy.visiable == False:
                continue
            can_say_enemy_num += 1

        flag = False
        def bfs1():
            q = Queue.Queue()
            vis = set()
            start = mLegStart.get_cell_id(player.x, player.y)
            q.put(("", start, 0))
            vis.add(start)
            while False == q.empty():
                move, uid, ustep = q.get()
                errx, erry = mLegStart.get_x_y(uid)
                if ustep >= 7:
                    break
                if ustep >= 1:
                    flag = True
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
                    if True == self.judge_enemy_fast(nx, ny, ustep + 1):
                        continue
                    if ustep == 0:
                        if can_say_enemy_num < 4:
                            if False == self.match_self_can_say(nx, ny):
                                continue
                            if True == self.match_father_self_can_not_say(nx, ny):
                                continue
                            if True == self.match_wormhole_enemy_fast(nx, ny, ustep + 1):
                                continue
                        move = mv
                    vis.add(cell)
                    q.put((move, cell, ustep + 1))

        def bfs2():
            q = Queue.Queue()
            vis = set()
            start = mLegStart.get_cell_id(player.x, player.y)
            q.put(("", start, 0))
            vis.add(start)
            while False == q.empty():
                move, uid, ustep = q.get()
                errx, erry = mLegStart.get_x_y(uid)
                if ustep >= 7:
                    break
                if ustep >= 1:
                    flag = True
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
                    if True == self.judge_enemy_fast(nx, ny, ustep + 1):
                        continue
                    if ustep == 0:
                        move = mv
                    vis.add(cell)
                    q.put((move, cell, ustep + 1))
        if flag == False:
            move_distance = dict()
            move_distance[""] = dict()
            move_distance["left"] = dict()
            move_distance["right"] = dict()
            move_distance["up"] = dict()
            move_distance["down"] = dict()
            bfs2()

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

        self.record_detial(player, "逃跑")
        d = ["", "up", "down", "left", "right"]
        info = "各个方向位置信息\n"
        for it in d:
            info += "---------------- {} --------------\n".format(it)
            for k, v in move_distance[it].iteritems():
                info += "[dis: {}] [num: {}] [point: {}]\n".format(
                    k, len(v), v)
        mLogger.info(info)

    '''
    不用逃跑
    1. 吃能量，并且能量在我的视野范围内
    2. 越远越好
    '''

    def find_power(self, player, used_power):
        powers = self.mRoundObj.msg['msg_data'].get('power', None)
        if None == powers:
            return False
        power_area = set()
        for power in powers:
            cell = mLegStart.get_cell_id(power['x'], power['y'])
            if cell in used_power:
                continue
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
                player.move = move
                used_power.add(uid)
                return True
            sons = mLegStart.SONS.get(uid, None)
            if True == self.error_no_sons(sons, uid):
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
                if ustep == 0:
                    if True == self.judge_suddenly_dead(nx, ny):
                        continue
                    if True == self.match_enemy_can_say(nx, ny):
                        continue
                    move = mv
                vis.add(cell)
                q.put((move, cell, ustep + 1))
        return False

    def expand_vision(self):
        have_vision_count = set()

        def cal(player):
            uid = mLegStart.get_cell_id(player.x, player.y)
            sons = mLegStart.SONS.get(uid, None)
            if True == self.error_no_sons(sons, uid):
                return
            for mv, nx, ny in sons:
                if mv == player.move:
                    vid = mLegStart.get_cell_id(nx, ny)
                    have_vision_count.add(vid)
                    return

        players = []
        used_power = set()
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if True == self.match_need_escape(player):
                cal(player)
                continue
            if True == self.find_power(player, used_power):
                cal(player)
                continue
            players.append(player)

        all_enums = self.get_all_enums(players)
        max_count, ret_enum = None, None
        for enum in all_enums:
            import copy
            vision_count = copy.deepcopy(have_vision_count)
            flag = True
            for pid, em, ex, ey in enum:
                if True == self.judge_suddenly_dead(ex, ey):
                    flag = False
                    break
                if True == self.match_enemy_can_say(ex, ey):
                    flag = False
                    break
                width, height = mLegStart.width, mLegStart.height
                vision = mLegStart.msg['msg_data']['map']['vision']
                x1, y1 = max(0, ex - vision), max(0, ey - vision)
                x2 = min(width - 1, ex + vision)
                y2 = min(height - 1, ey + vision)

                for i in range(x1, x2 + 1):
                    for j in range(y1, y2 + 1):
                        cell = mLegStart.get_cell_id(i, j)
                        vision_count.add(cell)
            if flag == False:
                # mLogger.warning("[有人可能会暴露视野]")
                continue
            if max_count == None or len(vision_count) >= max_count:
                max_count, ret_enum = len(vision_count), enum

        if ret_enum == None:
            max_count, ret_enum = None, None
            for enum in all_enums:
                import copy
                vision_count = copy.deepcopy(have_vision_count)
                for pid, em, ex, ey in enum:
                    width, height = mLegStart.width, mLegStart.height
                    vision = mLegStart.msg['msg_data']['map']['vision']
                    x1, y1 = max(0, ex - vision), max(0, ey - vision)
                    x2 = min(width - 1, ex + vision)
                    y2 = min(height - 1, ey + vision)

                    for i in range(x1, x2 + 1):
                        for j in range(y1, y2 + 1):
                            cell = mLegStart.get_cell_id(i, j)
                            vision_count.add(cell)
                if max_count == None or len(vision_count) >= max_count:
                    max_count, ret_enum = len(vision_count), enum

        mLogger.info("[max_count: {}; ret_enum: {}]".format(
            max_count, ret_enum))
        for pid, em, ex, ey in ret_enum:
            mPlayers[pid].move = em

    def do_excute(self):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if True == self.match_need_escape(player):
                self.escape(player)
        self.expand_vision()


mDoBeat = DoBeat()
