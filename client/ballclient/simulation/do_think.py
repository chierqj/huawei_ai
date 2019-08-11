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


class DoThink(Action):
    def __init__(self):
        super(DoThink, self).__init__()

    def reward_power(self, player, move, px, py):
        max_weight, sum_weight = 0, 0
        for k, power in self.mRoundObj.POWER_WAIT_SET.iteritems():
            # 我到金币的
            dis = mLegStart.get_short_length(px, py, power.x, power.y)
            weight = 1.0 / math.exp(dis)

            if power.visiable == False:
                dis = config.POWER_ALPHA * dis + config.POWER_BELAT * power.last_appear_dis
                weight = 0.0 if dis == 0 else 1.0 / math.exp(dis)

            max_weight = max(max_weight, weight)
            sum_weight += weight

            mLogger.info("{} [my_fish: {}; point: ({}, {});] [power_value: {}; point: ({}, {})] [dis: {}] [weight: {:.10f}]".format(
                move, player.id, player.x, player.y, power.point, power.x, power.y, dis, weight))

        max_weight *= config.THINK_POWER_WEIGHT
        sum_weight *= config.THINK_POWER_WEIGHT

        nweight = self.weight_moves.get(move, 0)
        # self.weight_moves[move] = float("%.10f" % (nweight + sum_weight))
        self.weight_moves[move] = float("%.10f" % (nweight + max_weight))

    def reward_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.reward_power(player, move, go_x, go_y)

    def punish_vis_cell(self, player, move, px, py):
        cell_id = mLegStart.get_cell_id(px, py)
        if cell_id in player.vis_cell:
            nweight = self.weight_moves.get(move, 0)

            mLogger.info("{} [my_fish: {}; point: ({}, {});] [vis_cell_point: ({}, {})] [weight: {:.10f}]".format(
                move, player.id, player.x, player.y, px, py, config.CELL_WEIGHT))

            self.weight_moves[move] = float(
                "%.10f" % (nweight - config.CELL_WEIGHT))


    def punish_player(self, player, move, px, py):
        max_weight, sum_weight = 0, 0
        for k, oth_player in othPlayers.iteritems():
            # 敌人到我的，敌人要吃我
            dis = mLegStart.get_short_length(
                oth_player.x, oth_player.y, px, py)
            weight = 1.0 / math.exp(dis)

            if oth_player.visiable == False:
                dis = config.PLAYER_ALPHA * dis + config.PLAYER_BELTA * oth_player.last_appear_dis
                weight = 0.0 if dis == 0 else 1.0 / math.exp(dis)

            max_weight = max(max_weight, weight)
            sum_weight += weight
            mLogger.info("{} [my_fish: {}; point: ({}, {});] [othfish: {}; point: ({}, {})] [dis: {}] [weight: {:.10f}]".format(
                move, player.id, player.x, player.y, oth_player.id, oth_player.x, oth_player.y, dis, weight))

        max_weight *= config.THINK_PLAYER_WEIGHT
        sum_weight *= config.THINK_PLAYER_WEIGHT
        nweight = self.weight_moves.get(move, 0)
        # self.weight_moves[move] = float("%.10f" % (nweight + sum_weight))
        self.weight_moves[move] = float("%.10f" % (nweight + max_weight))


    def punish_weight(self, player, next_one_points):
        for move, go_x, go_y in next_one_points:
            self.punish_player(player, move, go_x, go_y)
            self.punish_vis_cell(player, move, go_x, go_y)


mDoThink = DoThink()
