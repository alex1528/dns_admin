#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import socket
import re

import ujson as json

import tornado.web
import tornado.httpserver
import tornado.options
import tornado.escape
import tornado.netutil

from dns_admin.libs import const, session, ldapauth, mysqloj
from dns_admin.libs import funcs, domain, record, oper
from dns_admin.web import base


demo = ldapauth.Auth()


class IndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if username:
            self.render("index.html")
        else:
            self.redirect("/login")


class LoginHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("login.html")


class LogoutHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if username:
            self.session["username"] = None
            self.session.save()
            self.redirect("/login")


class LdapauthHandler(base.BaseHandler):

    def post(self):
        username = self.get_argument('username')
        if username.endswith("@nosa.me"):
            username = username.strip("@nosa.me")
        password = self.get_argument("password")
        if demo.auth(username, password):
            self.session["username"] = username
            self.session.save()
            self.redirect("/")
        else:
            return self.render('ldap_login_failed.html')


class LdapauthapiHandler(base.BaseHandler):

    def post(self):
        username = self.get_argument('username')
        if username.endswith("@nosa.me"):
            username = username.strip("@nosa.me")
        password = self.get_argument("password")

        ret_dict = {}
        if demo.auth(username, password):
            self.session["username"] = username
            self.session.save()
            ret_dict['result'] = "success"
        else:
            ret_dict['result'] = "error"
        self.write(json.dumps(ret_dict))


class DomainIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("domain_index.html")


class DomainQueryIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("domain_index.html")


class OperIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("oper_index.html")


class OperQueryIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("oper_query_index.html")


class OperAddIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("oper_add_index.html")


class OperModifyIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("oper_modify_index.html")


class OperDeleteIndexHandler(base.BaseHandler):

    def get(self):
        username = self.get_current_user()
        if not username:
            self.redirect("/login")
        self.render("oper_delete_index.html")


class DomainHandler(base.BaseHandler):

    def get(self, name):
        """ 查看某个域信息的 api.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        ret = domain.get(name)
        self.write(json.dumps(ret))


class DomainALLHandler(base.BaseHandler):

    def get(self):
        """ 查看所有域信息的 api.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        ret = domain.get()
        self.write(json.dumps(ret))


class RecordHandler(base.BaseHandler):

    def get(self, name):
        """ 某一个域的所有记录 api.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        ret = record.get(name)
        self.write(json.dumps(ret))


class RecordALLHandler(base.BaseHandler):

    def get(self):
        """ 所有域的所有记录 api.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        ret = record.get()
        self.write(json.dumps(ret))


class DataTableRecordHandler(base.BaseHandler):

    def get(self, name):
        """ 某一个域的所有记录 api, 格式为了 Data Tree 做了处理.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        _list = list()
        for i in record.get(name):
            _list.append([i["id"], i["name"], i["type"], i["value"]])            
        _ret = {
            "aaData": _list,
            "iTotalRecords": len(_list),
            "sEcho": 0,
            "iTotalDisplayRecords": len(_list)
        }
        self.write(json.dumps(_ret))


class DataTableALLRecordHandler(base.BaseHandler):

    def get(self):
        """ 某所有域的所有记录 api, 格式为了 Data Tree 做了处理.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        _list = list()
        for i in record.get():
            _list.append([i["id"], i["name"], i["type"], i["value"]])            
        _ret = {
            "aaData": _list,
            "iTotalRecords": len(_list),
            "sEcho": 0,
            "iTotalDisplayRecords": len(_list)
        }
        self.write(json.dumps(_ret))


class QueryHandler(base.BaseHandler):

    def get(self):
        """ 查询 api.

        key 表示通过指定hostname还是ip来查询;
        dnslist 一个list，里面是hostname或者ip的值.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        key = self.get_argument("key", None)
        dnslist = self.get_argument("dnslist", None)
        dnslist = eval(dnslist)

        if key not in ["hostname", "ip"]:
            ret = {
                'status': "failed",
                'result': "must assgin hostname or ip to query."
            }
            self.write(json.dumps(ret))
            return

        if dnslist is None:
            ret = {
                'status': "failed",
                'result': "please assgin hostname or ip."
            }
            self.write(json.dumps(ret))
            return

        if key == "hostname":
            for i in dnslist:
                if not funcs.check(hostname=i.strip()):
                    ret = {
                        'status': "failed",
                        'result': "hostname - %s is illegal.." % i
                    }
                    self.write(json.dumps(ret))
                    return
        elif key == "ip":
            for i in dnslist:
                if not funcs.check(ip=i.strip()):
                    ret = {
                        'status': "failed",
                        'result': "ip - %s is illegal.." % i
                    }
                    self.write(json.dumps(ret))
                    return
        ret = {
            'status': "success",
            'result': oper.query(key, dnslist)
        }
        self.write(json.dumps(ret))


class AddHandler(base.BaseHandler):

    def post(self):
        """ 增加 api.

        dnslist 一个list，元素是 hostname 和 ip 组成的字典.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        dnslist = self.get_argument("dnslist", None)
        dnslist = eval(dnslist)

        if dnslist is None:
            ret = {
                'status': "failed",
                'result': "please assgin hostname and ip."
            }
            self.write(json.dumps(ret))
            return

        # 添加之前做检查.
        for i in dnslist:
            hostname = i["hostname"].strip()
            ip = i["ip"].strip()

            # 规则检查.
            if not funcs.check(hostname, ip):
                ret = {
                    'status': "failed",
                    'result': "hostname or ip is illegal."
                }
                self.write(json.dumps(ret))
                return

            # 如果主机名最后一个域是 internal, 则表示是内网域名, 可以重复
            # 添加, 所以增加之前不检查主机名是否已经存在.
            import re
            pattern = re.compile(r".internal$")
            match = pattern.search(hostname)
            if match:
                continue

            # 记录存在检查(只检查 hostname 是否已经存在, ip 不检查)
            _ip = oper.query("hostname", [hostname])[0]["ip"]
            if _ip != []:
                ret = {
                    'status': "failed",
                    'result': "%s record exists." % hostname
                }
                self.write(json.dumps(ret))
                return

        status, result = oper.add(dnslist)
        if status:
            ret = {
                'status': "success",
                'result': "add success"
            }
        else:
            ret = {
                'status': "failed",
                'result': result
            }
        self.write(json.dumps(ret))

        return


class ModifyHandler(base.BaseHandler):

    def post(self):
        """ 修改 api.

        key 表示通过指定hostname还是ip来修改.
        dnslist 一个list，里面是hostname和ip的值.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        key = self.get_argument("key", None)
        dnslist = self.get_argument("dnslist", None)
        dnslist = eval(dnslist)

        if key not in ["hostname", "ip"]:
            ret = {
                'status': "failed",
                'result': "must assgin hostname or ip to modify."
            }
            self.write(json.dumps(ret))
            return

        if dnslist is None:
            ret = {
                'status': "failed",
                'result': "please assgin hostname and ip."
            }
            self.write(json.dumps(ret))
            return

        for i in dnslist:
            hostname = i["hostname"].strip()
            ip = i["ip"].strip()

            if not funcs.check(hostname, ip):
                ret = {
                    'status': "failed",
                    'result': "hostname or ip is illegal."
                }
                self.write(json.dumps(ret))
                return

            if key == "hostname":
                _ip = oper.query(
                    "hostname", [hostname])[0]["ip"]
                if _ip == []:
                    ret = {
                        'status': "failed",
                        'result': "hostname - %s record not exists." % hostname
                    }
                    self.write(json.dumps(ret))
                    return
            elif key == "ip":
                # 对于内网域名, 由于不写反向记录, 此处查不到.
                # 对于主机名, hostname 只有一个(如果有残余主机名
                # 有这个 ip, 应该先把残余主机名删掉).
                # 所以此处 _hostname 为空或只有一个元素.
                _hostname = oper.query("ip", [ip])[0]["hostname"]
                if _hostname == []:
                    ret = {
                        'status': "failed",
                        'result': "ip - %s record not exists." % ip
                    }
                    self.write(json.dumps(ret))
                    return
                # 如果旧的主机名域和新的主机名域不同, 退出.
                elif _hostname[0].split(".")[-1] != hostname.split(".")[-1]:
                    ret = {
                        'status': "failed",
                        'result': "dns domain is not same."
                    }
                    self.write(json.dumps(ret))
                    return

        status, result = oper.modify(key, dnslist)
        if status:
            ret = {
                'status': "success",
                'result': "dns record modify success."
            }
        else:
            ret = {
                'status': "failed",
                'result': result
            }
        self.write(json.dumps(ret))


class DeleteHandler(base.BaseHandler):

    def post(self):
        """ 删除 api.

        key 表示通过指定hostname还是ip来删除.
        dnslist 一个list，里面是 hostname 或者 ip 的值.

        """
        username = self.get_current_user()
        if not username:
            self.redirect("/login")

        key = self.get_argument("key", None)
        dnslist = self.get_argument("dnslist", None)
        dnslist = eval(dnslist)

        if key not in ["hostname", "ip"]:
            ret = {
                'status': "failed",
                'result': "must assgin hostname or ip to delete."
            }
            self.write(json.dumps(ret))
            return

        if dnslist is None:
            ret = {
                'status': "failed",
                'result': "please assgin hostname or ip."
            }
            self.write(json.dumps(ret))
            return

        for i in dnslist:
            if key == "hostname":
                hostname = i.strip()
                if not funcs.check(hostname=hostname):
                    ret = {
                        'status': "failed",
                        'result': "hostname or ip is illegal."
                    }
                    self.write(json.dumps(ret))
                    return

                _ip = oper.query(
                    "hostname", [hostname])[0]["ip"]
                if _ip == []:
                    ret = {
                        'status': "failed",
                        'result': "hostname - %s not exists,can't delete." % hostname
                    }
                    self.write(json.dumps(ret))
                    return
            elif key == "ip":
                ip = i.strip()
                if not funcs.check(ip=ip):
                    ret = {
                        'status': "failed",
                        'result': "hostname or ip is illegal."
                    }
                    self.write(json.dumps(ret))
                    return

                _hostname = oper.query("ip", [ip])[0]["hostname"]
                if _hostname == []:
                    ret = {
                        'status': "failed",
                        'result': "ip - %s not exists,can't delete." % ip
                    }
                    self.write(json.dumps(ret))
                    return

        status, result = oper.delete(key, dnslist)
        if status:
            ret = {
                'status': "success",
                'result': "delete success."
            }
            self.write(json.dumps(ret))
        else:
            ret = {
                'status': "failed",
                'result': result
            }
            self.write(json.dumps(ret))


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/",           IndexHandler),
            (r"/login",      LoginHandler),
            (r"/logout",     LogoutHandler),
            (r"/ldapauth",   LdapauthHandler),
            (r"/api/v1/ldapauth", LdapauthapiHandler),
            # 页面.
            (r"/domain/index", DomainIndexHandler),
            (r"/oper/index", OperIndexHandler),
            (r"/oper/query/index", OperQueryIndexHandler),
            (r"/oper/add/index", OperAddIndexHandler),
            (r"/oper/modify/index", OperModifyIndexHandler),
            (r"/oper/delete/index", OperDeleteIndexHandler),
            # API.
            (r"/api/v1/domains/records/([^/]+)/?",  RecordHandler),
            (r"/api/v1/domains/records/?",  RecordALLHandler),            
            (r"/api/v1/domains/([^/]+)/?",  DomainHandler),
            (r"/api/v1/domains/?",  DomainALLHandler),
            (r"/api/v1/query/?",  QueryHandler),
            (r"/api/v1/add/?",    AddHandler),
            (r"/api/v1/modify/?", ModifyHandler),
            (r"/api/v1/delete/?", DeleteHandler),
            # Data Table API.
            (r"/api/v1/dt/records/([^/]+)/?",  DataTableRecordHandler),
            (r"/api/v1/dt/records/?",  DataTableALLRecordHandler),
        ]

        settings = {
            'debug': False,
            'template_path': os.path.join(os.path.dirname(__file__), "../../dns_admin/templates"),
            'static_path': os.path.join(os.path.dirname(__file__), "../../dns_admin/static"),
            'cookie_secret': "z1D234AVwerh+WTvyqJCQLwerETQYUznEweruYskSF062J0To",
            'session_secret': "3cdcb1f234008103b6e78ab50b466a40b9977db396840c2830",
            'session_timeout': 60 * 60 * 24 * 30
            # "xsrf_cookies": True,
        }

        tornado.web.Application.__init__(self, handlers, **settings)
        self.session_manager = session.SessionManager(
            settings["session_secret"], settings["session_timeout"])


def main():
    sockets = tornado.netutil.bind_sockets(
        const.BIND_PORT, address=const.BIND_IP, family=socket.AF_INET)
    tornado.process.fork_processes(0)

    application = Application()
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    http_server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
