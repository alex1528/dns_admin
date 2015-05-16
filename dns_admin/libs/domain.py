#-*- coding: utf-8 -*-

""" 根据名称查看一个域的信息, 信息包括:

    域名;
    配置文件路径;
    serial 值

"""

from dns_admin.libs import mysqloj


def get(name=None):
    _mysql_oj = mysqloj.PooledConnection()
    if name is None:
        result = list()
        sql = "select name, domain, path, serial from domain "
        data = _mysql_oj.select(sql)
        for item in data:
            _dict = {
                "name": item[0],
                "domain": item[1],
                "path": item[2],
                "serial": item[3]
            }
            result.append(_dict)
    else:
        sql = "select name, domain, path, serial from domain "\
            "where name='%s' " % name
        data = _mysql_oj.select(sql)
        data = data[0]
        result = {
            "name": data[0],
            "domain": data[1],
            "path": data[2],
            "serial": data[3]
        }
    return result