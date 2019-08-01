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
        self.add = [[1, 0], [0, -1], [-1, 0], [0, 1], [0, 0]]
        self.direction = {1: 'right', 2: 'up', 3: 'left', 4: 'down'}
        self.beat = []

    def get_result(self):
        return self.result

    def check_players(self):
        return "players" in self.msg["msg_data"]

    def check_team(self, player):
        return "team" in player

    def check_power(self):
        return "power" in self.msg["msg_data"]

    def get_dis(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    def initialize_msg(self, msg):
        self.msg = msg

    def judge(self, px, py):
        if px < 0 or py < 0 or px >= mLegStart.msg['msg_data']['map']['width'] or py >= mLegStart.msg['msg_data']['map']['height']:
            return False
        for meteor in mLegStart.msg['msg_data']['map']['meteor']:
            if meteor['x'] == px and meteor['y'] == py:
                return False
        if self.msg['msg_data']['mode'] == "beat":
            for player in self.msg['msg_data']['players']:
                if player['team'] != config.team_id:
                    for xy in self.add:
                        if player['x'] + xy[0] == px and player['y'] + xy[1] == py:
                            return False
            return True
        else:
            return True

    def run(self, px, py, flag):
        move = ['']
        add = 0
        if flag == 1:
            add = random.randint(1, 12317) % 4
        for i in range(0, 3):
            k = (i + add) % 4
            dx, dy = px + self.add[k][0], py + self.add[k][1]
            if self.judge(dx, dy) == True:
                if move == ['']:
                    move = [self.direction[k + 1]]
                else:
                    for wormhole in mLegStart.msg['msg_data']['map']['wormhole']:
                        if wormhole['x'] == dx and wormhole['y'] == dy:
                            move = [self.direction[k + 1]]
        return move

    # powers代表可以吃的东西
    def get_direct(self, px, py, powers):
        min_x, min_y = -1, -1
        min_dis, min_dis2 = 961006, 961006
        # 我可以吃人，我去吃距离最小的鱼
        if self.msg['msg_data']['mode'] == "think":
            for player in self.msg['msg_data']['players']:
                if player['team'] != config.team_id:
                    dis = self.get_dis(px, py, player['x'], player['y'])
                    if min_dis > dis:
                        min_dis, min_x, min_y = dis, player['x'], player['y']
        if None == powers:
            if min_x == -1:
                return self.run(px, py, 1)
        else:
            powers = sorted(powers, key=lambda it: self.get_dis(
                it['x'], it['y'], px, py))
            # 离我最近的金币powers[0]， 距离min_dis2
            min_dis2 = self.get_dis(powers[0]['x'], powers[0]['y'], px, py)
        move = ['']
        if min_dis2 < 5:
            min_x, min_y = powers[0]['x'], powers[0]['y']
        else:
            return self.run(px, py, 1)
        short_move = mLegStart.get_short_move(px, py, min_x, min_y)

        if short_move == None:
            mLogger.info("cant find move from ({}, {}) to ({}, {})".format(
                px, py, min_x, min_y))
            move = self.run(px, py, 1)
        else:
            move = [short_move]
        return move
        # if px < min_x and self.judge(px + 1, py):
        #     move = ['right']
        # elif px > min_x and self.judge(px - 1, py):
        #     move = ['left']
        # elif py < min_y and self.judge(px, py + 1):
        #     move = ['down']
        # elif py > min_y and self.judge(px, py - 1):
        #     move = ['up']
        # else:
        #     move = self.run(px, py, 1)
        # return move

    def get_move(self, px, py):
        move = ['']
        powers = self.msg["msg_data"].get("power", None)
        move = self.get_direct(px, py, powers)
        return move

    def make_action(self):
        self.result["msg_data"]["round_id"] = self.msg['msg_data'].get(
            'round_id', None)
        if False == self.check_players:
            return

        players = self.msg['msg_data'].get('players', [])
        action = []
        for player in players:
            if False == self.check_team(player):
                continue
            team_id = player.get("team", -1)
            if team_id == config.team_id:
                move = self.get_move(player['x'], player['y'])
                action.append({
                    "team": player['team'],
                    "player_id": player['id'],
                    "move": move
                })
        self.result['msg_data']['actions'] = action

    def excute(self, msg):
        self.initialize_msg(msg)
        self.make_action()


mRound = Round()
