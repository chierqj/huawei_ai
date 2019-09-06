# coding=utf-8

import logging
import os
from ballclient.auth import config


def need_log(text=''):
    if False == config.record_log:
        return

    def metric(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return metric


class Logger:

    def __init__(self, path=config.log_file_path, clevel=logging.DEBUG, Flevel=logging.DEBUG):
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.DEBUG)
        # fmt = logging.Formatter(
        #     '[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s] - %(message)s', '%H:%M:%S')
        fmt = logging.Formatter(
            '[%(levelname)s] - %(message)s')

        # 设置CMD日志
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.setLevel(clevel)
        # 设置文件日志
        fh = logging.FileHandler(path, mode='w')
        fh.setFormatter(fmt)
        fh.setLevel(Flevel)
        # self.logger.addHandler(sh)
        self.logger.addHandler(fh)

    @need_log
    def debug(self, message):
        self.logger.debug(message)

    @need_log
    def info(self, message):
        self.logger.info(message)

    @need_log
    def war(self, message):
        self.logger.warn(message)

    @need_log
    def error(self, message):
        self.logger.error(message)

    @need_log
    def cri(self, message):
        self.logger.critical(message)


mLogger = Logger().logger
