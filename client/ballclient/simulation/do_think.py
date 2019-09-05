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
        self.grab_player = None
        self.USED_PLAYER_ID = set()     # 堵传送门用到的鱼的id
        self.LIMIT_LOST_VISION = 1

    def init(self):
        self.grab_player = None
        self.USED_PLAYER_ID.clear()
        self.USED_VISION_POINT.clear()

    def confirm_grab_player(self):
        if self.grab_player != None and self.grab_player.lost_vision_num <= self.LIMIT_LOST_VISION:
            return

        ret_key = None
        for k, enemy in othPlayers.iteritems():
            # if enemy.score <= 5:
            #     continue
            if enemy.visiable == True:
                self.grab_player = enemy
                return
            if enemy.predict_x == None:
                continue
            if enemy.lost_vision_num <= self.LIMIT_LOST_VISION:
                ret_key = k
        if ret_key == None:
            self.grab_player = None
        else:
            self.grab_player = othPlayers[ret_key]

    def error_no_sons(self, sons, uid):
        ux, uy = mLegStart.get_x_y(uid)
        if sons == None:
            mLogger.warning(
                "[没有儿子] [uid: {}; point: ({}, {})]".format(uid, ux, uy))
            return True
        return False

    '''
    判断相关
    1. 判断(x, y, step)我是不是更快
    2. 判断(x, y, move)是不是传送门，是的话我要去堵
    '''

    def match_self_fast(self, x, y, step):
        for k, mfish in mPlayers.iteritems():
            if mfish.sleep == True:
                continue
            dis = mLegStart.get_short_length(mfish.x, mfish.y, x, y)
            if dis <= step and True == self.try_close(mfish, x, y, step):
                return True
        return False

    def match_tunnel_after_move(self, x, y, move):
        ux, uy = self.go_next(x, y, move)
        if False == mLegStart.match_tunnel(ux, uy):
            return False
        return True

    def get_close(self, players):
        if len(players) == 0:
            return
        limit_point = set()

        def bfs(player):
            import Queue
            q = Queue.Queue()
            vis = set()
            start = mLegStart.get_cell_id(player.x, player.y)

            q.put(("", start, 0))
            vis.add(start)

            while False == q.empty():
                umove, uid, ustep = q.get()
                sons = mLegStart.SONS.get(uid, None)
                if True == self.error_no_sons(sons, uid):
                    continue
                for mv, nx, ny in sons:
                    vid = mLegStart.get_cell_id(nx, ny)
                    if ustep == 0:
                        umove = mv
                    if vid in vis:
                        continue
                    if vid in limit_point:
                        continue
                    if nx == self.grab_player.predict_x and ny == self.grab_player.predict_y:
                        limit_point.add(uid)
                        player.move = umove
                        return True
                    vis.add(vid)
                    q.put((umove, vid, ustep + 1))
            dis, move, cell = self.get_min_dis(
                player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
            player.move = move

        def cmp(p1, p2):
            dis1 = mLegStart.get_short_length(
                p1.x, p1.y, self.grab_player.predict_x, self.grab_player.predict_y)
            dis2 = mLegStart.get_short_length(
                p2.x, p2.y, self.grab_player.predict_x, self.grab_player.predict_y)
            if dis1 <= dis2:
                return -1
            return 1

        players = sorted(players, cmp)
        for player in players:
            bfs(player)
            self.record_detial(player, "逼近")

        # dis, move, cell = self.get_min_dis(
        #     player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
        # player.move = move
        # self.record_detial(player, "逼近")

    # 敌人到px, px 走了step步
    def try_close(self, player, px, py, step):
        dis, move, cell = self.get_min_dis(
            player.x, player.y, self.grab_player.predict_x, self.grab_player.predict_y)
        gox, goy = mLegStart.get_x_y(cell)
        dis, move, cell = self.get_min_dis(gox, goy, px, py)
        if dis <= step - 1:
            return True
        return False

    def send_near_player(self, x, y, step):
        '''
        1. 找一个离(x, y)最近的鱼
        2. 我比敌人至少快两步，我就逼近。否则我就堵门
        '''
        ret_dis, ret_key, ret_move = None, None, None

        num = 0
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            dis, move, cell = self.get_min_dis(player.x, player.y, x, y)
            if ret_dis == None or dis < ret_dis:
                ret_dis, ret_key, ret_move = dis, k, move
            num += 1
        # if num <= 1:
        #     return False

        if ret_key == None:
            return False
        if ret_dis <= (step - 2) and True == self.try_close(player, x, y, step-1):
            return False

        self.USED_PLAYER_ID.add(mPlayers[ret_key].id)
        mPlayers[ret_key].move = ret_move
        mLogger.info("[传送门: ({}, {}); 敌人的距离: {}] [player: {}; point: ({}, {}); move: {}; 我的距离: {}]".format(
            x, y, step, mPlayers[ret_key].id, mPlayers[ret_key].x, mPlayers[ret_key].y, mPlayers[ret_key].move, ret_dis
        ))
        return True

    def start_grab(self):
        import Queue
        q = Queue.Queue()
        vis = set()

        start = mLegStart.get_cell_id(
            self.grab_player.predict_x, self.grab_player.predict_y)
        q.put((start, 0))
        vis.add(start)

        while False == q.empty():
            uid, ustep = q.get()
            ux, uy = mLegStart.get_x_y(uid)
            sons = mLegStart.SONS.get(uid, None)

            if True == self.error_no_sons(sons, uid):
                continue

            for mv, nx, ny in sons:
                vid = mLegStart.get_cell_id(nx, ny)
                if vid in vis:
                    continue
                if self.match_self_fast(nx, ny, ustep + 1):
                    continue

                # 传送带传过来的，并且找到了堵门的
                if True == self.match_tunnel_after_move(ux, uy, mv):
                    flag = self.send_near_player(nx, ny, ustep + 1)
                    if True == flag:
                        tunl_sons = mLegStart.SONS.get(vid, None)
                        if True == self.error_no_sons(tunl_sons, vid):
                            continue
                        for tunl_mv, tunl_x, tunl_y in tunl_sons:
                            tunl_id = mLegStart.get_cell_id(tunl_x, tunl_y)
                            vis.add(tunl_id)
                q.put((vid, ustep + 1))
                vis.add(vid)

        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            if player.id in self.USED_PLAYER_ID:
                continue
            players.append(player)
        self.get_close(players)

    def do_excute(self):
        self.USED_PLAYER_ID.clear()
        self.USED_VISION_POINT.clear()

        self.confirm_grab_player()
        if self.grab_player != None:
            mLogger.info("有敌人，可以追击......")
            mLogger.info("[敌人] [player: {}; point: ({}, {}); predict: ({}, {}); lost: {}]".format(
                self.grab_player.id,
                self.grab_player.x,
                self.grab_player.y,
                self.grab_player.predict_x,
                self.grab_player.predict_y,
                self.grab_player.lost_vision_num
            ))
            self.start_grab()
        else:
            mLogger.info("没有敌人，开始巡航......")
            for k, player in mPlayers.iteritems():
                self.travel(player)


mDoThink = DoThink()
