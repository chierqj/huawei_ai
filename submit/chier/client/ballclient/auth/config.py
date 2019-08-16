# coding: utf-8

# 队伍ID
team_id = None
# 队伍名称
team_name = "A+CK.AI"

# 本地日志目录; 提交日志目录（submit时候注意替换）
# log_file_path = 'C:/Users/chier/Desktop/huawei_ai/log/battle.log'
log_file_path = '/var/log/battle.log'

# debug模式最短路径也保存，提交的时候不需要
need_short_path = False

# 是否需要计算最短路第一步的移动方向
need_short_move = False

# log是否输出详细每条鱼每一步的情况
record_detial = True

# log是否打印评分信息
record_weight = False

'''
计算权重
'''
# 能量系数
BEAT_POWER_WEIGHT = 1.0
# 敌方的鱼的系数
BEAT_PLAYER_WEIGHT = -4.0


THINK_POWER_WEIGHT = 1.0
THINK_PLAYER_WEIGHT = 0.0

# 每个格子避免重复走累加的数字
CELL_WEIGHT = 0.00001
# 在我看不到鱼的时候
# dis = ALPHA * dis + BELTA * last_appear_dis
# dis = 0的话就不加评分了
POWER_ALPHA = 0.0
POWER_BELAT = 0.0

PLAYER_ALPHA = 0.0
PLAYER_BELTA = 0.0
