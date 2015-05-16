#-*- coding: utf-8 -*-

import subprocess
import re
import random
import time
import sys


def shell(cmd):
    process = subprocess.Popen(
        args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    std_out, std_err = process.communicate()
    return_code = process.poll()
    return return_code, std_out, std_err


def get_hostname():
    cmd = "hostname "
    rc, so, se = shell(cmd)

    if rc == 0:
        return so


def get_inner_ip():
    cmd = "hostname -i"
    rc, so, se = shell(cmd)

    if rc == 0:
        return so


def get_extra_ip():
    """ 获取公网IP.

    """

    cmd = ''' /sbin/ifconfig |grep "inet addr:" |egrep -v '''\
            '''"127.0.0.1|10\.|192\.168\." |awk '{print $2}' '''\
            '''\|awk -F ":" '{print $2}' '''
    rc, so, se = shell(cmd)

    if rc == 0:
        return so


def is_valid_ip(ip):
    """ 检查ip是否合法.

    """

    p = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    s = p.findall(ip.strip())
    if s == []:
        return False

    return len([i for i in s[0].split('.') if (0 <= int(i) <= 255)]) == 4


def mac_random():
    mac = [0x00, 0x16, 0x3e, random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff), random.randint(0x00, 0xff)]
    s = []
    for item in mac:
        s.append(str("%02x" % item))

    return ':'.join(s)


def ping(ip):
    cmd = "ping -c 3 %s &>/dev/null " % ip

    rc, so, se = shell(cmd)
    if rc == 0:
        return True
    else:
        return False


def dns_check(hostname):
    cmd = "nslookup %s &>/dev/null " % hostname

    rc, so, se = shell(cmd)
    if rc == 0:
        return True
    else:
        return False


def check_wait(check_cmd, post_cmd, timeinit=0, interval=10, timeout=600):
    """ 循环等待某一条件成功, 就执行post_cmd, 时间超过 timeout 就超时.

    """

    timetotal = timeinit

    while timetotal < timeout:
        rc, ro, re = shell(check_cmd)
        if rc != 0:
            rc, ro, re = shell(post_cmd)
            if rc == 0:
                return True
            else:
                return False

        time.sleep(interval)
        timetotal += interval

    return False
