# coding: utf-8

'''
:param msg: dict
:return:
return type: dict


round_id = msg['msg_data']['round_id']
players = msg['msg_data']['players']
direction = {1: 'up', 2: 'down', 3: 'left', 4: 'right'}
result = {
    "msg_name": "action",
    "msg_data": {
        "round_id": round_id
    }
}
action = []
for player in players:
    if player['team'] == constants.team_id:
        action.append({"team": player['team'], "player_id": player['id'],
                       "move": [direction[random.randint(1, 4)]]})
return result
'''
from ballclient.auth import config
from ballclient.simulation.my_leg_start import mLegStart
import random


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

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        self.make_action()

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

    def run(self, px, py):
        move = ['']
        for i in range(0, 3):
            if self.judge(px + self.add[i][0], py + self.add[i][1]) == True:
                move = [self.direction[i + 1]]
                return move
        return move

    def get_random_dir(self):
        return [self.direction[random.randint(1, 12317) % 4 + 1]]

    def get_move(self, px, py):
        move = ['']
        if False == self.check_power():
            # 没有power:1.找传送门 2.找鱼 3.跑路
            move = self.run(px, py)  # 跑路
            return move
        powers = self.msg["msg_data"].get("power", [])
        powers = sorted(powers, key=lambda it: self.get_dis(
            it['x'], it['y'], px, py))
        min_x, min_y = powers[0]['x'], powers[0]['y']

        if px < min_x and self.judge(px + 1, py):
            move = ['right']
        elif px > min_x and self.judge(px - 1, py):
            move = ['left']
        elif py < min_y and self.judge(px, py + 1):
            move = ['down']
        elif py > min_y and self.judge(px, py - 1):
            move = ['up']
        else:
            # 吃鱼or跑路
            move = [self.direction[random.randint(1, 6772317) % 4 + 1]]
            # move = self.run(px, py)
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


mRound = Round()
