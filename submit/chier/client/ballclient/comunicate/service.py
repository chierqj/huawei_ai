# encoding:utf8
'''
业务方法模块，需要选手实现

选手也可以另外创造模块，在本模块定义的方法中填入调用逻辑。这由选手决定

所有方法的参数均已经被解析成json，直接使用即可

所有方法的返回值为dict对象。客户端会在dict前面增加字符个数。
'''
from ballclient.simulation.my_leg_start import mLegStart
from ballclient.simulation.my_round import mRound
from ballclient.simulation.my_leg_end import mLegEnd
from ballclient.simulation.my_game_over import mGameOver
from ballclient.utils.logger import mLogger


def leg_start(msg):
    try:
        mLegStart.excute(msg)
    except Exception as e:
        mLogger.error(e)


def round(msg):
    try:
        mRound.excute(msg)
        return mRound.get_result()
    except Exception as e:
        mLogger.error(e)


def leg_end(msg):
    try:
        mLegEnd.excute(msg)
    except Exception as e:
        mLogger.error(e)


def game_over(msg):
    try:
        mGameOver.excute(msg)
    except Exception as e:
        mLogger.error(e)