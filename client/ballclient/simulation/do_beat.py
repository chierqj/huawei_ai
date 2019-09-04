# coding: utf-8

from ballclient.simulation.my_leg_start import mLegStart
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.auth import config
from ballclient.simulation.my_player import mPlayers, othPlayers, Player
from ballclient.simulation.my_power import Power
import random
import math
from ballclient.simulation.my_action import Action


class DoBeat(Action):
    def __init__(self):
        super(DoBeat, self).__init__()

    def init(self):
        pass
        
    def do_excute(self):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            


mDoBeat = DoBeat()
