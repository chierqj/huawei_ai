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
        self.power_set = dict()
        self.neighbar_power = None
        self.mode = None
        self.last_remain_life = None

    def init(self):
        self.power_set.clear()
        self.neighbar_power = None
        self.mode = None

    # 暴露给service使用的，获取最终结果
    def get_result(self):
        return self.result

    '''
    初始化+更新状态操作
    1. 初始化消息
    2. 更新players状态
    3. 更新矿点信息，包括矿点自身信息以及地图累加矿点
    4. 刷新完之后做一些工作
    '''

    # 初始化赋值msg消息;更新fish和power集合
    def initialize_msg(self, msg):
        self.msg = msg
        if self.neighbar_power == None:
            self.neighbar_power = [
                [0] * mLegStart.width for _ in range(mLegStart.height)]
        if self.mode == None or self.mode != self.msg['msg_data']['mode']:
            self.power_set.clear()
        self.mode = self.msg['msg_data']['mode']

    # 更新一下所有玩家的状态
    def update_players(self):
        for k, player in mPlayers.iteritems():
            player.sleep = True
            player.visiable = False
            player.lost_vision_num += 1
        for k, player in othPlayers.iteritems():
            player.sleep = True
            player.visiable = False
            player.lost_vision_num += 1

        players = self.msg['msg_data'].get('players', [])
        for player in players:
            team_id = player.get("team", -1)
            pid = player.get("id", -1)
            if team_id == config.team_id:
                mPlayers[pid].x = player['x']
                mPlayers[pid].y = player['y']
                mPlayers[pid].sleep = (False if player['sleep'] == 0 else True)
                mPlayers[pid].visiable = True
                mPlayers[pid].score = player['score']
                mPlayers[pid].lost_vision_num = 0
            else:
                othPlayers[pid].x = player['x']
                othPlayers[pid].y = player['y']
                othPlayers[pid].sleep = (
                    False if player['sleep'] == 0 else True)
                othPlayers[pid].visiable = True
                othPlayers[pid].score = player['score']
                othPlayers[pid].lost_vision_num = 0

    # 更新一下能量的状态
    def update_power_set(self):
        for k, v in self.power_set.iteritems():
            v.lost_vision_num += 1
            v.visiable = False
        powers = self.msg['msg_data'].get("power", [])
        for power in powers:
            cell_id = mLegStart.get_cell_id(power['x'], power['y'])
            if cell_id in self.power_set:
                self.power_set[cell_id].x = power['x']
                self.power_set[cell_id].y = power['y']
                self.power_set[cell_id].lost_vision_num = 0
                self.power_set[cell_id].visiable = True
                self.power_set[cell_id].point = power['point']
            else:
                self.power_set[cell_id] = Power(
                    x=power['x'],
                    y=power['y'],
                    point=power['point'],
                    visiable=True,
                    lost_vision_num=0
                )

                width = mLegStart.width
                height = mLegStart.height
                vision = mLegStart.msg['msg_data']['map']['vision']
                x1, y1 = max(0, power['x'] -
                             vision), max(0, power['y'] - vision)
                x2, y2 = min(
                    width - 1, power['x'] + vision), min(height - 1, power['y'] + vision)
                for i in range(x1, x2 + 1):
                    for j in range(y1, y2 + 1):
                        self.neighbar_power[i][j] += power['point']

    # 更新一下每个鱼访问过的点
    def do_after_updated(self):
        remain_life = 0
        for team in self.msg['msg_data']['teams']:
            if team['id'] == config.team_id:
                remain_life = team['remain_life']
        if self.last_remain_life == None:
            self.last_remain_life = remain_life

        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                if self.last_remain_life <= 0:
                    continue
                mLogger.warning(">睡眠，被吃了< [fish: {}; point: ({}, {}); move: {}]".format(
                    player.id, player.x, player.y, player.move))

                eated_info = mLegEnd.eated_info.get(player.id, dict())
                eated_info = {
                    'count': eated_info.get('count', 0) + 1,
                    'score': eated_info.get('score', 0) + 10 + player.score
                }
                mLegEnd.eated_info[player.id] = eated_info

    # 获取action准备动作，先对所有鱼求最短路。然后根据模式不同执行不同的策略。
    def make_action(self):
        # 检查用的变量是否存在
        self.result["msg_data"]["round_id"] = self.msg['msg_data'].get(
            'round_id', None)

        # 调用函数获取action
        action = []
        if self.mode != mLegStart.my_team_force:
            action = mDoBeat.excute(self)
        else:
            action = mDoThink.excute(self)

        self.result['msg_data']['actions'] = action

    # 打印日志
    def print_log(self):
        round_id = self.msg['msg_data']['round_id']
        mLogger.info(
            "\n\n-------------------------[round: {}]-------------------------\n".format(round_id))

    '''
    程序入口流程
    1. 初始化msg消息
    2. 打印round_id
    3. 更新players状态
    4. 更新powers状态
    5. 做一些刷新完状态之后的工作
    6. 开始这一回合的round
    '''

    # 程序入口
    def excute(self, msg):
        self.initialize_msg(msg)
        self.print_log()
        self.update_players()
        self.update_power_set()
        self.do_after_updated()
        self.make_action()


mRound = Round()
