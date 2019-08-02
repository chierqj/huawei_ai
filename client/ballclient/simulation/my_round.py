# coding: utf-8
from ballclient.auth import config
from ballclient.simulation.my_leg_start import mLegStart
import random
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog


class Round(object):
    def __init__(self):
        self.msg = ""
        self.result = {
            "msg_name": "action",
            "msg_data": {
                "round_id": None,
                "actions": []
            }
        }
        self.direction = {1: 'right', 2: 'up', 3: 'left', 4: 'down'}
        self.beat = []

    # 暴露给service使用的，获取最终结果
    def get_result(self):
        return self.result

    # 检查players是否存在，True表示存在
    def check_players(self):
        return "players" in self.msg["msg_data"]

    # 检查teamid是否存在player，True表示存在
    def check_team(self, player):
        return "team" in player

    # 检查power是否存在，True表示存在
    def check_power(self):
        return "power" in self.msg["msg_data"]

    # 判断边界，True表示在边界内
    def match_border(self, x, y):
        if x < 0 or x >= mLegStart.msg['msg_data']['map']['width']:
            return False
        if y < 0 or y >= mLegStart.msg['msg_data']['map']['height']:
            return False
        return True

    # 判断是否为陨石，True表示为陨石，不能走
    def match_meteor(self, px, py):
        if mLegStart.get_graph_cell(px, py) == '#':
            return True
        return False

    # 判断当前是什么回合，分情况对player开始move
    def get_move(self, player):
        if self.msg['msg_data']['mode'] == "beat":
            ret = mDoBeat.excute(player)
            return [ret]
        else:
            ret = mDoThink.excute(player)
            return [ret]

    # 获取action准备动作，检查变量是否存在，对每一个player开始调度
    def make_action(self):
        self.result["msg_data"]["round_id"] = self.msg['msg_data'].get(
            'round_id', None)
        if False == self.check_players():
            return

        players = self.msg['msg_data'].get('players', [])
        action = []
        for player in players:
            if False == self.check_team(player):
                continue
            team_id = player.get("team", -1)
            if team_id == config.team_id:
                move = self.get_move(player)
                if move == []:
                    mLogger.warning("players 移动为空")
                action.append({
                    "team": player['team'],
                    "player_id": player['id'],
                    "move": move
                })
        self.result['msg_data']['actions'] = action

    # 初始化赋值msg消息
    def initialize_msg(self, msg):
        self.msg = msg

    # 程序入口
    def excute(self, msg):
        self.initialize_msg(msg)
        self.make_action()


mRound = Round()


class DoBeat():
    def __init__(self):
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

    # 判断物理上能不能走到这个位置，不超边界，不是障碍物
    def judge_physical(self, px, py):
        if False == mRound.match_border(px, py):
            return False
        if True == mRound.match_meteor(px, py):
            return False
        return True

    # 判断px, py这个位置能不能被吃，True表示能被吃
    def match_beat_eated(self, px, py):
        for player in mRound.msg['msg_data']['players']:
            if player['team'] != config.team_id:
                for x, y in self.dinger_dirs:
                    nx, ny = player['x'] + x, player['y'] + y
                    if nx == px and ny == py:
                        return True
        return False

    # 根据move改变坐标
    def go_next(self, x, y, cell):
        if cell == 'up':
            return x, y - 1
        if cell == 'down':
            return x, y + 1
        if cell == 'left':
            return x - 1, y
        if cell == 'right':
            return x + 1, y

    # 因为能看到金币，但是最短路吃不到。所以尝试物理上向金币靠近
    def physics_go(self, x1, y1, x2, y2):
        if x1 < x2 and self.judge_physical(x1 + 1, y1):
            return "right"
        if x1 > x2 and self.judge_physical(x1 - 1, y1):
            return "left"
        if y1 < y2 and self.judge_physical(x1, y1 + 1):
            return "down"
        if y1 > y2 and self.judge_physical(x1, y1 - 1):
            return "up"
        return None

    # 获取最近的金币移动方向
    def find_nearst_power(self):
        min_dis, result = 12317, None
        px, py = self.mPlayer['x'], self.mPlayer['y']
        for it in mRound.msg['msg_data']['power']:
            x, y = it['x'], it['y']
            dis = self.get_dis(x, y, px, py)
            if dis < min_dis:
                # 查表获取我到金币之间的移动方向
                mv = mLegStart.get_short_move(px, py, x, y)
                if mv != None:
                    # 我走一步到哪了，我是px, py
                    nx, ny = self.go_next(px, py, mv)
                    if False == self.match_beat_eated(nx, ny):
                        min_dis, result = dis, mv
        return result

    # 获取最近的虫洞移动方向
    def find_nearst_worm_hole(self):
        min_dis, result = 12317, None
        px, py = self.mPlayer['x'], self.mPlayer['y']
        for it in mLegStart.msg['msg_data']['map']['wormhole']:
            x, y = it['x'], it['y']
            dis = self.get_dis(x, y, px, py)
            if dis <= min_dis:
                # 查表获取我到虫洞之间的移动方向
                mv = mLegStart.get_short_move(px, py, x, y)
                if mv != None:
                    # 我走一步到哪了，我是px, py
                    nx, ny = self.go_next(px, py, mv)
                    if False == self.match_beat_eated(nx, ny):
                        min_dis, result = dis, mv
        return result

    # 能不能随机游走，True表示能
    def judge_random_walk(self, px, py):
        # 物理上走不了，返回False
        if False == self.judge_physical(px, py):
            return False
        # 看看会不会被吃，True表示被吃了，不能走
        if True == self.match_beat_eated(px, py):
            return False
        return True

    # 开始随机游走
    def random_walk(self):
        # 随机游走之前，先去找虫洞。
        dirs = [('up', 0, -1), ('down', 0, 1),
                ('left', -1, 0), ('right', 1, 0)]
        for mv, x, y in dirs:
            if self.judge_random_walk(self.mPlayer['x'] + x, self.mPlayer['y'] + y):
                return mv
        self.record_detial("None", "躲不过去")
        return mRound.direction[random.randint(1, 12317) % 4 + 1]

    def record_detial(self, move, text):
        if False == config.record_detial or None == move:
            return
        round_id = mRound.msg['msg_data']['round_id']
        player_id = self.mPlayer['id']
        mLogger.info('[round: {}, fish: {}, from: ({}, {}), move: {}] {}'.format(
            round_id, player_id, self.mPlayer['x'], self.mPlayer['y'], move, text))

    # 获取下一步的移动方向；
    def get_direct(self):
        # 有金币，找最近的金币并且不被追到
        if True == mRound.check_power():
            ret = self.find_nearst_power()
            self.record_detial(ret, "找到金币")
        # 没有金币，尝试去找虫洞
        else:
            ret = self.find_nearst_worm_hole()
            self.record_detial(ret, "找到虫洞")
        # 以上两种情况都失败了，说明P都没有，或者贼危险，容易被吃，开始随机游走
        if None == ret:
            ret = self.random_walk()
            self.record_detial(ret, "随机游走")
        return ret

    def excute(self, player):
        self.mPlayer = player
        return self.get_direct()


mDoBeat = DoBeat()


class DoThink():
    def __init__(self):
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

    # 判断物理上能不能走到这个位置，不超边界，不是障碍物
    def judge_physical(self, px, py):
        if False == mRound.match_border(px, py):
            return False
        if True == mRound.match_meteor(px, py):
            return False
        return True

    # 判断px, py这个位置能不能被吃，True表示能被吃；Think回合，我最大
    def match_beat_eated(self, px, py):
        return False
        for player in mRound.msg['msg_data']['players']:
            if player['team'] != config.team_id:
                for x, y in self.dinger_dirs:
                    nx, ny = player['x'] + x, player['y'] + y
                    if nx == px and ny == py:
                        return True
        return False

    # 根据move改变坐标
    def go_next(self, x, y, cell):
        if cell == 'up':
            return x, y - 1
        if cell == 'down':
            return x, y + 1
        if cell == 'left':
            return x - 1, y
        if cell == 'right':
            return x + 1, y

    # 获取最近的金币移动方向
    def find_nearst_power(self):
        min_dis, result = 12317, None
        px, py = self.mPlayer['x'], self.mPlayer['y']
        for it in mRound.msg['msg_data']['power']:
            x, y = it['x'], it['y']
            dis = self.get_dis(x, y, px, py)
            if dis < min_dis:
                # 查表获取我到金币之间的移动方向
                mv = mLegStart.get_short_move(px, py, x, y)
                if mv != None:
                    # 我走一步到哪了，我是px, py
                    nx, ny = self.go_next(px, py, mv)
                    if False == self.match_beat_eated(nx, ny):
                        min_dis, result = dis, mv
        return result

    # 获取最近的虫洞移动方向
    def find_nearst_worm_hole(self):
        min_dis, result = 12317, None
        px, py = self.mPlayer['x'], self.mPlayer['y']
        for it in mLegStart.msg['msg_data']['map']['wormhole']:
            x, y = it['x'], it['y']
            dis = self.get_dis(x, y, px, py)
            if dis <= min_dis:
                # 查表获取我到虫洞之间的移动方向
                mv = mLegStart.get_short_move(px, py, x, y)
                if mv != None:
                    # 我走一步到哪了，我是px, py
                    nx, ny = self.go_next(px, py, mv)
                    if False == self.match_beat_eated(nx, ny):
                        min_dis, result = dis, mv
        return result

    # 能不能随机游走，True表示能
    def judge_random_walk(self, px, py):
        # 物理上走不了，返回False
        if False == self.judge_physical(px, py):
            return False
        # 看看会不会被吃，True表示被吃了，不能走
        if True == self.match_beat_eated(px, py):
            return False
        return True

    # 开始随机游走
    def random_walk(self):
        dirs = [('up', 0, -1), ('down', 0, 1),
                ('left', -1, 0), ('right', 1, 0)]
        for mv, x, y in dirs:
            if self.judge_random_walk(self.mPlayer['x'] + x, self.mPlayer['y'] + y):
                return mv
        return mRound.direction[random.randint(1, 12317) % 4 + 1]

    def record_detial(self, move, text):
        if False == config.record_detial or None == move:
            return
        round_id = mRound.msg['msg_data']['round_id']
        player_id = self.mPlayer['id']
        mLogger.info('[round: {}, fish: {}, from: ({}, {}), move: {}] {}'.format(
            round_id, player_id, self.mPlayer['x'], self.mPlayer['y'], move, text))

    # 获取下一步的移动方向；
    def get_direct(self):

        # 有金币，找最近的金币并且不被追到
        if True == mRound.check_power():
            ret = self.find_nearst_power()
            self.record_detial(ret, "找到金币")
        # 没有金币，尝试去找虫洞
        else:
            ret = self.find_nearst_worm_hole()
            self.record_detial(ret, "找到虫洞")
        # 以上两种情况都失败了，说明P都没有，或者贼危险，容易被吃，开始随机游走
        if None == ret:
            ret = self.random_walk()
            self.record_detial(ret, "随机游走")
        return ret

    def excute(self, player):
        self.mPlayer = player
        return self.get_direct()


mDoThink = DoThink()
