# coding: utf-8
from ballclient.auth import config
from ballclient.simulation.do_beat import mDoBeat
from ballclient.simulation.do_think import mDoThink
from ballclient.simulation.my_leg_start import mLegStart
from ballclient.simulation.my_player import Player, mPlayers, othPlayers
from ballclient.simulation.my_power import Power
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.simulation.my_leg_end import mLegEnd


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
        self.POWER_WAIT_SET = dict()
        self.neighbar_power = None
        self.my_alive_player_num = 0
        self.limit_dead_weight = -1.0

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
        if move == "":
            return x, y
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
        if mLegStart.match_wormhole(go_cell):
            go_x, go_y = mLegStart.get_x_y(mLegStart.do_wormhoe(go_cell))
        return go_x, go_y

    # 获取action准备动作，先对所有鱼求最短路。然后根据模式不同执行不同的策略。
    def make_action(self):
        # 检查用的变量是否存在
        self.result["msg_data"]["round_id"] = self.msg['msg_data'].get(
            'round_id', None)

        # 调用函数获取action
        action = []
        if self.msg['msg_data']['mode'] != mLegStart.my_team_force:
            action = mDoBeat.excute(self)
        else:
            # action = mDoBeat.excute(self)
            action = mDoThink.excute(self)

        self.result['msg_data']['actions'] = action

    # 初始化赋值msg消息;更新fish和power集合
    def initialize_msg(self, msg):
        self.msg = msg
        self.my_alive_player_num = 0

        if self.neighbar_power == None:
            width = mLegStart.msg['msg_data']['map']['width']
            height = mLegStart.msg['msg_data']['map']['height']
            self.neighbar_power = [[0] * width for _ in range(height)]

    # 更新players状态
    def initialize_players(self):
        for k, value in mPlayers.iteritems():
            value.initialize()
            value.update_last_appear()
        for k, value in othPlayers.iteritems():
            value.initialize()
            value.update_last_appear()

    # 看到能量的时候，给周围视野范围内的能量值都累加
    def add_neighbar_power(self, x, y, point):
        width = mLegStart.msg['msg_data']['map']['width']
        height = mLegStart.msg['msg_data']['map']['height']
        vision = mLegStart.msg['msg_data']['map']['vision']
        x1, y1 = max(0, x - vision), max(0, y - vision)
        x2, y2 = min(width - 1, x + vision), min(height - 1, y + vision)
        for i in range(x1, x2 + 1):
            for j in range(y1, y2 + 1):
                self.neighbar_power[i][j] += point

    # 更新一下所有玩家的状态
    def update_player_wait_set(self):
        if False == self.check_players():
            return
        players = self.msg['msg_data'].get('players', [])
        for player in players:
            team_id = player.get("team", -1)
            pid = player.get("id", -1)
            if team_id == config.team_id:
                mPlayers[pid].assign(
                    last_appear_dis=0,
                    score=player['score'],
                    sleep=(False if player['sleep'] == 0 else True),
                    x=player['x'],
                    y=player['y'],
                    visiable=True
                )
                self.my_alive_player_num += 1
            else:
                if pid in othPlayers:
                    othPlayers[pid].assign(
                        last_appear_dis=0,
                        score=player['score'],
                        sleep=(False if player['sleep'] == 0 else True),
                        x=player['x'],
                        y=player['y'],
                        visiable=True
                    )

    # 更新一下能量的状态
    def update_power_wait_set(self):
        for k, v in self.POWER_WAIT_SET.iteritems():
            v.update_last_appear()
        if False == self.check_power():
            return
        for power in self.msg['msg_data']['power']:
            cell_id = mLegStart.get_cell_id(power['x'], power['y'])
            if cell_id in self.POWER_WAIT_SET:
                self.POWER_WAIT_SET[cell_id].assign(
                    last_appear_dis=0,
                    x=power['x'],
                    y=power['y'],
                    point=power['point'],
                    visiable=True
                )
            else:
                self.POWER_WAIT_SET[cell_id] = Power(
                    last_appear_dis=0,
                    x=power['x'],
                    y=power['y'],
                    point=power['point'],
                    visiable=True
                )
                self.add_neighbar_power(power['x'], power['y'], power['point'])

    # 打印日志
    def print_log(self):
        round_id = self.msg['msg_data']['round_id']
        mLogger.info(
            "\n\n-------------------------[round: {}]-------------------------\n".format(round_id))

    # 更新一下每个鱼访问过的点
    def update_vis_set(self):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                player.vis_cell.clear()
                mLogger.warning(">睡眠，被吃了< [fish: {}; point: ({}, {}); move: {}; dead_weight: {}]".format(
                    player.id, player.x, player.y, player.move, player.dead_weight))
            else:
                cell_id = mLegStart.get_cell_id(player.x, player.y)
                player.vis_cell.add(cell_id)

    # 程序入口
    def excute(self, msg):
        self.initialize_msg(msg)
        self.print_log()
        self.initialize_players()
        self.update_player_wait_set()
        self.update_power_wait_set()
        self.update_vis_set()
        self.make_action()


mRound = Round()
