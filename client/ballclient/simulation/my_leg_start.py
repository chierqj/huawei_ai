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

class LegStart(object):
    def __init__(self):
        self.msg = ""
        self.short_path = []

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        mLogger.info(msg["msg_data"]["map"])
        self.create_short_path()

    def create_short_path(self):
        width = self.msg['msg_data']['map']['width']
        height = self.msg['msg_data']['map']['height']
        tol = width * height
        self.short_path = [[] * tol for _ in range(tol)]


mLegStart = LegStart()
