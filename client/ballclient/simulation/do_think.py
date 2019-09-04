# coding: utf-8

import math
import random

from ballclient.auth import config
from ballclient.simulation.my_action import Action
from ballclient.simulation.my_leg_start import mLegStart
from ballclient.simulation.my_player import Player, mPlayers, othPlayers
from ballclient.simulation.my_power import Power
from ballclient.utils.logger import mLogger
from ballclient.utils.time_wapper import msimulog
from ballclient.simulation.my_leg_end import mLegEnd


class DoThink(Action):
    def __init__(self):
        super(DoThink, self).__init__()
        self.grab_player = None

    def init(self):
        self.grab_player = None

    # def 

    def do_excute(self):
        for k, player in mPlayers.iteritems():
            if player.sleep == True:
                continue
            player.move = ""

mDoThink = DoThink()
