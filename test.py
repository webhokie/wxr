#!/usr/bin/env python
# coding=utf-8

import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.netutil
import tornado.process
import os
from datetime import *
import hashlib
import logging as L
from weixin import WeiXinMessageProcessor
from db import MySQL

TOKEN = 'blah_token'

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        # mysql stuff
        self.db = MySQL()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('main.html')

class WeiXinHandler(BaseHandler):
    def initialize(self):
        super(WeiXinHandler, self).initialize()
        self.processor = WeiXinMessageProcessor(TOKEN, self.db)

    def get(self):
        signature = self.get_argument('signature')
        timestamp = self.get_argument('timestamp')
        nonce = self.get_argument('nonce')
        echostr = self.get_argument('echostr')
        #if checkSignature(signature, timestamp, nonce):
        if self.processor.checkSignature(signature, timestamp, nonce):
            self.write(echostr)
        else:
            self.write('fail')
    
    def post(self):
        L.error("request: %s" % self.request.body)
        res = self.processor.processMessage(self.request.body)
        L.error("response: %s" % res)
        if res and len(res) > 0:
            self.write(res)

class RegisterHandler(BaseHandler):
    def get(self):
        self.render('static/register.html', errors=None)

    def post(self):
        tel = self.get_argument("telephone").strip()
        pwd = self.get_argument("password").strip()
        usr = self.get_argument("username").strip()
        wx_id = self.get_argument("wx_id").strip()
        L.error('%s\t%s\t%s\t%s\n' % (wx_id, usr, pwd, tel))
        res = self.db.select('select * from user where telephone = "%s"' % tel)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if res is not None:
            self.render('static/register.html', errors='手机号已被注册')
        else:
            res = self.db.select('select wx_id from user where wx_id = "%s"' % wx_id)
            try:
                if res is not None:
                    self.db.updateCondition('user', {'telephone':tel, 'password':pwd, 'username':usr, 'register_time':now}, 'wx_id="%s"' % wx_id)
                else:
                    self.db.insertCondition('user', {'telephone':tel, 'password':pwd, 'username':usr, 'register_time':now, 'wx_id':wx_id, 'follow_time':now})
            except:
                self.render('static/register.html', errors='未知错误')
            self.render('static/success.html')

settings = {
    "static_path" : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/weixin", WeiXinHandler),
    (r"/register.*", RegisterHandler),
], **settings)

if __name__ == "__main__":
    # single process
    application.listen(80)

    # multi process
    #sockets = tornado.netutil.bind_sockets(80)
    #tornado.process.fork_processes(0)
    #server = tornado.httpserver.HTTPServer(application)
    #server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
