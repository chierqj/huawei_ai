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
        self.my_team_force = None
        self.FATHER = dict()
        self.SONS = dict()
        self.width = None
        self.height = None

    '''
    暴露给外面的接口
    1. 获取最短路经
    2. 获取最短路径长度
    '''
    # 暴露给其它地方用的获取两个点之间的最短路径，再config配置中需要打开

    def get_short_path(self, x1, y1, x2, y2):
        if self.match_border(x1, y1):
            return None
        if self.match_border(x2, y2):
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
        if self.match_border(x1, y1):
            mLogger.warning("start_point: ({}, {})越界了".format(x1, y1))
            return None
        if self.match_border(x2, y2):
            mLogger.warning("end_point: ({}, {})越界了".format(x2, y2))
            return None
        if x1 == x2 and y1 == y2:
            return 0

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

    '''
    保存路径信息相关:
    1. 更新保存最短路经
    2. 更新保存最短路经的第一步
    3. 更新保存最短路径长度
    '''

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

    '''
    地图自身物理属性相关：
    1. 根据(x, y)获取映射id
    2. 根据映射id获取(x, y)
    3. 判断(x, y)是否超出边界
    4. 判断(x, y)物理上是不是可以走 [边界 & 障碍]
    5. 判断(x, y)是不是传送带
    6. 判断(x, y)是不是虫洞
    7. 判断(x, y)是不是满足bfs的起点条件 [. | 虫洞]
    8. 根据(x, y)获取地图的元素
    '''

    # condition 1
    def get_cell_id(self, x, y):
        return x * self.msg['msg_data']['map']['width'] + y

    # condition 2
    def get_x_y(self, pid):
        x = int(pid / self.msg['msg_data']['map']['width'])
        y = pid % self.msg['msg_data']['map']['width']
        return x, y

    # condition 3
    def match_border(self, x, y):
        if x < 0 or x >= self.msg['msg_data']['map']['width']:
            return True
        if y < 0 or y >= self.msg['msg_data']['map']['height']:
            return True
        return False

    # condition 4
    def match_physic_can_go(self, x, y):
        if self.match_border(x, y):
            return False
        if self.get_graph_cell(x, y) == '#':
            return False
        return True

    # condition 5
    def match_tunnel(self, x, y):
        c = self.get_graph_cell(x, y)
        if c == '>' or c == '<' or c == '^' or c == '|':
            return True
        return False

    # condition 6
    def match_wormhole(self, x, y):
        c = self.get_graph_cell(x, y)
        if c.isalpha() and c.lower() in self.wormhole and c.upper() in self.wormhole:
            return True
        return False

    # condition 7
    def match_bfs(self, x, y):
        cell = self.get_graph_cell(x, y)
        if cell == '.' or self.match_wormhole(x, y):
            return True
        return False

    # 因为定义横方向是x轴，因此获取px, py在地图上是什么的时候。必须用这个方法获取，否则就是反的
    def get_graph_cell(self, px, py):
        return self.graph[py][px]

    # 打印地图
    def print_graph(self):
        print(" "),
        for i in range(20):
            print i, "\t",
        print
        for i, row in enumerate(self.graph):
            print i, "\t".join(row)

    '''
    处理地图特殊情况
    1. 预处理传送门
    2. 输入虫洞的字母，返回对应另一个虫洞的位置映射id
    3. 输入一个传送带的位置映射id，返回传送带的出口位置映射id
    4. 创建边集合
    '''

    # 预处理所有的传送带
    def init_tunnel_go(self):
        for tunnel in self.msg['msg_data']['map']['tunnel']:
            px, py = tunnel['x'], tunnel['y']
            u = self.get_cell_id(px, py)
            while True:
                cell = self.get_graph_cell(px, py)
                if False == self.match_tunnel(px, py):
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

    # 创建所有边关联
    def create_edge(self):
        def go_next(x, y, move):
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
        def real_go_point(x, y, move):
            go_x, go_y = go_next(x, y, move)
            if False == self.match_physic_can_go(go_x, go_y):
                return None, None
            go_cell = self.get_graph_cell(go_x, go_y)
            if self.match_tunnel(go_x, go_y):
                go_cell_id = self.get_cell_id(go_x, go_y)
                go_x, go_y = self.get_x_y(mLegStart.do_tunnel(go_cell_id))
            if self.match_wormhole(go_x, go_y):
                go_x, go_y = self.get_x_y(mLegStart.do_wormhoe(go_cell))
            return go_x, go_y

        # 获取下一步移动的位置，仅判断是不是合法
        def get_next_one_points(x, y):
            moves = ['up', 'down', 'left', 'right']
            result = []
            for move in moves:
                # 获取move之后真正到达的位置
                go_x, go_y = real_go_point(x, y, move)
                if go_x == None:
                    continue
                if False == self.match_physic_can_go(go_x, go_y):
                    continue
                if go_x == x and go_y == y:
                    continue
                result.append((move, go_x, go_y))
            return result

        for x in range(self.width):
            for y in range(self.height):
                cell = self.get_graph_cell(x, y)
                if cell != '.' and False == self.match_wormhole(x, y):
                    continue

                ucell = self.get_cell_id(x, y)
                next_points = get_next_one_points(x, y)
                for mv, nx, ny in next_points:
                    vcell = self.get_cell_id(nx, ny)

                    fathers = self.FATHER.get(vcell, set())
                    fathers.add(ucell)
                    self.FATHER[vcell] = fathers

                    sons = self.SONS.get(ucell, [])
                    sons.append((mv, nx, ny))
                    self.SONS[ucell] = sons

    '''
    求最短路经，同时保存结果
    '''

    # 单点最短路，顺带记录了start到它能到的其他点的最短路，不用每次都求
    def create_short_path(self, start_point):
        if start_point in self.short_length:
            return
        import Queue
        # bfs 需要变量
        q = Queue.Queue()
        vis = set()

        # 记录最短路路径需要变量
        if True == config.need_short_path:
            pre = dict()
            pre[start_point] = -1

        # 队列添加第一个节点
        q.put((start_point, 0))
        vis.add(start_point)

        while False == q.empty():
            uid, ustep = q.get()
            self.update_short_length_dict(start_point, uid, ustep)
            sons = self.SONS.get(uid)
            for mv, nx, ny in sons:
                vid = self.get_cell_id(nx, ny)
                if vid in vis:
                    continue
                vis.add(vid)
                q.put((vid, ustep + 1))
                if True == config.need_short_path:
                    pre[vid] = uid

        if True == config.need_short_path:
            for point in vis:
                tmp, path = point, []
                while tmp != -1:
                    path.append(self.get_x_y(tmp))
                    tmp = pre[tmp]
                path = path[::-1]
                self.update_short_path_dict(start_point, point, path)

    '''
    初始化相关
    1. 初始化msg
    2. 初始化地图
    3. 初始化players对象
    '''

    # 初始化赋值msg
    def initialize_msg(self, msg):
        self.msg = msg
        self.short_path.clear()
        self.short_move.clear()
        self.short_length.clear()
        self.wormhole.clear()
        self.tunnel_go.clear()
        self.graph = []    # 空地: '.',  障碍物: '#', 虫洞: '字母', 传送带: '<>^|'
        self.my_team_force = None
        self.FATHER.clear()
        self.SONS.clear()
        self.width = self.msg['msg_data']['map']['width']
        self.height = self.msg['msg_data']['map']['height']
        self.tol_cells = self.width * self.height

        mPlayers.clear()
        othPlayers.clear()

        mLogger.info(self.msg)

    # 创建地图，赋值地图每个格子的元素
    def initialize_graph(self):
        def get_tunnel_label(s):
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
        self.graph = [['.'] * self.width for _ in range(self.height)]
        for meteor in self.msg['msg_data']['map']['meteor']:
            self.graph[meteor['y']][meteor['x']] = '#'
        for tunnel in self.msg['msg_data']['map']['tunnel']:
            self.graph[tunnel['y']][tunnel['x']
                                    ] = get_tunnel_label(tunnel["direction"])
        for wormhole in self.msg['msg_data']['map']['wormhole']:
            self.graph[wormhole['y']][wormhole['x']] = wormhole["name"]
            self.wormhole[wormhole['name']] = (wormhole['x'], wormhole['y'])

    # 创建所有player obj
    def create_player_obj(self):
        teams = self.msg['msg_data']['teams']
        for team in teams:
            team_id = team['id']
            force = team['force']
            if team['id'] == config.team_id:
                self.my_team_force = team['force']
                for pid in team['players']:
                    mPlayers[pid] = Player(
                        fish_id=pid,
                        team_id=team_id,
                        force=force,
                    )
            else:
                for pid in team['players']:
                    othPlayers[pid] = Player(
                        fish_id=pid,
                        team_id=team_id,
                        force=force,
                    )

    '''
    入口流程
    1. 初始化消息
    2. 初始化地图
    3. 预处理传送带
    4. 初始化边集合
    5. 初始化players对象
    '''

    # 程序入口
    def excute(self, msg):
        self.initialize_msg(msg)
        self.initialize_graph()
        self.init_tunnel_go()
        self.create_edge()
        self.create_player_obj()

        for k, v in self.SONS.iteritems():
            ux, uy = self.get_x_y(k)
            mLogger.info("({}, {}) -> {}".format(ux, uy, v))


mLegStart = LegStart()
