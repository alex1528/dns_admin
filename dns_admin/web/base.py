# -*- coding: utf-8 -*-

import sys

import tornado.web

from dns_admin.libs import session


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.session = session.Session(self.application.session_manager, self)

    def get_current_user(self):
        return self.session.get("username")