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

    def match_escape(self, player):
        for k, oth_player in othPlayers.iteritems():
            if oth_player.predict_x == None:
                continue
            if oth_player.visiable == False and oth_player.lost_vision_num > self.LIMIT_LOST_VISION:
                continue
            dis = mLegStart.get_short_length(
                oth_player.predict_x, oth_player.predict_y, player.x, player.y)
            if dis <= 5:
                return True
        return False

    def escape(self, player):
        ans_move = ""

        def bfs():
            import Queue
            q = Queue.Queue()
            vis = set()

            cell = mLegStart.get_cell_id(player.x, player.y)
            q.put((0, "", player.x, player.y))
            vis.add(cell)

            def judge_enemy(x, y, c_step):
                for k, oth_player in othPlayers.iteritems():
                    if oth_player.predict_x == None:
                        continue
                    if oth_player.visiable == False and oth_player.lost_vision_num > self.LIMIT_LOST_VISION:
                        continue
                    dis = mLegStart.get_short_length(
                        oth_player.predict_x, oth_player.predict_y, x, y)
                    if dis <= c_step:
                        return False
                return True

            while False == q.empty():
                step, move, ux, uy = q.get()
                player.move = move
                next_one_points = self.get_next_one_points(ux, uy)

                for mv, nx, ny in next_one_points:
                    v_cell = mLegStart.get_cell_id(nx, ny)
                    if v_cell in vis:
                        continue
                    # if False == self.judge_in_vision(player.x, player.y, nx, ny):
                    #     continue
                    if step == 0:
                        move = mv

                    if judge_enemy(nx, ny, step + 1) == False:
                        continue

                    vis.add(v_cell)
                    q.put((step+1, move, nx, ny))
        bfs()
        # player.move = ans_move

    def do_excute(self):
        self.update_predict()
        players = []
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue

            # round_id = self.mRoundObj.msg['msg_data']['round_id']
            # if round_id > 145 and round_id < 150:
            #     player.move = ""
            #     continue

            if self.match_escape(player) == True:
                self.escape(player)
                continue
            players.append(player)
            # self.travel(player)
        self.eat_power_or_travel(players)

    # # 能量值奖励评分
    # def reward_power(self, player, move, px, py):
    #     max_weight, sum_weight = 0, 0
    #     for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
    #         # 我到金币的
    #         dis = mLegStart.get_short_length(px, py, power.x, power.y)
    #         weight = float("%.5f" % (1.0 / math.exp(dis)))

    #         if power.visiable == False:
    #             dis = config.POWER_ALPHA * dis + config.POWER_BELAT * power.last_appear_dis
    #             weight = 0.0 if dis == 0 else float(
    #                 "%.5f" % (1.0 / math.exp(dis)))

    #         max_weight = max(max_weight, weight)
    #         sum_weight += weight

    #         if config.record_weight == True:
    #             mLogger.info("{} [my_fish: {}; point: ({}, {});] [power_value: {}; point: ({}, {})] [dis: {}] [weight: {:.5f}]".format(
    #                 move, player.id, player.x, player.y, power.point, power.x, power.y, dis, weight))

    #     max_weight *= config.BEAT_POWER_WEIGHT
    #     sum_weight *= config.BEAT_POWER_WEIGHT

    #     nweight = self.weight_moves.get(move, 0)
    #     self.weight_moves[move] = float("%.5f" % (nweight + sum_weight))

    # # 奖励评分
    # def reward_weight(self, player, next_one_points):
    #     for move, go_x, go_y in next_one_points:
    #         self.reward_power(player, move, go_x, go_y)

    # # 访问过的节点的惩罚评分，防止逛街
    # def punish_vis_point(self, player, move, px, py):
    #     cell_id = mLegStart.get_cell_id(px, py)
    #     if cell_id in player.vis_point_count:
    #         nweight = self.weight_moves.get(move, 0)

    #         self.weight_moves[move] = float(
    #             "%.5f" % (nweight - config.CELL_WEIGHT))

    #         if config.record_weight == True:
    #             mLogger.info("{} [my_fish: {}; point: ({}, {});] [vis_cell_point: ({}, {})] [weight: {:.5f}]".format(
    #                 move, player.id, player.x, player.y, px, py, config.CELL_WEIGHT))

    # # 敌人的惩罚评分
    # def punish_player(self, player, move, px, py):
    #     max_weight, sum_weight = 0, 0
    #     flag = False
    #     for k, oth_player in othPlayers.iteritems():
    #         if oth_player.visiable == False:
    #             continue
    #         # if False == self.judge_in_vision(oth_player.x, oth_player.y, player.x, player.y):
    #         #     continue
    #         flag = True
    #         # 敌人到我的，敌人要吃我
    #         dis = mLegStart.get_short_length(
    #             oth_player.x, oth_player.y, px, py)
    #         weight = float("%.5f" % (1.0 / math.exp(dis)))

    #         max_weight = max(max_weight, weight)
    #         sum_weight += weight

    #         if config.record_weight == True:
    #             mLogger.info("{} [my_fish: {}; point: ({}, {});] [othfish: {}; point: ({}, {})] [dis: {}] [weight: {:.5f}]".format(
    #                 move, player.id, player.x, player.y, oth_player.id, oth_player.x, oth_player.y, dis, weight))

    #     max_weight *= config.BEAT_PLAYER_WEIGHT
    #     sum_weight *= config.BEAT_PLAYER_WEIGHT

    #     nweight = self.weight_moves.get(move, 0)
    #     self.weight_moves[move] = float("%.5f" % (nweight + sum_weight))

    # # 惩罚评分
    # def punish_weight(self, player, next_one_points):
    #     for move, go_x, go_y in next_one_points:
    #         self.punish_player(player, move, go_x, go_y)
    #         self.punish_vis_point(player, move, go_x, go_y)

    # def select_best_move(self):
    #     max_weight, ret_move = None, None
    #     for move, weight in self.weight_moves.iteritems():
    #         if max_weight == None or weight > max_weight:
    #             max_weight, ret_move = weight, move
    #     return ret_move

    # # 入口调用
    # def do_excute(self):
    #     self.update_predict()
    #     vis_point = set()
    #     for k, player in mPlayers.iteritems():
    #         if player.sleep == True:
    #             continue
    #         # if False == self.match_escape(player):
    #         #     self.travel(player)
    #         #     continue
    #         round_id = self.mRoundObj.msg['msg_data']['round_id']
    #         if round_id > 145 and round_id <= 150:
    #             player.move = ""
    #             self.record_detial(player)
    #             continue

    #         next_one_points = self.get_next_one_points(
    #             player.x, player.y, vis_point)
    #         if len(next_one_points) == 0:
    #             player.move = ""
    #             continue

    #         self.weight_moves.clear()
    #         self.reward_weight(player, next_one_points)
    #         self.punish_weight(player, next_one_points)

    #         ret_move = self.select_best_move()
    #         player.move = ret_move

    #         ret_x, ret_y = self.mRoundObj.real_go_point(
    #             player.x, player.y, ret_move)
    #         ret_cell_id = mLegStart.get_cell_id(ret_x, ret_y)
    #         vis_point.add(ret_cell_id)

    #         self.record_detial(player)
mDoBeat = DoBeat()
