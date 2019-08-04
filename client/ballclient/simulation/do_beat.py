# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
import random


class DoBeat():
    def __init__(self):
        self.mRoundObj = ""

        self.mPlayer = ""
        # 被吃的8个方向，顺带自己这个格子。总共9个
        # self.dinger_dirs = [(-1, -1), (0, -1), (1, -1), (-1, 0),
        #                     (1, 0), (-1, 1), (0, 1), (1, 1), (0, 0)]
        # 被吃的4个方向，顺带自己这个格子。总共5个
        self.dinger_dirs = [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]
        # 被吃的1个方向，即就是下一步在的位置
        # self.dinger_dirs = [(0, 0)]

    # 获取两点的曼哈顿距离
    def get_dis(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    # 判断px, py这个位置能不能被吃，True表示能被吃
    def match_beat_eated(self, px, py):
        for player in self.mRoundObj.msg['msg_data']['players']:
            if player['team'] != config.team_id:
                for x, y in self.dinger_dirs:
                    nx, ny = player['x'] + x, player['y'] + y
                    if nx == px and ny == py:
                        return True
        return False

    def record_detial(self, move, text):
        if False == config.record_detial or None == move:
            return
        round_id = self.mRoundObj.msg['msg_data']['round_id']
        player_id = self.mPlayer['id']
        mLogger.info('[round: {}, fish: {}, from: ({}, {}), move: {}] {}'.format(
            round_id, player_id, self.mPlayer['x'], self.mPlayer['y'], move, text))

    # 计算可以行走 & 不被吃的方向
    def get_safe_moves(self):
        moves = ['up', 'down', 'left', 'right']
        result = []
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(
                self.mPlayer['x'], self.mPlayer['y'], move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if True == self.match_beat_eated(go_x, go_y):
                continue
            result.append((move, go_x, go_y))
        return result

    # 向金币方向移动
    def move_to_power(self, safe_moves):
        if False == self.mRoundObj.check_power():
            return None
        min_dis, result = 12317, None
        for move, go_x, go_y in safe_moves:
            for power in self.mRoundObj.msg['msg_data']['power']:
                x, y = power['x'], power['y']
                short_length = mLegStart.get_short_length(go_x, go_y, x, y)
                if short_length != None and short_length < min_dis:
                    min_dis, result = short_length, move
        return result

      # 判断当前self.mPlayer是不是身处虫洞
    def is_wromhole(self):
        cell = mLegStart.get_graph_cell(self.mPlayer['x'], self.mPlayer['y'])
        if cell.isalpha():
            return True
        return False

    # 向虫洞方向移动
    def move_to_wrom_hole(self, safe_moves):
        if True == self.is_wromhole():
            return None
        if False == self.mRoundObj.check_wormhole():
            return None
        min_dis, result = 12317, None
        for move, go_x, go_y in safe_moves:
            for wormhole in mLegStart.msg['msg_data']['map']['wormhole']:
                x, y = wormhole['x'], wormhole['y']
                short_length = mLegStart.get_short_length(go_x, go_y, x, y)
                if short_length != None and short_length < min_dis:
                    min_dis, result = short_length, move
        return result

    # 在可行的移动方向内随机游走，如果可行方向为空，那就随机四个方向
    def move_random_walk(self, safe_moves):
        length = len(safe_moves)
        if length == 0:
            return self.mRoundObj.direction[random.randint(1, 12317) % 4 + 1]
        rd = random.randint(1, 12317) % length
        return safe_moves[rd][0]

    # 获取下一步的移动方向；
    def get_direct(self):
        # 上下左右四个方向，哪个可以行走(边界 & 安全)
        safe_moves = self.get_safe_moves()

        # 如果safe_moves为None，表示都不安全，随机游走听天命
        if len(safe_moves) == 0:
            self.record_detial("random", "不安全听天命")
            return self.move_random_walk(safe_moves)

        result = None

        # 第一优先级：吃金币
        result = self.move_to_power(safe_moves)
        if result != None:
            self.record_detial(result, "吃金币")
            return result

        # 第二优先级；找虫洞
        result = self.move_to_wrom_hole(safe_moves)
        if result != None:
            self.record_detial(result, "找虫洞")
            return result

        # 第三优先级；在安全的方向内随机游走
        result = self.move_random_walk(safe_moves)
        self.record_detial(result, "随机游走")

        return result

    def excute(self, mRoundObj, player):
        self.mRoundObj = mRoundObj
        self.mPlayer = player
        return self.get_direct()


mDoBeat = DoBeat()
