# -*- coding: utf-8 -*-

import redis

from dns_admin.libs import const


connection = 0
if connection == 0:
    client = redis.Redis(
        host=const.REDIS_HOST, port=const.REDIS_PORT, db=const.REDIS_DB)
    connection += 1
else:
    pass
