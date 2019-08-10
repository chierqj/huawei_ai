# coding: utf-8

from ballclient.utils.logger import mLogger
import json
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player


class LegStart(object):
    def __init__(self):
        self.msg = ""
        self.short_path = dict()
        self.short_move = dict()
        self.short_length = dict()
        self.wormhole = dict()
        self.tunnel_go = dict()
        self.graph = []    # 空地: '.',  障碍物: '#', 虫洞: '字母', 传送带: '<>^|'
        self.direction = ['down', 'up', 'right', 'left']
        self.tol_cells = 0
        self.fa = []
        self.cell_vis_cnt = dict()

    # 更新最短路径的二维字典，u-v的路径是个list
    def update_short_path_dict(self, key1, key2, value):
        if key1 in self.short_path:
            self.short_path[key1].update({key2: value})
        else:
            self.short_path.update({key1: {key2: value}})

    # 更新最短路径的移动方向的二维字典，u-v的移动是个string
    def update_short_move_dict(self, key1, key2, value):
        if key1 in self.short_move:
            self.short_move[key1].update({key2: value})
        else:
            self.short_move.update({key1: {key2: value}})

    # 更新最短路径的长度，u-v的长度是个int
    def update_short_length_dict(self, key1, key2, value):
        if key1 in self.short_length:
            self.short_length[key1].update({key2: value})
        else:
            self.short_length.update({key1: {key2: value}})

    # 判断x, y超出地图的范围了
    def out_graph_border(self, x, y):
        if x < 0 or x >= self.msg['msg_data']['map']['width']:
            return True
        if y < 0 or y >= self.msg['msg_data']['map']['height']:
            return True
        return False

    # 符不符合求最短路bfs的条件，必须是空地或者虫洞
    def match_bfs(self, st):
        x, y = self.get_x_y(st)
        cell = self.get_graph_cell(x, y)
        if cell == '.' or self.match_wormhole(cell):
            return True
        return False

    # 根据x, y坐标获取地图每个格子映射的id
    def get_cell_id(self, x, y):
        return x * self.msg['msg_data']['map']['width'] + y

    # 根于地图每个格子的映射的id获取x,y坐标
    def get_x_y(self, pid):
        x = int(pid / self.msg['msg_data']['map']['width'])
        y = pid % self.msg['msg_data']['map']['width']
        return x, y

    # 判断x, y点是不是物理上可以走。不超过边界 & 不是障碍物
    def match_border(self, x, y):
        if self.out_graph_border(x, y):
            return False
        if self.get_graph_cell(x, y) == '#':
            return False
        return True

    # 判断c是不是传送带
    def match_tunnel(self, c):
        if c == '>' or c == '<' or c == '^' or c == '|':
            return True
        return False

    # 判断c是不是虫洞
    def match_wormhole(self, c):
        if c.isalpha() and c.lower() in self.wormhole and c.upper() in self.wormhole:
            return True
        return False

    # 打印地图
    def print_graph(self):
        print(" "),
        for i in range(20):
            print i, "\t",
        print
        for i, row in enumerate(self.graph):
            print i, "\t".join(row)

    # 预处理所有的传送带
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

    # 虫洞的时候，返回对应另一个位置的映射id
    def do_wormhoe(self, alp):
        nalp = alp.lower() if alp.isupper() else alp.upper()
        ret = self.get_cell_id(self.wormhole[nalp][0], self.wormhole[nalp][1])
        return ret

    # 传送带的时候，返回u这个点直接会被传送到哪里
    def do_tunnel(self, u):
        ret = self.tunnel_go.get(u, None)
        if None == ret:
            x, y = self.get_x_y(u)
            mLogger.error("self.tunnel_go is None ({}, {})".format(x, y))
        return ret

    # 当前点pid向四个方向走，获取到的move, nx, ny；move用0,1,2,3表示
    def get_dirs(self, pid):
        x, y = self.get_x_y(pid)
        dirs = []
        dirs.append((0, x, y + 1))
        dirs.append((1, x, y - 1))
        dirs.append((2, x + 1, y))
        dirs.append((3, x - 1, y))
        return dirs

    # 因为定义横方向是x轴，因此获取px, py在地图上是什么的时候。必须用这个方法获取，否则就是反的
    def get_graph_cell(self, px, py):
        return self.graph[py][px]

    # 并查集获取集合标记id
    def get_fa(self, x):
        if self.fa[x] == x:
            return x
        else:
            ret = self.get_fa(self.fa[x])
            self.fa[x] = ret
            return ret

    # 单点最短路，顺带记录了start到它能到的其他点的最短路，不用每次都求
    def create_short_path(self, start_point):
        if start_point in self.short_length:
            return

        import Queue

        # bfs 需要变量
        q = Queue.Queue()
        vis = set()

        # 记录最短路径的第一步移动方向需要变量
        if True == config.need_short_move:
            move_act = dict()
            self.fa = [i for i in range(self.tol_cells)]

        # 记录最短路路径需要变量
        if True == config.need_short_path:
            pre = dict()
            pre[start_point] = -1

        # 队列添加第一个节点
        q.put((start_point, 0))
        vis.add(start_point)

        while False == q.empty():
            uid, step = q.get()
            TX, TY = self.get_x_y(uid)
            # mLogger.info("point: ({},{}); step: {}".format(TX, TY, step))
            self.update_short_length_dict(start_point, uid, step)
            dirs = self.get_dirs(uid)
            for mv, nx, ny in dirs:
                if False == self.match_border(nx, ny):
                    continue
                cell = self.get_graph_cell(nx, ny)
                n_cell_id = self.get_cell_id(nx, ny)
                if self.match_wormhole(cell):
                    n_cell_id = self.do_wormhoe(cell)
                elif self.match_tunnel(cell):
                    n_cell_id = self.do_tunnel(n_cell_id)
                if n_cell_id in vis:
                    continue

                vis.add(n_cell_id)
                q.put((n_cell_id, step + 1))

                if True == config.need_short_move:
                    if uid == start_point:
                        move_act[n_cell_id] = mv
                    else:
                        self.fa[self.get_fa(n_cell_id)] = self.get_fa(uid)

                if True == config.need_short_path:
                    pre[n_cell_id] = uid

        if True == config.need_short_move:
            for key in move_act:
                value = move_act[key]
                fa = self.get_fa(key)
                move_act[fa] = value
            for point in vis:
                if self.match_bfs(point) and point != start_point:
                    fa = self.get_fa(point)
                    mv = move_act.get(fa, None)
                    if mv != None:
                        self.update_short_move_dict(
                            start_point, point, self.direction[mv])

        if True == config.need_short_path:
            for point in vis:
                tmp, path = point, []
                while tmp != -1:
                    path.append(self.get_x_y(tmp))
                    tmp = pre[tmp]
                path = path[::-1]
                self.update_short_path_dict(start_point, point, path)

    # 暴露给其它地方用的获取两个点之间的最短路径，再config配置中需要打开
    def get_short_path(self, x1, y1, x2, y2):
        if self.out_graph_border(x1, y1):
            return None
        if self.out_graph_border(x2, y2):
            return None

        pid1 = self.get_cell_id(x1, y1)
        pid2 = self.get_cell_id(x2, y2)
        result = None
        if pid1 in self.short_path:
            result = self.short_path[pid1].get(pid2, None)
        if None == result:
            self.create_short_path(pid1)

        if pid1 not in self.short_path:
            mLogger.warning("({}, {})这个点被孤立了，哪里都去不了".format(x1, y1, x2, y2))
        else:
            result = self.short_path[pid1].get(pid2, None)
        if None == result:
            mLogger.warning("({}, {}) 到 ({}, {})找不到最短路".format(x1, y1, x2, y2))
        return result

    # 暴露给其它地方用的获取两个点之间的最短路径，再config配置中需要打开
    def get_short_length(self, x1, y1, x2, y2):
        if self.out_graph_border(x1, y1):
            mLogger.warning("start_point: ({}, {})越界了".format(x1, y1))
            return None
        if self.out_graph_border(x2, y2):
            mLogger.warning("end_point: ({}, {})越界了".format(x2, y2))
            return None

        pid1 = self.get_cell_id(x1, y1)
        pid2 = self.get_cell_id(x2, y2)
        result = None

        if pid1 in self.short_length:
            result = self.short_length[pid1].get(pid2, None)
        if None == result:
            self.create_short_path(pid1)
        if pid1 not in self.short_length:
            mLogger.warning("({}, {})这个点被孤立了，哪里都去不了".format(x1, y1, x2, y2))
        else:
            result = self.short_length[pid1].get(pid2, None)
        if None == result:
            mLogger.warning("({}, {}) 到 ({}, {})找不到最短路".format(x1, y1, x2, y2))
        return result

    # 暴露给其它地方用的获取两个点之间的最短路径的移动方向
    def get_short_move(self, x1, y1, x2, y2):
        if self.out_graph_border(x1, y1):
            return None
        if self.out_graph_border(x2, y2):
            return None

        pid1 = self.get_cell_id(x1, y1)
        pid2 = self.get_cell_id(x2, y2)

        result = None
        if pid1 in self.short_move:
            result = self.short_move[pid1].get(pid2, None)
        if None == result:
            self.create_short_path(pid1)

        if pid1 not in self.short_move:
            mLogger.warning("({}, {})这个点被孤立了，哪里都去不了".format(x1, y1, x2, y2))
        else:
            result = self.short_move[pid1].get(pid2, None)
        if None == result:
            mLogger.warning("({}, {}) 到 ({}, {})找不到最短路".format(x1, y1, x2, y2))
        return result

    # 初始化地图数组
    def initialize_graph(self, width, height):
        self.graph = [['.'] * width for _ in range(height)]

    # msg消息给出的传送带是up,down,left,right在graph中，存成字符形式s
    def get_tunnel_label(self, s):
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

    # 创建地图，赋值地图每个格子的元素
    def create_graph(self):
        for meteor in self.msg['msg_data']['map']['meteor']:
            self.graph[meteor['y']][meteor['x']] = '#'
        for tunnel in self.msg['msg_data']['map']['tunnel']:
            self.graph[tunnel['y']][tunnel['x']
                                    ] = self.get_tunnel_label(tunnel["direction"])
        for wormhole in self.msg['msg_data']['map']['wormhole']:
            self.graph[wormhole['y']][wormhole['x']] = wormhole["name"]
            self.wormhole[wormhole['name']] = (wormhole['x'], wormhole['y'])

    # 初始化赋值msg
    def initialize_msg(self, msg):
        self.msg = msg
        self.short_path.clear()
        self.short_move.clear()
        self.short_length.clear()
        self.wormhole.clear()
        self.tunnel_go.clear()
        self.graph = []    # 空地: '.',  障碍物: '#', 虫洞: '字母', 传送带: '<>^|'
        self.tol_cells = 0
        self.fa = []
        self.cell_vis_cnt.clear()

    # 初始化所有的players
    def create_players(self):
        teams = self.msg['msg_data'].get("teams", [])
        for team in teams:
            team_id = team.get("id", -1)
            if team_id == config.team_id:
                players = team.get("players", [])
                force = team.get("force", "NULL")
                for player in players:
                    mPlayers[player] = Player(
                        fish_id=player, team_id=team_id, force=force)
            else:
                players = team.get("players", [])
                force = team.get("force", "NULL")
                for player in players:
                    othPlayers[player] = Player(
                        fish_id=player, team_id=team_id, force=force)

    def excute(self, msg):
        # 初始化赋值msg
        self.initialize_msg(msg)
        width = self.msg['msg_data']['map']['width']
        height = self.msg['msg_data']['map']['height']
        # 定义地图的总格子数
        self.tol_cells = width * height
        # 初始化地图变量
        self.initialize_graph(width, height)
        # 根据msg消息创建地图，二维数组
        # 空地: '.',  障碍物: '#', 虫洞: '字母', 传送带: '<>^|'
        self.create_graph()
        # 预处理所有传送带的位置，这个传送到可以直接到哪里
        self.init_tunnel_go()
        self.create_players()


mLegStart = LegStart()
