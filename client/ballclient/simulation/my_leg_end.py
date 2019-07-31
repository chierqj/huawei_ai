# coding: utf-8
'''
:param msg:
{
    "msg_name" : "leg_end",
    "msg_data" : {
        "teams" : [
        {
            "id" : 1001,				#队ID
            "point" : 770             #本leg的各队所得点数
        },
        {
        "id" : 1002,
        "point" : 450
            }
        ]
    }
}

:return:
teams = msg["msg_data"]['teams']
for team in teams:
    print "teams:%s" % team['id']
    print "point:%s" % team['point']
    print "\n\n"
'''


class LegEnd(object):
    def __init__(self):
        self.msg = ""
        self.tolPoint = dict()

    def initialize_msg(self, msg):
        self.msg = msg

    def excute(self, msg):
        self.initialize_msg(msg)
        teams = msg["msg_data"]['teams']
        for team in teams:
            point = self.tolPoint.get(str(team['id']), 0)
            self.tolPoint[str(team['id'])] = point + team["point"]


mLegEnd = LegEnd()
