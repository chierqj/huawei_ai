# coding: utf-8

from ballclient.utils.logger import mLogger


import time
import functools


def msimulog(text=''):
    def metric(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t_begin = time.time()
            st_info = text + '[%s start]' % (fn.__name__)
            mLogger.debug(st_info)
            res = fn(*args, **kwargs)
            t_end = time.time()
            ex_t = '%.3f' % ((t_end - t_begin) * 1000)
            ed_info = text + \
                '[{} end] [executed: {}ms]'.format(fn.__name__, ex_t)
            mLogger.debug(ed_info)
            return res
        return wrapper
    return metric
