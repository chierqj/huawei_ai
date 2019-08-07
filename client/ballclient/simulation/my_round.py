# coding: utf-8
from ballclient.auth import config
from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog

from ballclient.simulation.do_beat import mDoBeat
from ballclient.simulation.do_think import mDoThink
from ballclient.simulation.my_player import mPlayers, othPlayers


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

    # 检查wormhole是否存在，True表示存在
    def check_wormhole(self):
        return "wormhole" in mLegStart.msg["msg_data"]["map"]

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

    # 根据move改变坐标
    def go_next(self, x, y, move):
        if move == 'up':
            return x, y - 1
        if move == 'down':
            return x, y + 1
        if move == 'left':
            return x - 1, y
        if move == 'right':
            return x + 1, y

    # x, y这个点在向move这方向移动后，真正的坐标是哪里，有虫洞或者传送带
    def real_go_point(self, x, y, move):
        go_x, go_y = self.go_next(x, y, move)
        if False == self.match_border(go_x, go_y):
            return None, None
        if True == self.match_meteor(go_x, go_y):
            return None, None
        go_cell = mLegStart.get_graph_cell(go_x, go_y)
        if mLegStart.match_tunnel(go_cell):
            go_cell_id = mLegStart.get_cell_id(go_x, go_y)
            go_x, go_y = mLegStart.get_x_y(mLegStart.do_tunnel(go_cell_id))
        if go_cell.isalpha():
            go_x, go_y = mLegStart.get_x_y(mLegStart.do_wormhoe(go_cell))
        return go_x, go_y

    # 获取action准备动作，先对所有鱼求最短路。然后根据模式不同执行不同的策略。
    def make_action(self):
        # 检查用的变量是否存在
        self.result["msg_data"]["round_id"] = self.msg['msg_data'].get(
            'round_id', None)
        if False == self.check_players():
            return

        # 遍历players，获取自己的鱼和对方的鱼
        players = self.msg['msg_data'].get('players', [])
        for player in players:
            if player.get("team", -1) == config.team_id:
                mPlayers[player['id']].assign(
                    player['score'], player['sleep'], player['x'], player['y'])
            else:
                othPlayers[player['id']].assign(
                    player['score'], player['sleep'], player['x'], player['y'])
        # 调用函数获取action
        action = []
        if self.msg['msg_data']['mode'] == "beat":
            action = mDoBeat.excute(self)
        else:
            # action = mDoBeat.excute(self)
            action = mDoThink.excute(self)

        self.result['msg_data']['actions'] = action

    # 初始化赋值msg消息
    def initialize_msg(self, msg):
        self.msg = msg
        for k, value in mPlayers.iteritems():
            value.initialize()
        for k, value in othPlayers.iteritems():
            value.initialize()

    # 程序入口
    def excute(self, msg):
        self.initialize_msg(msg)
        self.make_action()


mRound = Round()
