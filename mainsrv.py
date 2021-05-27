#!/usr/bin/env python3   
#MAFIA server
#Copyright (C) 2021 Vitiaz D., Chernikov M. 

#This program is free software: you can redistribute it and/or modify it under
#the terms of the GNU General Public License as published by the Free Software
#Foundation, either version 3 of the License, or any later version.

#This program is distributed in the hope that it will be useful, but WITHOUT ANY
#WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS FOR
#A PARTICULAR PURPOSE. See the GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along with
#this program. If not, see <http://www.gnu.org/licenses/>.

import os
import io
import json
import random
import urllib
import asyncio
import datetime
from wsconnector import WebsocketConnector
import aiomysql
#from wsconnector import WebsocketHandler
import tornado.ioloop
import tornado.httpclient
import tornado.web
import tornado.auth
import tornado.template
import tornado.httpserver
import user_agents
print(os.getcwd())
'''
Site navigation plan:

Landing -> oauth2login - | set cookie uuid
   \\----> email login - |
                         |
        lobby selector<--#
        \\//
game itself        
'''
class Mainframe():
    class index(tornado.web.RequestHandler):
        async def get(self):
            self.write(tornado.template.Loader(os.getcwd() + "/front-end/").load("registration.html").generate())
    class account(tornado.web.RequestHandler,tornado.auth.GoogleOAuth2Mixin):
        async def get(self):
            self.settings["google_oauth"]={"key":"801663922478-sg6opa1be1ur4vi5levltb957414auq1.apps.googleusercontent.com","secret":"KpAmXqKa1tEP2e4V6Yml4TEV"}
            if self.get_argument('code', False)!=False:
                access = await self.get_authenticated_user(
                    redirect_uri='http://127.0.0.1:8000/account',
                    code=self.get_argument('code'))
                user = await self.oauth2_request(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    access_token=access["access_token"])
                user=json.dumps(user)
                self.write('''<script>localStorage.setItem('google',`%s`);</script>%s''' % (user,user))#костылиус
            else:
                self.authorize_redirect(
                    redirect_uri='http://127.0.0.1:8000/account',
                    client_id=self.settings["google_oauth"]["key"],
                    scope=['openid','profile'],
                    response_type='code',
                    extra_params={'approval_prompt': 'auto'})

    class unlogin(tornado.web.RequestHandler):
        def get(self):
            self.clear_cookie("logintoken")
            self.redirect("/")

    class start(tornado.web.RequestHandler):
        async def get(self):
            self.redirect("/?started")

    class stylesheet(tornado.web.StaticFileHandler):
        def initialize(self,path):
            self.dirname, self.filename = os.path.split(path)
            self.absolute_path=path
            self.root=self.dirname
            super(tornado.web.StaticFileHandler,self).initialize()

        async def get(self, path=None, include_body=True):
            print("МОБІЛКА" if user_agents.parse(
                self.request.headers["User-Agent"]).is_mobile else "комп")
            if user_agents.parse(self.request.headers["User-Agent"]).is_mobile:

                await super().get("Lobby.css", include_body)#TODO Макс поменяй названия
            else:
                await super().get("feedback.css", include_body)#TODO Макс поменяй названия
    class favicon(tornado.web.RequestHandler):
        def prepare(self):
            self.set_header("Content-Type", 'image/ico; charset="utf-8"')

        def get(self):
            self.write(open('static/favicon.ico', 'rb').read())

cookie_secret = "alkhflkjawhrcqwilbcrkqwcbrewncywonvwqoqcrwn"


class MyStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')

def app()->tornado.web.Application:
    root_path=os.getcwd()
    return tornado.web.Application([
        (r"/", Mainframe.index),
        (r"/account", Mainframe.account),
        (r"/pool", WebsocketConnector),
        (r"/css", Mainframe.stylesheet,{'path': root_path + "/static/"}),#TODO Макс вставь папку где стили лежат
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': root_path + "/static/"}),
        (r'/img/(.*)', tornado.web.StaticFileHandler, {'path': root_path + "/front-end/img/"}),
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': root_path + "/front-end/"}),
    ],
        cookie_secret=cookie_secret,
        xsrf_cookies=False,
        xsrf_cookie_kwargs=dict(samesite="Lax"),
        hsts=True,debug=True,
        websocket_ping_interval=2,
        websocket_ping_timeout=5

    )

http_server = tornado.httpserver.HTTPServer(app(), xheaders=True)
if __name__ == '__main__':
    http_server.listen(8000)
    tornado.ioloop.IOLoop.current().start()
