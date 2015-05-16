#-*- coding: utf-8 -*-

""" 根据模板生成 bind 配置文件.

"""


from jinja2 import Environment, FileSystemLoader

from dns_admin.libs import const, funcs, logger, mysqloj, domain, record, utils


def _serial(name):
    """设置 serial 的值, 使之加1, 而且返回加1后的值.

    由于 Mysql 的事务处理功能, 在并发条件下 serial 值是安全的.

    """
    sqls = [
        "select serial from domain where name='%s' for update " % name,
        "update domain set serial = serial + 1 where name='%s' " % name,
        "select serial from domain where name='%s' " % name
    ]

    _mysql_oj = mysqloj.PooledConnection()
    return _mysql_oj.sqls(sqls)


def _get(serial, data, template_dir, template_file, conf_path):
    """ 生成某个域的配置文件.

    """
    try:
        j2_env = Environment(loader=FileSystemLoader(template_dir),
                             trim_blocks=True)
        ret = j2_env.get_template(template_file).render(
            serial=serial,
            data=data
        )
        if isinstance(ret, unicode):
            ret = ret.encode("utf-8")
        with file(conf_path, 'w') as f:
            f.writelines(ret)
    except Exception, e:
        return (False, "%s" % e)

    return (True, None)


def get(names=None):
    """ 生成某些域的配置文件并重新加载.

    """
    if names is None:
        return (False, "please assgin domain name to be templated.")

    # 如果 names 是空列表, 返回 True.
    if names == []:
        return (True, "no any domain is templated.")

    for name in names:
        status, serial = _serial(name)
        serial = serial[0][0]
        if not status:
              return (status, serial)
        conf_path = domain.get(name)["path"]
        records = record.get(name)

        status, result = _get(serial, records, const.BIND_TEMPLATE_DIR, const.BIND_TEMPLATE_FILE, conf_path)
        message = "template bind conf, status:%s, result:%s, serial:%s, "\
                    "conf_path:%s" % (status, result, serial, conf_path)
        logger.logger.info(message)
        if not status:
            return (status, result)

        cmd = "chown named:named %s" % conf_path
        rc, ro, re = utils.shell(cmd)
        message = "cmd:%s, return_code:%s, return_output:%s, "\
                    "return_error:%s" % (cmd, rc, ro, re)
        logger.logger.info(message)
        if rc != 0:
            return (False, re)

    if funcs.reload():
        return (True, None)
    else:
        return (False, "reload named failed")