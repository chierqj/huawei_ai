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
need_short_move = False

# log是否输出详细每条鱼每一步的情况
record_detial = True

'''
计算权重
'''
# 能量系数
BEAT_POWER_WEIGHT = 1.0
# 敌方的鱼的系数
BEAT_PLAYER_WEIGHT = 1.5


THINK_POWER_WEIGHT = 1.0
THINK_PLAYER_WEIGHT = 1.2

# 每个格子避免重复走累加的数字
CELL_WEIGHT = 0.001
# last_appear_dis的衰变系数 += last_appear_dis * ALPHA
ALPHA = 0.8
# delta;player在计算出来的距离上面减去多少，因为怕被吃
DELTA = 0.8