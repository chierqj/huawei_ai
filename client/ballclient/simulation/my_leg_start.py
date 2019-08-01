# coding: utf-8

from ballclient.utils.logger import mLogger
import json
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config


class LegStart(object):
    def __init__(self):
        self.msg = ""
        self.short_path = dict()
        self.short_move = dict()
        self.wormhole = dict()
        self.tunnel_go = dict()
        self.graph = []    # 空地: '.',  障碍物: '#', 虫洞: '字母', 传送带: '<>^|'
        self.direction = ['down', 'up', 'right', 'left']
        self.tol_cells = 0
        self.fa = []

    def update_short_path_dict(self, key1, key2, value):
        if key1 in self.short_path:
            self.short_path[key1].update({key2: value})
        else:
            self.short_path.update({key1: {key2: value}})

    def update_short_move_dict(self, key1, key2, value):
        if key1 in self.short_move:
            self.short_move[key1].update({key2: value})
        else:
            self.short_move.update({key1: {key2: value}})

    def init_tunnel_go(self):
        for tunnel in self.msg['msg_data']['map']['tunnel']:
            px, py = tunnel['x'], tunnel['y']
            u = self.get_cell_id(px, py)
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
            self.tunnel_go[u] = self.get_cell_id(px, py)

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
        if pid1 in self.short_path:
            ret = self.short_path[pid1].get(pid2, None)
            return ret
        else:
            return None

    def get_short_move(self, x1, y1, x2, y2):
        if self.out_graph_border(x1, y1):
            return None
        if self.out_graph_border(x2, y2):
            return None

        pid1 = self.get_cell_id(x1, y1)
        pid2 = self.get_cell_id(x2, y2)

        if pid1 in self.short_move:
            ret = self.short_move[pid1].get(pid2, None)
            return ret
        else:
            return None

    def initialize_msg(self, msg):
        self.msg = msg

    @msimulog("LegStart")
    def excute(self, msg):
        self.initialize_msg(msg)
        width = self.msg['msg_data']['map']['width']
        height = self.msg['msg_data']['map']['height']
        self.tol_cells = width * height
        self.initialize_graph(width, height)
        self.create_graph()
        self.init_tunnel_go()
        for st in range(self.tol_cells):
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
        ret = self.get_cell_id(self.wormhole[nalp][0], self.wormhole[nalp][1])
        return ret

    def do_tunnel(self, u):
        ret = self.tunnel_go.get(u, None)
        if None == ret:
            x, y = self.get_x_y(u)
            mLogger.error("self.tunnel_go is None ({}, {})".format(x, y))
        return ret

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

    def get_fa(self, x):
        if self.fa[x] == x:
            return x
        else:
            ret = self.get_fa(self.fa[x])
            self.fa[x] = ret
            return ret

    def bfs(self, st, width, height):
        import Queue

        q = Queue.Queue()
        pre = [-1 for _ in range(self.tol_cells)]
        self.fa = [i for i in range(self.tol_cells)]
        move_act = dict()
        vis = [False for _ in range(self.tol_cells)]

        q.put((st, 0))
        vis[st] = True

        while False == q.empty():
            uid, step = q.get()

            if config.limit_path_length != -1 and step >= config.limit_path_length:
                continue

            dirs = self.get_dirs(uid)
            for mv, nx, ny in dirs:
                if False == self.match_border(nx, ny):
                    continue
                cell = self.get_graph_cell(nx, ny)
                n_cell_id = self.get_cell_id(nx, ny)
                if cell.isalpha():
                    n_cell_id = self.do_wormhoe(cell)
                elif self.match_tunnel(cell):
                    n_cell_id = self.do_tunnel(n_cell_id)
                if True == vis[n_cell_id]:
                    continue
                if uid == st:
                    move_act[n_cell_id] = mv
                else:
                    self.fa[self.get_fa(n_cell_id)] = self.get_fa(uid)

                vis[n_cell_id] = True
                pre[n_cell_id] = uid
                q.put((n_cell_id, step + 1))

        for key in move_act:
            value = move_act[key]
            fa = self.get_fa(key)
            move_act[fa] = value
        for ed in range(self.tol_cells):
            if self.match_bfs(ed) and ed != st:
                fa = self.get_fa(ed)
                mv = move_act.get(fa, None)
                if mv != None:
                    self.update_short_move_dict(st, ed, self.direction[mv])

        if True == config.need_short_path:
            for ed in range(self.tol_cells):
                tmp, path = ed, []
                while tmp != -1:
                    path.append(self.get_x_y(tmp))
                    tmp = pre[tmp]
                path = path[::-1]
                self.update_short_path_dict(st, ed, path)

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
