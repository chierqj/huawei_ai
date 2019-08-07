# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers
import random


class DoThink():
    def __init__(self):
        self.mRoundObj = ""
        # 被吃的8个方向，顺带自己这个格子。总共9个
        # self.dinger_dirs = [(-1, -1), (0, -1), (1, -1), (-1, 0),
        #                     (1, 0), (-1, 1), (0, 1), (1, 1), (0, 0)]
        # 被吃的4个方向，顺带自己这个格子。总共5个
        self.dinger_dirs = [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]
        # 被吃的1个方向，即就是下一步在的位置
        # self.dinger_dirs = [(0, 0)]

        self.continue_catch_fish_num = 0

    # 获取两点的曼哈顿距离
    def get_dis(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    # 判断px, py这个位置能不能被吃，True表示能被吃
    def match_beat_eated(self, px, py):
        return False
        for player in self.mRoundObj.msg['msg_data']['players']:
            if player['team'] != config.team_id:
                for x, y in self.dinger_dirs:
                    nx, ny = player['x'] + x, player['y'] + y
                    if nx == px and ny == py:
                        return True
        return False

    def record_detial(self, player, move, text):
        if False == config.record_detial or None == move:
            return
        round_id = self.mRoundObj.msg['msg_data']['round_id']
        player_id = player.id
        mLogger.info('[round: {}, player: {}, from: ({}, {}), move: {}] {}'.format(
            round_id, player_id, player.x, player.y, move, text))

    # 计算可以行走 & 不被吃的方向
    def get_safe_moves(self, player):
        moves = ['up', 'down', 'left', 'right']
        result = []
        for move in moves:
            # 获取move之后真正到达的位置
            go_x, go_y = self.mRoundObj.real_go_point(
                player.x, player.y, move)
            if False == self.mRoundObj.match_border(go_x, go_y):
                continue
            if True == self.mRoundObj.match_meteor(go_x, go_y):
                continue
            if True == self.match_beat_eated(go_x, go_y):
                continue
            result.append((move, go_x, go_y))
        return result

    # 向金币方向移动
    def move_to_power(self, safe_moves, used_power):
        if False == self.mRoundObj.check_power():
            return None
        min_dis, go_power, result = 12317, -1, None
        for move, go_x, go_y in safe_moves:
            for power in self.mRoundObj.msg['msg_data']['power']:
                x, y = power['x'], power['y']
                cell_id = mLegStart.get_cell_id(x, y)
                if cell_id in used_power:
                    continue
                short_length = mLegStart.get_short_length(go_x, go_y, x, y)
                if short_length != None and short_length < min_dis:
                    min_dis, go_power, result = short_length, cell_id, move
        used_power.add(go_power)
        return result

    # 判断当前player是不是身处虫洞
    def is_wormhole(self, player):
        cell = mLegStart.get_graph_cell(player.x, player.y)
        if cell.isalpha():
            return True
        return False

    # 向虫洞方向移动
    def move_to_wrom_hole(self, player, safe_moves):
        if True == self.is_wormhole(player):
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
    def get_catch_power_direct(self, player, used_power):
        # 上下左右四个方向，哪个可以行走(边界 & 安全)
        safe_moves = self.get_safe_moves(player)

        # 如果safe_moves为None，表示都不安全，随机游走听天命
        if len(safe_moves) == 0:
            self.record_detial(player, "random", "不安全听天命")
            return self.move_random_walk(safe_moves)

        result = None

        # 第一优先级：吃金币
        result = self.move_to_power(safe_moves, used_power)
        if result != None:
            self.record_detial(player, result, "吃金币")
            return result

        # 第二优先级；找虫洞
        result = self.move_to_wrom_hole(player, safe_moves)
        if result != None:
            self.record_detial(player, result, "找虫洞")
            return result

        # 第三优先级；在安全的方向内随机游走
        result = self.move_random_walk(safe_moves)
        self.record_detial(player, result, "随机游走")

        return result

    # 获取下一步的移动方向；
    def get_catch_wromhole_direct(self, player, used_power):
        # 上下左右四个方向，哪个可以行走(边界 & 安全)
        safe_moves = self.get_safe_moves(player)

        # 如果safe_moves为None，表示都不安全，随机游走听天命
        if len(safe_moves) == 0:
            self.record_detial(player, "random", "不安全听天命")
            return self.move_random_walk(safe_moves)

        result = None

        # 第二优先级；找虫洞
        result = self.move_to_wrom_hole(player, safe_moves)
        if result != None:
            self.record_detial(player, result, "找虫洞")
            return result

        # 第一优先级：吃金币
        result = self.move_to_power(safe_moves, used_power)
        if result != None:
            self.record_detial(player, result, "吃金币")
            return result

        # 第三优先级；在安全的方向内随机游走
        result = self.move_random_walk(safe_moves)
        self.record_detial(player, result, "随机游走")

        return result

    def get_grab_player(self):
        min_dis, result = 12317, None
        for k1, mplayer in mPlayers.iteritems():
            for k2, othplayer in othPlayers.iteritems():
                if False == othplayer.visibile:
                    continue
                if True == othplayer.sleep:
                    mLogger.info("恭喜你，成功抓住一条鱼")
                    continue
                if True == mPlayers:
                    continue
                # dis = mLegStart.get_short_length(
                #     mplayer.x, mplayer.y, othplayer.x, othplayer.y)

                dis = int(k2)
                if dis < min_dis:
                    min_dis, result = dis, othplayer
        return result

    def get_send_players(self, grab_player):
        result = []
        for k, mplayer in mPlayers.iteritems():
            dis = mLegStart.get_short_length(
                mplayer.x, mplayer.y, grab_player.x, grab_player.y)
            result.append((dis, mplayer))
        result = sorted(result, key=lambda it: it[0])
        result = [it[1] for it in result]
        return result

    def catch_power(self):
        action, used_power = [], set()
        for k, player in mPlayers.iteritems():
            action.append({
                "team": player.team,
                "player_id": player.id,
                "move": [self.get_catch_power_direct(player, used_power)]
            })
        return action

    def catch_fish(self):
        action, used_power = [], set()

        round_id = self.mRoundObj.msg['msg_data']['round_id']

        grab_player = self.get_grab_player()

        # 看不到被抓的鱼，我就去优先钻虫洞
        if None == grab_player:
            mLogger.info("[round: {}] 找不到被抓的鱼".format(round_id))
            for k, player in mPlayers.iteritems():
                move = ""
                if self.continue_catch_fish_num >= 2:
                    self.continue_catch_fish_num = 0
                    move = self.get_catch_power_direct(player, used_power)
                else:
                    self.continue_catch_fish_num += 1
                    move = self.get_catch_wromhole_direct(player, used_power)
                action.append({
                    "team": player.team,
                    "player_id": player.id,
                    "move": [move]
                })
            return action
        else:
            mLogger.info("[round: {}] 被抓的鱼 {}:({},{})".format(
                round_id, grab_player.id, grab_player.x, grab_player.y))

            # 能看到被抓的鱼，我派出send_catch_num条去抓鱼。其余的吃金币
            send_players = self.get_send_players(grab_player)
            send_catch_num = 3
            for player in send_players[:send_catch_num]:
                move = mLegStart.get_short_move(
                    player.x, player.y, grab_player.x, grab_player.y)
                action.append({
                    "team": player.team,
                    "player_id": player.id,
                    "move": [move]
                })
            for player in send_players[send_catch_num:]:
                action.append({
                    "team": player.team,
                    "player_id": player.id,
                    "move": [self.get_catch_power_direct(player, used_power)]
                })
            return action

    def get_my_player_num(self):
        num = 0
        for k, value in mPlayers.iteritems():
            if True == value.visibile and False == value.sleep:
                num += 1
        return num

    def get_bug_move(self):
        action = []
        for k, player in mPlayers.iteritems():
            go_x, go_y = player.bug_move[player.bug_num % 6]
            if player.target == None or (player.x == player.target[0] and player.y == player.target[1]):
                player.target = (go_x, go_y)
                player.bug_num += 1

            move = mLegStart.get_short_move(
                player.x, player.y, player.target[0], player.target[1])
            if move == None:
                move = ""
            action.append({
                "team": player.team,
                "player_id": player.id,
                "move": [move]
            })
        return action

    def excute(self, mRoundObj):
        return self.get_bug_move()
        self.mRoundObj = mRoundObj

        my_player_num = self.get_my_player_num()
        action = []

        # 如果我的鱼没有四条，我就去吃金币；否则我就去抓鱼
        if my_player_num < 4:
            mLogger.info("[round: {}] 抓鱼人手不够".format(
                self.mRoundObj.msg['msg_data']['round_id']))
            action = self.catch_power()
        else:
            action = self.catch_fish()
        return action


mDoThink = DoThink()
