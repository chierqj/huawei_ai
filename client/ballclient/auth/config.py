# coding: utf-8

# 队伍ID
team_id = None
# 队伍名称
team_name = "A+CK.AI"

# 本地日志目录; 提交日志目录（submit时候注意替换）
log_file_path = 'C:/Users/chier/Desktop/huawei_ai/log/battle.log'
# log_file_path = '/var/log/battle.log'

# debug模式最短路径也保存，提交的时候不需要
need_short_path = False

# 是否需要计算最短路第一步的移动方向
need_short_move = True

# log是否输出详细每条鱼每一步的情况
record_detial = True

# 权重
POWER_WEIGHT = 1.0
PLAYER_WEIGHT = 3.0
CELL_WEIGHT = 0.01
