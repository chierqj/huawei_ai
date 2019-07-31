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
import random


class Round(object):
    def __init__(self):
        self.msg = ""
        self.result = ""

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        self.make_action()

    def get_result(self):
        return self.result

    def get_dis(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    def get_move(self, px, py):
        direction = {1: 'up', 3: 'down', 2: 'left', 4: 'right'}
        move = [direction[random.randint(1, 12317) % 4 + 1]]

        powers = self.msg["msg_data"].get("power", None)

        if None == powers:
            return move
        powers = sorted(powers, key=lambda it: self.get_dis(
            it['x'], it['y'], px, py))
        min_x, min_y = powers[0]['x'], powers[0]['y']

        if px < min_x:
            move = ['right']
        elif px > min_x:
            move = ['left']
        elif py < min_y:
            move = ['down']
        elif py > min_y:
            move = ['up']
        else:
            move = ['']

        return move

    def make_action(self):
        round_id = self.msg['msg_data'].get('round_id', None)
        self.result = {
            "msg_name": "action",
            "msg_data": {
                "round_id": round_id
            }
        }

        players = self.msg['msg_data'].get('players', None)
        if players == None:
            self.result['msg_data']['actions'] = []
            return

        action = []
        for player in players:
            team_id = player.get("team", None)
            if team_id == config.team_id:
                move = self.get_move(player['x'], player['y'])
                action.append({
                    "team": player['team'],
                    "player_id": player['id'],
                    "move": move
                })
        self.result['msg_data']['actions'] = action


mRound = Round()
