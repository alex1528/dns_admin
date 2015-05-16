#-*- coding: utf-8 -*-

""" 根据名称查看一个域的记录.

"""

from dns_admin.libs import mysqloj


def _get(name):
    _mysql_oj = mysqloj.PooledConnection()
    sql = "select id, name, type, value from %s " % name
    data = _mysql_oj.select(sql)

    result = list()
    for item in data:
        _dict = {
            "id": item[0],
            "name": item[1],
            "type": item[2],
            "value": item[3]
        }
        result.append(_dict)
    return result


def get(name=None):
    _mysql_oj = mysqloj.PooledConnection()
    if name is None:
        result = list()
        sql = "select name from domain "
        names = _mysql_oj.select(sql)
        names = [ i[0] for i in names ]
        for name in names:
            result.extend(_get(name))
        return result
    else:
        return _get(name)
