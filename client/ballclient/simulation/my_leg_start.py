# coding: utf-8

'''
:param msg:
:return: None

print "msg_name:%s" % msg['msg_name']
print "map_width:%s" % msg['msg_data']['map']['width']
print "map_height:%s" % msg['msg_data']['map']['height']
print "vision:%s" % msg['msg_data']['map']['vision']
print "meteor:%s" % msg['msg_data']['map']['meteor']
# print "cloud:%s" % msg['msg_data']['map']['cloud']
print "tunnel:%s" % msg['msg_data']['map']['tunnel']
print "wormhole:%s" % msg['msg_data']['map']['wormhole']
print "teams:%s" % msg['msg_data']['teams']
'''
from ballclient.logger import mLogger
import json

# msg = {u'msg_name': u'leg_start', u'msg_data': {u'map': {u'wormhole': [{u'y': 0, u'x': 19, u'name': u'A'}, {u'y': 6, u'x': 13, u'name': u'b'}, {u'y': 13, u'x': 6, u'name': u'a'}, {u'y': 19, u'x': 0, u'name': u'B'}], u'tunnel': [{u'y': 5, u'x': 5, u'direction': u'up'}, {u'y': 5, u'x': 6, u'direction': u'right'}, {u'y': 5, u'x': 7, u'direction': u'right'}, {u'y': 5, u'x': 8, u'direction': u'right'}, {u'y': 5, u'x': 9, u'direction': u'right'}, {u'y': 5, u'x': 10, u'direction': u'right'}, {u'y': 5, u'x': 11, u'direction': u'right'}, {u'y': 5, u'x': 12, u'direction': u'right'}, {u'y': 5, u'x': 13, u'direction': u'right'}, {u'y': 5, u'x': 14, u'direction': u'right'}, {u'y': 6, u'x': 5, u'direction': u'up'}, {u'y': 6, u'x': 14, u'direction': u'down'}, {u'y': 7, u'x': 5, u'direction': u'up'}, {u'y': 7, u'x': 14, u'direction': u'down'}, {u'y': 8, u'x': 5, u'direction': u'up'}, {u'y': 8, u'x': 14, u'direction': u'down'}, {u'y': 9, u'x': 5, u'direction': u'up'}, {u'y': 9, u'x': 14, u'direction': u'down'}, {u'y': 10, u'x': 5, u'direction': u'up'}, {u'y': 10, u'x': 14, u'direction': u'down'}, {u'y': 11, u'x': 5, u'direction': u'up'}, {u'y': 11, u'x': 14, u'direction': u'down'}, {u'y': 12, u'x': 5, u'direction': u'up'}, {
#     u'y': 12, u'x': 14, u'direction': u'down'}, {u'y': 13, u'x': 5, u'direction': u'up'}, {u'y': 13, u'x': 14, u'direction': u'down'}, {u'y': 14, u'x': 5, u'direction': u'left'}, {u'y': 14, u'x': 6, u'direction': u'left'}, {u'y': 14, u'x': 7, u'direction': u'left'}, {u'y': 14, u'x': 8, u'direction': u'left'}, {u'y': 14, u'x': 9, u'direction': u'left'}, {u'y': 14, u'x': 10, u'direction': u'left'}, {u'y': 14, u'x': 11, u'direction': u'left'}, {u'y': 14, u'x': 12, u'direction': u'left'}, {u'y': 14, u'x': 13, u'direction': u'left'}, {u'y': 14, u'x': 14, u'direction': u'down'}], u'height': 20, u'width': 20, u'meteor': [{u'y': 1, u'x': 18}, {u'y': 1, u'x': 19}, {u'y': 4, u'x': 7}, {u'y': 4, u'x': 8}, {u'y': 4, u'x': 11}, {u'y': 4, u'x': 12}, {u'y': 7, u'x': 4}, {u'y': 7, u'x': 15}, {u'y': 8, u'x': 4}, {u'y': 8, u'x': 15}, {u'y': 11, u'x': 4}, {u'y': 11, u'x': 15}, {u'y': 12, u'x': 4}, {u'y': 12, u'x': 15}, {u'y': 15, u'x': 7}, {u'y': 15, u'x': 8}, {u'y': 15, u'x': 11}, {u'y': 15, u'x': 12}, {u'y': 18, u'x': 0}, {u'y': 18, u'x': 1}], u'vision': 3}, u'teams': [{u'players': [0, 1, 2, 3], u'force': u'beat', u'id': 1111}, {u'players': [4, 5, 6, 7], u'force': u'think', u'id': 6666}]}}


class LegStart(object):
    def __init__(self):
        self.msg = ""
        self.short_path = []
        self.short_move = []
        self.wormhole = dict()
        self.graph = []
        self.directions = ['down', 'up', 'right', 'left']

    def out_graph_border(self, x, y):
        if x < 0 or x >= self.msg['msg_data']['map']['width']:
            return True
        if y < 0 or y >= self.msg['msg_data']['map']['height']:
            return True
        return False

    def get_short_path(self, x1, y1, x2, y2):
        if self.out_graph_border(x1, y1):
            return None
        if self.out_graph_border(x2, y2):
            return None

        pid1 = self.get_cell_id(x1, y1)
        pid2 = self.get_cell_id(x2, y2)
        if self.short_path[pid1][pid2] == [] or self.short_path[pid1][pid2] == -1:
            return None
        return self.short_path[pid1][pid2]

    def get_short_move(self, x1, y1, x2, y2):
        if self.out_graph_border(x1, y1):
            return None
        if self.out_graph_border(x2, y2):
            return None

        pid1 = self.get_cell_id(x1, y1)
        pid2 = self.get_cell_id(x2, y2)
        if self.short_move[pid1][pid2] == -1:
            return None
        return self.directions[self.short_move[pid1][pid2]]

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        width = self.msg['msg_data']['map']['width']
        height = self.msg['msg_data']['map']['height']
        self.initialize_graph(width, height)
        self.create_graph()

        for st in range(width * height):
            if self.match_bfs(st):
                self.bfs(st, width, height)

    def match_bfs(self, st):
        x, y = self.get_x_y(st)
        cell = self.get_graph_cell(x, y)
        if cell == '.' or cell.isalpha():
            return True
        return False

    def print_graph(self):
        print(" "),
        for i in range(20):
            print i, "\t",
        print
        for i, row in enumerate(self.graph):
            print i, "\t".join(row)

    def get_x_y(self, pid):
        x = int(pid / self.msg['msg_data']['map']['width'])
        y = pid % self.msg['msg_data']['map']['width']
        return x, y

    def match_border(self, x, y):
        if self.out_graph_border(x, y):
            return False
        if self.get_graph_cell(x, y) == '#':
            return False
        return True

    def match_tunnel(self, c):
        if c == '>' or c == '<' or c == '^' or c == '|':
            return True
        return False

    def do_wormhoe(self, alp):
        nalp = alp.lower() if alp.isupper() else alp.upper()
        return self.wormhole[nalp]

    def do_tunnel(self, px, py):
        while True:
            cell = self.get_graph_cell(px, py)
            if False == self.match_tunnel(cell):
                break
            if cell == '>':
                px += 1
            if cell == '<':
                px -= 1
            if cell == '^':
                py -= 1
            if cell == '|':
                py += 1
        return px, py

    def get_cell_id(self, x, y):
        return x * self.msg['msg_data']['map']['width'] + y

    def get_dirs(self, pid):
        x, y = self.get_x_y(pid)
        dirs = []
        dirs.append((0, x, y + 1))
        dirs.append((1, x, y - 1))
        dirs.append((2, x + 1, y))
        dirs.append((3, x - 1, y))
        return dirs

    def get_graph_cell(self, px, py):
        return self.graph[py][px]

    def bfs(self, st, width, height):
        import Queue

        q = Queue.Queue()
        pre = [-1 for _ in range(width * height)]
        pre_move = [-1 for _ in range(width * height)]
        vis = [False for _ in range(width * height)]

        q.put(st)
        vis[st] = True

        while False == q.empty():
            uid = q.get()

            dirs = self.get_dirs(uid)
            for mv, nx, ny in dirs:
                if False == self.match_border(nx, ny):
                    continue
                cell = self.get_graph_cell(nx, ny)
                if cell.isalpha():
                    nx, ny = self.do_wormhoe(cell)
                elif self.match_tunnel(cell):
                    nx, ny = self.do_tunnel(nx, ny)
                cell_id = self.get_cell_id(nx, ny)
                if True == vis[cell_id]:
                    continue

                vis[cell_id] = True
                pre[cell_id] = uid
                pre_move[cell_id] = mv
                q.put(cell_id)

        for ed in range(width * height):
            tmp, path = ed, []
            while tmp != -1:
                path.append(self.get_x_y(tmp))
                tmp = pre[tmp]
            path = path[::-1]
            self.short_path[st][ed] = path
            if len(path) >= 2:
                nx, ny = path[1]
                cell = self.get_cell_id(nx, ny)
                self.short_move[st][ed] = pre_move[cell]
            # print(self.short_path[st][ed]),
            # print(self.short_move[st][ed])

    def get_tunnel_dir(self, s):
        if s == "down":
            return "|"
        elif s == "up":
            return "^"
        elif s == "left":
            return "<"
        elif s == 'right':
            return ">"
        else:
            return "-1"

    def initialize_graph(self, width, height):
        self.graph = [['.'] * width for _ in range(height)]
        tol = width * height
        self.short_path = [[-1] * tol for _ in range(tol)]
        self.short_move = [[-1] * tol for _ in range(tol)]

    def create_graph(self):
        for meteor in self.msg['msg_data']['map']['meteor']:
            self.graph[meteor['y']][meteor['x']] = '#'
        for tunnel in self.msg['msg_data']['map']['tunnel']:
            self.graph[tunnel['y']][tunnel['x']
                                    ] = self.get_tunnel_dir(tunnel["direction"])
        for wormhole in self.msg['msg_data']['map']['wormhole']:
            self.graph[wormhole['y']][wormhole['x']] = wormhole["name"]
            self.wormhole[wormhole['name']] = (wormhole['x'], wormhole['y'])


mLegStart = LegStart()
# mLegStart.excute(msg)
