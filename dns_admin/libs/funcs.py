#-*- coding: utf-8 -*-

import re
import shutil
import os


from dns_admin.libs import utils, domain


def reload(domain=None):
    """ 重新加载配置.

    """
    if domain is None:
        dns_reload_cmd = "/usr/sbin/rndc reload "
    else:
        dns_reload_cmd = "/usr/sbin/rndc reload %s " % domain

    rc, ro, re = utils.shell(dns_reload_cmd)
    if rc == 0:
        return True
    else:
        return False


def check(hostname=None, ip=None):
    """ 检查 hostname 和 ip 是否合法.

    """
    if hostname is None and ip is None:
        return 

    # names 是域的名称.
    names = [ i["name"] for i in domain.get()]
    names.remove("reverse")   # 删除反向记录 reverse

    if hostname and ip is None:
        if not filter(lambda x: ".%s" % x in hostname, names):
            return False
    elif ip and hostname is None:
        if not utils.is_valid_ip(ip):
            return False
    else:
        if not filter(lambda x: ".%s" % x in hostname, names):
            return False
        if not utils.is_valid_ip(ip):
            return False
    return True


def dns(hostname=None, ip=None):
    """ 把 hostname 或者 ip 修改为 dns 需要的形式.

    正向解析只对 hostname 做解析, 反向解析只对 ip 做解析.

    比如 db1.hy01 在解析文件里是 db1, 而 10.0.12.51 在反向解析文件里面
    是 51.12.0 .

    """
    if hostname is None and ip is None:
        return
    elif hostname and ip is None:
        hostname_dns = ".".join(hostname.strip().split(".")[:-1])
        return hostname_dns
    elif ip and hostname is None:
        ip_dns = ip.split(".")[-1] + "." + ip.split(
            ".")[-2] + "." + ip.split(".")[-3]
        return ip_dns
    else:
        hostname_dns = ".".join(hostname.strip().split(".")[:-1])
        ip_dns = ip.split(".")[-1] + "." + ip.split(
            ".")[-2] + "." + ip.split(".")[-3]
        return hostname_dns, ip_dns


def table(hostname=None, ip=None):
    """ 根据 hostname 和 ip 返回 Mysql 数据库中的表名.

    比如 hostname 是 pxe0.hy01, 那么返回 hy01;

    对于 ip, 因为只有一个反向域, 直接返回 reverse.

    """
    if hostname is None and ip is None:
        return
    elif hostname and ip is None:
        return hostname.split(".")[-1]
    elif ip and hostname is None:
        return "reverse"
    else:
        return hostname.split(".")[-1], "reverse"
