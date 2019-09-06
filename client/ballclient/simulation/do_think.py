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


# class DoThink(Action):
#     def __init__(self):
#         super(DoThink, self).__init__()
#         self.grab_player = None
#         self.USED_PLAYER_ID = set()     # 堵传送门用到的鱼的id
#         self.LIMIT_LOST_VISION = 1

#     def init(self):
#         self.grab_player = None
#         self.USED_PLAYER_ID.clear()
#         self.USED_VISION_POINT.clear()

#     def confirm_grab_player(self):
#         if self.grab_player != None and self.grab_player.lost_vision_num <= self.LIMIT_LOST_VISION:
#             return

#         def get_dis(x, y):
#             ret_dis = None
#             for k, player in mPlayers.iteritems():
#                 if player.sleep == True:
#                     continue
#                 dis = mLegStart.get_short_length(player.x, player.y, x, y)
#                 if ret_dis == None or dis < ret_dis:
#                     ret_dis = dis
#             return ret_dis

#         # ret_key = None
#         ret_key1, ret_dis1 = None, None
#         ret_key2, ret_dis2 = None, None
#         for k, enemy in othPlayers.iteritems():
#             if enemy.visiable == True:
#                 dis = get_dis(enemy.x, enemy.y)
#                 if ret_dis1 == None or dis < ret_dis1:
#                     ret_dis1, ret_key1 = dis, k
#             if enemy.predict_x == None:
#                 continue
#             if enemy.lost_vision_num <= self.LIMIT_LOST_VISION:
#                 dis = get_dis(enemy.predict_x, enemy.predict_y)
#                 if ret_dis2 == None or dis < ret_dis2:
#                     ret_dis2, ret_key2 = dis, k
#         if ret_key1 != None:
#             self.grab_player = othPlayers[ret_key1]
#             return
#         if ret_key2 != None:
#             self.grab_player = othPlayers[ret_key2]
#             return
#         self.grab_player = None

#     '''
#     判断相关
#     1. 判断(x, y, step)我是不是更快
#     2. 判断(x, y, move)是不是传送门，是的话我要去堵
#     '''

#     def match_self_fast(self, x, y, step):
#         for k, mfish in mPlayers.iteritems():
#             if mfish.sleep == True:
#                 continue
#             dis = mLegStart.get_short_length(mfish.x, mfish.y, x, y)
#             if dis <= step and True == self.try_close(mfish, x, y, step):
#                 return True
#         return False

#     def match_tunnel_after_move(self, x, y, move):
#         ux, uy = self.go_next(x, y, move)
#         if False == mLegStart.match_tunnel(ux, uy):
#             return False
#         return True

#     # def get_close(self, players):
#     #     if len(players) == 0:
#     #         return
#     #     limit_point = set()

#     #     def bfs(player):
#     #         import Queue
#     #         q = Queue.Queue()
#     #         vis = set()
#     #         start = mLegStart.get_cell_id(player.x, player.y)

#     #         q.put(("", start, 0))
#     #         vis.add(start)

#     #         while False == q.empty():
#     #             umove, uid, ustep = q.get()
#     #             sons = mLegStart.SONS.get(uid, None)
#     #             if True == self.error_no_sons(sons, uid):
#     #                 continue
#     #             for mv, nx, ny in sons:
#     #                 vid = mLegStart.get_cell_id(nx, ny)
#     #                 if ustep == 0:
#     #                     umove = mv
#     #                 if vid in vis:
#     #                     continue
#     #                 if vid in limit_point:
#     #                     continue
#     #                 if nx == self.grab_player.predict_x and ny == self.grab_player.predict_y:
#     #                     limit_point.add(uid)
#     #                     player.move = umove
#     #                     return True
#     #                 vis.add(vid)
#     #                 q.put((umove, vid, ustep + 1))
#     #         dis, move, cell = self.get_min_dis(
#     #             player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
#     #         player.move = move

#     #     def cmp(p1, p2):
#     #         dis1 = mLegStart.get_short_length(
#     #             p1.x, p1.y, self.grab_player.predict_x, self.grab_player.predict_y)
#     #         dis2 = mLegStart.get_short_length(
#     #             p2.x, p2.y, self.grab_player.predict_x, self.grab_player.predict_y)
#     #         if dis1 <= dis2:
#     #             return -1
#     #         return 1

#     #     players = sorted(players, cmp)
#     #     for player in players:
#     #         bfs(player)
#     #         self.record_detial(player, "逼近")

#     def just_eat(self):
#         uid = mLegStart.get_cell_id(
#             self.grab_player.predict_x, self.grab_player.predict_y)
#         sons = mLegStart.SONS.get(uid, None)
#         if True == self.error_no_sons(sons, uid):
#             return False

#         def have_mplayer(x, y):
#             for k, player in mPlayers.iteritems():
#                 if player.sleep == True:
#                     continue
#                 dis1 = mLegStart.get_short_length(player.x, player.y, x, y)
#                 dis2 = mLegStart.get_short_length(x, y, player.x, player.y)
#                 if dis1 <= 1 and dis2 <= 1:
#                     return True
#                 # if player.x == x and player.y == y:
#                     # return True
#             return False

#         for mv, nx, ny in sons:
#             if False == have_mplayer(nx, ny):
#                 return False
#         for k, player in mPlayers.iteritems():
#             if player.sleep == True:
#                 continue
#             dis, move, cell = self.get_min_dis(
#                 player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
#             # if dis <= 1:
#             player.move = move
#             # break
#         return True

#     def get_close(self, players):
#         if len(players) == 0:
#             return

#         import Queue
#         q = Queue.Queue()
#         vis = set()
#         record_action = dict()

#         grab_label, mlabel = 0, 1
#         grab_start = mLegStart.get_cell_id(
#             self.grab_player.predict_x, self.grab_player.predict_y)
#         vis.add((grab_start, grab_label))
#         q.put((-1, "", grab_start, 0, grab_label))

#         used_pid = set()

#         tol_can_use = 0

#         for player in players:
#             if player.sleep == True:
#                 continue
#             start = mLegStart.get_cell_id(player.x, player.y)
#             vis.add((start, mlabel))
#             record_action[start] = {"pid": player.id, "move": ""}
#             q.put((player.id, "", start, 0, mlabel))
#             tol_can_use += 1

#         mLogger.info(record_action)

#         while False == q.empty():
#             pid, umove, uid, ustep, ulabel = q.get()
#             if pid in used_pid:
#                 continue
#             # if len(used_pid) == tol_can_use - 1:
#             #     break

#             sons = mLegStart.SONS.get(uid, None)
#             if True == self.error_no_sons(sons, uid):
#                 continue
#             for mv, nx, ny in sons:
#                 if ustep == 0:
#                     umove = mv

#                 vid = mLegStart.get_cell_id(nx, ny)
#                 grab_pair = (vid, grab_label)
#                 mpair = (vid, mlabel)

#                 if ulabel == grab_label:
#                     if grab_pair in vis:
#                         continue
#                     if mpair in vis:
#                         mpid = record_action[vid]["pid"]
#                         if mpid in used_pid:
#                             continue
#                         move = record_action[vid]["move"]
#                         mPlayers[mpid].move = move
#                         used_pid.add(mpid)
#                         mLogger.info("[敌人撞墙: ({}, {})] [player: {}; point: ({}, {}); move: {}]".format(
#                             nx, ny, mpid, mPlayers[mpid].x, mPlayers[mpid].y, mPlayers[mpid].move
#                         ))
#                         continue
#                     vis.add(grab_pair)
#                     q.put((pid, umove, vid, ustep + 1, ulabel))
#                 else:
#                     if mpair in vis:
#                         continue
#                     if grab_pair in vis and pid not in used_pid:
#                         mPlayers[pid].move = umove
#                         used_pid.add(pid)
#                         mLogger.info("[我要围捕: ({}, {})] [player: {}; point: ({}, {}); move: {}]".format(
#                             nx, ny, pid, mPlayers[pid].x, mPlayers[pid].y, mPlayers[pid].move
#                         ))
#                     record_action[vid] = {"pid": pid, "move": umove}
#                     vis.add(mpair)
#                     q.put((pid, umove, vid, ustep + 1, mlabel))
#         for k, player in mPlayers.iteritems():
#             if player.sleep == True:
#                 continue
#             if player.id in used_pid:
#                 continue
#             dis, move, cell = self.get_min_dis(
#                 player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
#             player.move = move
#             self.record_detial(player, "跳出算法")

#     # 敌人到px, px 走了step步
#     def try_close(self, player, px, py, step):
#         dis, move, cell = self.get_min_dis(
#             player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
#         gox, goy = mLegStart.get_x_y(cell)
#         dis, move, cell = self.get_min_dis(gox, goy, px, py)
#         if dis <= step - 1:
#             return True
#         return False

#     def send_near_player(self, x, y, step):
#         '''
#         1. 找一个离(x, y)最近的鱼
#         2. 我比敌人至少快两步，我就逼近。否则我就堵门
#         '''
#         ret_dis, ret_key, ret_move = None, None, None

#         num = 0
#         for k, player in mPlayers.iteritems():
#             if player.sleep == True:
#                 continue
#             if player.id in self.USED_PLAYER_ID:
#                 continue
#             dis, move, cell = self.get_min_dis(player.x, player.y, x, y)
#             if ret_dis == None or dis < ret_dis:
#                 ret_dis, ret_key, ret_move = dis, k, move
#             num += 1
#         if num <= 4:
#             return False

#         if ret_key == None:
#             return False
#         if ret_dis <= (step - 2) and True == self.try_close(player, x, y, step-1):
#             return False

#         self.USED_PLAYER_ID.add(mPlayers[ret_key].id)
#         mPlayers[ret_key].move = ret_move
#         mLogger.info("[传送门: ({}, {}); 敌人的距离: {}] [player: {}; point: ({}, {}); move: {}; 我的距离: {}]".format(
#             x, y, step, mPlayers[ret_key].id, mPlayers[ret_key].x, mPlayers[ret_key].y, mPlayers[ret_key].move, ret_dis
#         ))
#         return True

#     def start_grab(self):
#         import Queue
#         q = Queue.Queue()
#         vis = set()

#         start = mLegStart.get_cell_id(
#             self.grab_player.predict_x, self.grab_player.predict_y)
#         q.put((start, 0))
#         vis.add(start)

#         while False == q.empty():
#             uid, ustep = q.get()
#             ux, uy = mLegStart.get_x_y(uid)
#             sons = mLegStart.SONS.get(uid, None)

#             if True == self.error_no_sons(sons, uid):
#                 continue

#             for mv, nx, ny in sons:
#                 vid = mLegStart.get_cell_id(nx, ny)
#                 if vid in vis:
#                     continue
#                 if self.match_self_fast(nx, ny, ustep + 1):
#                     continue

#                 # 传送带传过来的，并且找到了堵门的
#                 if True == self.match_tunnel_after_move(ux, uy, mv):
#                     flag = self.send_near_player(nx, ny, ustep + 1)
#                     if True == flag:
#                         tunl_sons = mLegStart.SONS.get(vid, None)
#                         if True == self.error_no_sons(tunl_sons, vid):
#                             continue
#                         for tunl_mv, tunl_x, tunl_y in tunl_sons:
#                             tunl_id = mLegStart.get_cell_id(tunl_x, tunl_y)
#                             vis.add(tunl_id)
#                 q.put((vid, ustep + 1))
#                 vis.add(vid)

#         players = []
#         for k, player in mPlayers.iteritems():
#             if player.sleep == True:
#                 continue
#             if player.id in self.USED_PLAYER_ID:
#                 continue
#             players.append(player)
#         self.get_close(players)

#     def eat_power(self, player, used_power):
#         powers = self.mRoundObj.msg['msg_data'].get('power', None)
#         if None == powers:
#             return False

#         ret_dis, ret_move, ret_id = None, None, None
#         for power in powers:
#             if False == self.judge_in_vision(player.x, player.y, power['x'], power['y']):
#                 continue
#             power_id = mLegStart.get_cell_id(power['x'], power['y'])
#             if power_id in used_power:
#                 continue
#             dis, move, cell = self.get_min_dis(
#                 player.x, player.y, power['x'], power['y'])
#             if ret_dis == None or dis < ret_dis:
#                 ret_dis, ret_move, ret_id = dis, move, power_id
#         if ret_move == None:
#             return False
#         player.move = ret_move
#         used_power.add(ret_id)
#         return True

#     def expand_vision(self):
#         players = []
#         used_power = set()
#         for k, player in mPlayers.iteritems():
#             if player.sleep == True:
#                 continue
#             if True == self.eat_power(player, used_power):
#                 continue
#             players.append(player)
#         if len(players) == 0:
#             return

#         all_enums = self.get_all_enums(players)
#         max_count, ret_enum = None, None

#         for enum in all_enums:
#             vision_count = set()
#             for pid, em, ex, ey in enum:
#                 width, height = mLegStart.width, mLegStart.height
#                 vision = mLegStart.msg['msg_data']['map']['vision']
#                 # vision = 10
#                 x1, y1 = max(0, ex - vision), max(0, ey - vision)
#                 x2 = min(width - 1, ex + vision)
#                 y2 = min(height - 1, ey + vision)

#                 for i in range(x1, x2 + 1):
#                     for j in range(y1, y2 + 1):
#                         cell = mLegStart.get_cell_id(i, j)
#                         vision_count.add(cell)

#                 if max_count == None or len(vision_count) > max_count:
#                     max_count, ret_enum = len(vision_count), enum

#         if ret_enum == None:
#             mLogger.warning("[没有枚举的情况]")
#             return

#         mLogger.info("[max_count: {}; ret_enum: {}".format(
#             max_count, ret_enum))
#         for pid, em, ex, ey in ret_enum:
#             mPlayers[pid].move = em

#     def do_excute(self):
#         self.USED_PLAYER_ID.clear()
#         self.confirm_grab_player()

#         alive_num = 0
#         for k, player in mPlayers.iteritems():
#             if player.sleep == True:
#                 continue
#             alive_num += 1

#         # 只要这回合抓鱼，就不可能巡逻。把之前的巡逻初始化掉
#         if self.grab_player != None and alive_num >= 3:
#             # self.init_vision_point()
#             mLogger.info("有敌人，可以追击......")
#             mLogger.info("[敌人] [player: {}; point: ({}, {}); predict: ({}, {}); lost: {}]".format(
#                 self.grab_player.id,
#                 self.grab_player.x,
#                 self.grab_player.y,
#                 self.grab_player.predict_x,
#                 self.grab_player.predict_y,
#                 self.grab_player.lost_vision_num
#             ))
#             if False == self.just_eat():
#                 self.start_grab()
#         else:
#             mLogger.info("没有敌人，开始巡航......")
#             self.expand_vision()


class DoThink(Action):
    def __init__(self):
        super(DoThink, self).__init__()
        self.LIMIT_LOST_VISION = 1

    def init(self):
        pass

    def bfs(self, enemy):
        import Queue
        q = Queue.Queue()
        vis = set()
        record_action = dict()
        enemy_label, mlabel = 0, 1
        enemy_start = mLegStart.get_cell_id(enemy.predict_x, enemy.predict_y)
        vis.add((enemy_start, enemy_label))
        q.put((-1, "", enemy_start, 0, enemy_label))
        used_pid = set()
        tol_can_use = 0

        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            start = mLegStart.get_cell_id(player.x, player.y)
            vis.add((start, mlabel))
            record_action[start] = {"pid": player.id, "move": ""}
            q.put((player.id, "", start, 0, mlabel))
            tol_can_use += 1

        mLogger.info(record_action)
        while False == q.empty():
            pid, umove, uid, ustep, ulabel = q.get()
            if ustep >= 6:
                break
            if pid in used_pid:
                continue
            sons = mLegStart.SONS.get(uid, None)
            if True == self.error_no_sons(sons, uid):
                continue
            for mv, nx, ny in sons:
                if ustep == 0:
                    umove = mv
                vid = mLegStart.get_cell_id(nx, ny)
                grab_pair = (vid, enemy_label)
                mpair = (vid, mlabel)

                if ulabel == enemy_label:
                    if grab_pair in vis:
                        continue
                    if mpair in vis:
                        mpid = record_action[vid]["pid"]
                        if mpid in used_pid:
                            continue
                        move = record_action[vid]["move"]
                        mPlayers[mpid].move = move
                        used_pid.add(mpid)
                        mLogger.info("[敌人撞墙: ({}, {})] [player: {}; point: ({}, {}); move: {}; dis: {}]".format(
                            nx, ny, mpid, mPlayers[mpid].x, mPlayers[mpid].y, mPlayers[mpid].move, ustep + 1
                        ))
                        continue
                    vis.add(grab_pair)
                    q.put((pid, umove, vid, ustep + 1, ulabel))
                else:
                    if mpair in vis:
                        continue
                    if grab_pair in vis and pid not in used_pid:
                        mPlayers[pid].move = umove
                        used_pid.add(pid)
                        mLogger.info("[我要围捕: ({}, {})] [player: {}; point: ({}, {}); move: {}; dis: {}]".format(
                            nx, ny, pid, mPlayers[pid].x, mPlayers[pid].y, mPlayers[pid].move, ustep + 1
                        ))
                    record_action[vid] = {"pid": pid, "move": umove}
                    vis.add(mpair)
                    q.put((pid, umove, vid, ustep + 1, mlabel))
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in used_pid:
                continue
            dis, move, cell = self.get_min_dis(
                player.x, player.y, enemy.predict_x, enemy.predict_y)
            player.move = move
            self.record_detial(player, "跳出算法")

    def start_grab(self):
        flag = False
        for k, enemy in othPlayers.iteritems():
            if enemy.visiable == False:
                continue
            if enemy.predict_x == None:
                continue
            if enemy.lost_vision_num > self.LIMIT_LOST_VISION:
                continue
            if True == self.just_eat(enemy):
                return True
            mLogger.info("[敌人] [player: {}; point: ({}, {}); predict: ({}, {}); lost: {}]".format(
                enemy.id, enemy.x, enemy.y, enemy.predict_x, enemy.predict_y, enemy.lost_vision_num
            ))
            self.bfs(enemy)
            flag = True
        return flag

    def eat_power(self, player, used_power):
        powers = self.mRoundObj.msg['msg_data'].get('power', None)
        if None == powers:
            return False

        ret_dis, ret_move, ret_id, ret_cell = None, None, None, None
        for power in powers:
            if False == self.judge_in_vision(player.x, player.y, power['x'], power['y']):
                continue
            power_id = mLegStart.get_cell_id(power['x'], power['y'])
            if power_id in used_power:
                continue
            dis, move, cell = self.get_min_dis(
                player.x, player.y, power['x'], power['y'])
            if ret_dis == None or dis < ret_dis:
                ret_dis, ret_move, ret_id, ret_cell = dis, move, power_id, cell
        if ret_move == None:
            return False
        player.move = ret_move
        used_power.add(ret_id)
        px, py = mLegStart.get_x_y(ret_cell)
        info = "能量 ({}, {})".format(px, py)
        self.record_detial(player, info)
        return True

    def expand_vision(self):
        players = []
        used_power = set()
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if True == self.eat_power(player, used_power):
                continue
            players.append(player)
        if len(players) == 0:
            return

        all_enums = self.get_all_enums(players)
        max_count, ret_enum = None, None

        for enum in all_enums:
            vision_count = set()
            for pid, em, ex, ey in enum:
                width, height = mLegStart.width, mLegStart.height
                vision = mLegStart.msg['msg_data']['map']['vision']
                # vision = 10
                x1, y1 = max(0, ex - vision), max(0, ey - vision)
                x2 = min(width - 1, ex + vision)
                y2 = min(height - 1, ey + vision)

                for i in range(x1, x2 + 1):
                    for j in range(y1, y2 + 1):
                        cell = mLegStart.get_cell_id(i, j)
                        vision_count.add(cell)

                if max_count == None or len(vision_count) > max_count:
                    max_count, ret_enum = len(vision_count), enum

        if ret_enum == None:
            mLogger.warning("[没有枚举的情况]")
            return

        mLogger.info("[max_count: {}; ret_enum: {}".format(
            max_count, ret_enum))
        for pid, em, ex, ey in ret_enum:
            mPlayers[pid].move = em

    def just_eat(self, enemy):
        uid = mLegStart.get_cell_id(enemy.predict_x, enemy.predict_y)
        sons = mLegStart.SONS.get(uid, None)
        if True == self.error_no_sons(sons, uid):
            return False

        def have_mplayer(x, y):
            for k, player in mPlayers.iteritems():
                if player.sleep == True:
                    continue
                dis1 = mLegStart.get_short_length(player.x, player.y, x, y)
                dis2 = mLegStart.get_short_length(x, y, player.x, player.y)
                if dis1 <= 1 and dis2 <= 1:
                    return True
                # if player.x == x and player.y == y:
                    # return True
            return False

        for mv, nx, ny in sons:
            if False == have_mplayer(nx, ny):
                return False
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            dis, move, cell = self.get_min_dis(player.x, player.y, enemy.predict_x, enemy.predict_y)
            # if dis <= 1:
            player.move = move
            self.record_detial(player, "逼近")
            return True
            # break
        # return True

    def do_excute(self):
        if False == self.start_grab():
            self.expand_vision()


mDoThink = DoThink()
