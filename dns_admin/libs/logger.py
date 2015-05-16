#-*- coding: utf-8 -*-

import os
import logging

from dns_admin.libs import const


def get_logger():
    logger_ = logging.getLogger("dns-admin")
    formatter = logging.Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] [%(funcName)s] %(message)s', '%Y-%m-%d %H:%M:%S',)
    handler = logging.FileHandler(const.LOG_DIR + "/" + const.LOG_FILE)
    handler.setFormatter(formatter)
    logger_.addHandler(handler)
    logger_.setLevel(logging.DEBUG)
    return logger_


if not os.path.isdir(const.LOG_DIR):
    os.makedirs(const.LOG_DIR)


logger = get_logger()
