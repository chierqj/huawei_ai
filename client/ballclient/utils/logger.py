# coding=utf-8

import logging
import os
from ballclient.auth import config


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

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def war(self, message):
        self.logger.warn(message)

    def error(self, message):
        self.logger.error(message)

    def cri(self, message):
        self.logger.critical(message)


mLogger = Logger().logger
