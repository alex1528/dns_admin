#-*- coding: utf-8 -*-

""" 实现增删改查.

"""

import os
import sys
import shutil

from dns_admin.libs import logger, utils, const, \
    funcs, mysqloj, template


def add(dnslist):
    """ dnslist 里面包括 hostname 和 ip, 正向解析文件和反向解析文件都会被修改.

    如果是内网域名,则不增加反向记录.
    
    """
    logger.logger.info(dnslist)

    # 设置一个变量, 用来标识需要生成哪些域的配置(增加 serial 而且 reload bind).
    # 变量类型用 dict.
    domains_changed = dict()

    # 修改数据库.
    for i in dnslist:
        hostname = i["hostname"].strip()
        ip = i["ip"].strip()

        # 去掉 hostname 的后缀; 获取 ip 的第一位, 然后反向.
        hostname_dns, ip_dns = funcs.dns(hostname, ip)

        # 获取数据库表名.
        hostname_table, ip_table = funcs.table(hostname, ip)

        # 获取数据库执行对象.
        _mysql_oj = mysqloj.PooledConnection()

        # 增加正向解析.
        sql = """insert into %s (name, type, value) values """\
                """("%s", "A", "%s"); """ % (hostname_table, \
                hostname_dns, ip)
        status, result = _mysql_oj.change(sql)
        message = "sql:[%s], status:[%s], result:[%s]" % (sql, status, result)
        logger.logger.info(message)
        if not status:
            return (status, result)

        # 修改 domains_changed.
        domains_changed[hostname.split(".")[-1]] = None

        # 如果不是 internal 域, 增加反向记录.
        if hostname.split(".")[-1] != "internal":
            sql = """insert into %s (name, type, value) values """\
                    """("%s", "PTR", "%s.nosa.me."); """ % (ip_table, \
                    ip_dns, hostname)
            status, result = _mysql_oj.change(sql)
            message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                % (sql, status, result)
            logger.logger.info(message)
            if not status:
                return (status, result)

            # 修改 domains_changed.
            domains_changed["reverse"] = None

    # 生成配置文件, 并 reload.
    status, result = template.get(domains_changed.keys())
    message = "templates bind conf, names:[%s], status:[%s], result:[%s]" \
        % (sql, status, result)
    logger.logger.info(message)

    if not status:
        return (False, result)

    return (True, None)


def delete(key, dnslist):
    """ key 指根据 hostname 还是 ip 删除记录, dnslist 里面是 
        hostname 或者 ip.

    1). 如果 key 是 hostname, 会把 正向记录和反向记录都删除, 如果域
       是 internal, 因为本来就不添加 ip, 故反向记录不用删除.

    2). 如果 key 是 ip, 会删除反向记录, 正向记录怎么删除? 

        这里不是遍历所有的正向域, 删除有此 ip 的所有记录, 而是根据 
        ip 查反向记录, 根据查到的主机名列表(可能有多个机器名)拿到正
        向域列表, 然后去对应的正向域里删.

        因为内网域名的 ip 不会记录到反向域中, 所以根据 ip 删内网域名没有效果, 
        故内网域名只能通过 hostname 删除;
        对于主机名的 ip, 添加主机名记录的时候即使主机名的 ip 在反向记录里
        已经存在, 仍会添加, 所以这种方式能有效删除 ip 所对应的所有主机名记录.

    """
    logger.logger.info("key:%s %s" % (key, dnslist))

    # 设置一个变量, 用来标识需要生成哪些域的配置(增加 serial 而且 reload bind).
    # 变量类型用 dict.
    domains_changed = dict()

    _mysql_oj = mysqloj.PooledConnection()

    # 当 key 是 hostname 时, 删除记录.
    if key == "hostname":
        for i in dnslist:
            hostname = i.strip()

            # 去掉 hostname 的后缀.
            hostname_dns = funcs.dns(hostname=hostname)
    
            # 获取数据库表名.
            hostname_table = funcs.table(hostname=hostname)
    
            # 先查询对应的 ip.
            # 按照规则, 机器名只能有一个 ip, 而内网域名可能有多个 ip.
            # 当是主机名时, ip 只有一个;
            # 当是内网域名时, ip 可能有多个. 
            # 此处获取当是主机名的时候用, 故只有一个 ip.
            ip = query("hostname", [hostname])[0]["ip"]

            # 删除正向记录.
            sql = "delete from %s where name='%s' " % (\
                hostname_table, hostname_dns)
            status, result = _mysql_oj.change(sql)
            message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                % (sql, status, result)
            logger.logger.info(message)
            if not status:
                return (status, result)

            # 修改 domains_changed.
            domains_changed[hostname.split(".")[-1]] = None

            # 如果不是内网域名, 删除反向记录;
            # 如果是内网域名, 不用删除, 因为本来就没添加.
            if hostname.split(".")[-1] != "internal":
                # 获取数据库表名.
                ip_table = funcs.table(ip=ip)
    
                # 删除反向记录.
                # 此处根据主机名来删除, 也就是删除所有含有此主机名的反向记录.
                # 用到了主域 nosa.me. 
                sql = "delete from %s where value='%s.nosa.me.' " % (\
                    ip_table, hostname)
                status, result = _mysql_oj.change(sql)
                message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                    % (sql, status, result)
                logger.logger.info(message)
                if not status:
                    return (status, result)

                # 修改 domains_changed.
                domains_changed["reverse"] = None

    # 当 key 是 ip 时, 删除记录.
    if key == "ip":
        for i in dnslist:
            ip = i.strip()

            # 去掉 ip 第一个字段, 然后反向.
            ip_dns = funcs.dns(ip=ip)

            # 获取数据库表名.
            ip_table = funcs.table(ip=ip)

            # 根据 ip 查反向记录.
            # 后面删正向记录的时候用到.
            _hostname = query("ip", [ip])[0]["hostname"]

            # 删除反向记录.
            # 对于内网域名, 由于不添加反向记录, 故此处相当于没删.
            sql = "delete from %s where name='%s' " % (\
                ip_table, ip_dns)
            status, result = _mysql_oj.change(sql)
            message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                % (sql, status, result)
            logger.logger.info(message)
            if not status:
                return (status, result)

            # 修改 domains_changed.
            domains_changed["reverse"] = None

            # 对于内网域名, 由于不添加反向记录, _hostname 为空, 相当于没删.
            for hostname in _hostname:        
                # 获取数据库表名.
                hostname_table = funcs.table(hostname=hostname)
        
                # 删除正向记录.
                sql = "delete from %s where value='%s' " % (\
                    hostname_table, ip)
                status, result = _mysql_oj.change(sql)
                message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                    % (sql, status, result)
                logger.logger.info(message)
                if not status:
                    return (status, result)

                # 修改 domains_changed.
                domains_changed[hostname.split(".")[-1]] = None

    # 生成配置文件, 并 reload.
    status, result = template.get(domains_changed.keys())
    message = "templates bind conf, names:[%s], status:[%s], result:[%s]" \
        % (sql, status, result)
    logger.logger.info(message)

    if not status:
        return (False, result)

    return (True, None)


def modify(key, dnslist):
    """ key 表示通过 hostname 还是 ip 修改, dnslist 是个列表, 里面包括 
        hostname 和 ip.

    两种情况: 
    1). key 为 hostname, hostname 为 db1.hy01, ip为 10.1.21.34;
        表示把 hostname 是 db1.hy01 的记录的 ip 改为 10.1.21.34.

        如果域是 internal, 不修改反向记录.

    2). key 为 ip, ip 为 10.1.21.34, hostname 为 db1.hy01;            
        表示把 ip 是 10.1.21.34 的记录的 hostname 改为 db1.hy01.

        这里我们先根据 ip 查询反向域, 如果反向域没有此 ip, 说明可能是
        internal 域的 ip 或者不存在, 对于这种情况, 我们不予修改;

        如果旧主机名域和新主机名域不同, 报错退出.  

    注意: 不会判断要修改成的记录是否和之前记录一样, 会直接修改掉.

    """
    logger.logger.info("key:%s %s" % (key, dnslist))

    # 设置一个变量, 用来标识需要生成哪些域的配置(增加 serial 而且 reload bind).
    # 变量类型用 dict.
    domains_changed = dict()

    _mysql_oj = mysqloj.PooledConnection()

    # 当 key 是 hostname 时, 修改记录.
    if key == "hostname":
        for i in dnslist:
            hostname = i["hostname"].strip()
            ip = i["ip"].strip()

            # 去掉 hostname 的后缀.
            hostname_dns = funcs.dns(hostname=hostname)
    
            # 获取数据库表名.
            hostname_table = funcs.table(hostname=hostname)
    
            # 修改正向记录.
            sql = "update %s set value='%s' where %s.name='%s' " % (\
                hostname_table, ip, hostname_table, hostname_dns)
            status, result = _mysql_oj.change(sql)
            message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                % (sql, status, result)
            logger.logger.info(message)
            if not status:
                return (status, result)

            # 修改 domains_changed.
            domains_changed[hostname.split(".")[-1]] = None

            # 如果不是 internal 域, 修改反向记录.
            if hostname.split(".")[-1] != "internal":   
                # 去掉 hostname 的后缀.
                ip_dns = funcs.dns(ip=ip)
 
                # 获取数据库表名.
                ip_table = funcs.table(ip=ip)
    
                # 修改反向记录.
                # 用到了主域 nosa.me. 
                sql = "update %s set name='%s' where %s.value='%s.nosa.me.' " % (\
                    ip_table, ip_dns, ip_table, hostname)
                status, result = _mysql_oj.change(sql)
                message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                    % (sql, status, result)
                logger.logger.info(message)
                if not status:
                    return (status, result)

                # 修改 domains_changed.
                domains_changed["reverse"] = None

    # 当 key 是 ip 时, 修改记录.
    if key == "ip":
        for i in dnslist:
            hostname = i["hostname"].strip()
            ip = i["ip"].strip()

            # 去掉 ip 第一个字段, 然后反向.
            ip_dns = funcs.dns(ip=ip)

            # 获取数据库表名.
            ip_table = funcs.table(ip=ip)

            # 修改反向记录.
            sql = "update %s set value='%s.nosa.me.' where %s.name='%s' " % (\
                ip_table, hostname, ip_table, ip_dns)
            status, result = _mysql_oj.change(sql)
            message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                % (sql, status, result)
            logger.logger.info(message)
            if not status:
                return (status, result)

            # 修改 domains_changed.
            domains_changed["reverse"] = None

            # 去掉 hostname 的后缀.
            # 由于我们保证了旧主机名域和新主机名域相同, 所以可以用新主机名来获取.
            hostname_dns = funcs.dns(hostname=hostname)

            # 获取数据库表名.
            # 由于我们保证了旧主机名域和新主机名域相同, 所以可以用新主机名来获取.            
            hostname_table = funcs.table(hostname=hostname)
        
            # 修改正向记录.
            sql = "update %s set name='%s' where %s.value='%s' " % (\
                hostname_table, hostname_dns, hostname_table, ip)
            status, result = _mysql_oj.change(sql)
            message = "oper database, sql:[%s], status:[%s], result:[%s]"\
                % (sql, status, result)
            logger.logger.info(message)
            if not status:
                return (status, result)

            # 修改 domains_changed.
            domains_changed[hostname.split(".")[-1]] = None

    # 生成配置文件, 并 reload.
    status, result = template.get(domains_changed.keys())
    message = "templates bind conf, names:[%s], status:[%s], result:[%s]" \
        % (sql, status, result)
    logger.logger.info(message)

    if not status:
        return (False, result)
    return (True, None)
    

def query(key, dnslist):
    """ key 表示通过 hostname 还是 ip 查询, dnslist 是列表.

        hostname 通过查询正向文件;
        ip 通过查询反向文件.

    """
    logger.logger.info("key:%s %s" % (key, dnslist))

    _mysql_oj = mysqloj.PooledConnection()

    result = list()

    if key == "hostname":
        for i in dnslist:
            hostname = i.strip()

            # 去掉 hostname 的后缀.
            hostname_dns = funcs.dns(hostname=hostname)
    
            # 获取数据库表名.
            hostname_table = funcs.table(hostname=hostname)

            # 查询 ip, 对于 internal 域一个记录可能有多个 ip.
            sql = "select value from %s where name='%s' " % (
                hostname_table, hostname_dns)
            print sql
            data = _mysql_oj.select(sql)
            ip = [ i[0] for i in data]

            _dict = {
                "hostname": hostname,
                "ip": ip
            }
            result.append(_dict)

    if key == "ip":
        for i in dnslist:
            ip = i.strip()

            # 去掉 hostname 的后缀.
            ip_dns = funcs.dns(ip=ip)
    
            # 获取数据库表名.
            ip_table = funcs.table(ip=ip)

            # 查询 hostname, 有可能有多个 hostname 指向同一个 ip, 
            # 此时有两种情况:
            # 1. 如果 hostname 是机器名, 说明有的 hostname 是废弃的, 应该删掉;
            # 2. 如果 hostname 是内网域名, 属正常, 因为我们会把多个内网域名指向
            #    同一个 Vip.
            sql = "select value from %s where name='%s' " % (
                ip_table, ip_dns)
            print sql
            data = _mysql_oj.select(sql)
            # 去掉 .nosa.me.
            hostname = [ i[0].replace(".nosa.me.", "") for i in data]

            _dict = {
                "ip": ip,
                "hostname": hostname,
            }
            result.append(_dict)

    logger.logger.info(result)
    return result
