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
import uuid
import wsconnector
import aiomysql
#from wsconnector import WebsocketHandler
import tornado.ioloop
import tornado.httpclient
import tornado.web
import tornado.auth
import tornado.template
import tornado.httpserver
import tornado.httputil
import tornado.websocket
import user_agents
import sys
print(os.getcwd())
REDIRURL=sys.argv[1] if len(sys.argv)>=2 else"http://127.0.0.1:8000/"
print(REDIRURL)
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
            self.redirect("/Lobby.html")
    class account(tornado.web.RequestHandler,tornado.auth.GoogleOAuth2Mixin):
        async def get(self):
            self.settings["google_oauth"]={"key":"801663922478-sg6opa1be1ur4vi5levltb957414auq1.apps.googleusercontent.com","secret":"KpAmXqKa1tEP2e4V6Yml4TEV"}
            if self.get_argument('code', False)!=False:
                access = await self.get_authenticated_user(
                    redirect_uri=REDIRURL+'account',
                    code=self.get_argument('code'))
                user = await self.oauth2_request(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    access_token=access["access_token"])
                user=json.dumps(user)
                self.write('''<script>localStorage.setItem('google',`%s`);window.location.href="/";</script>%s''' % (user,user))#костылиус
            else:
                self.authorize_redirect(
                    redirect_uri=REDIRURL+'account',
                    client_id=self.settings["google_oauth"]["key"],
                    scope=['openid','profile'],
                    response_type='code',
                    extra_params={'approval_prompt': 'auto'})
    class fakelogon(tornado.web.RequestHandler,tornado.auth.GoogleOAuth2Mixin):
        async def get(self):
            user='{"id": "%s", "name": "Gameplayer 55055", "given_name": "Gameplayer", "family_name": "55055", "picture": "https://lh3.googleusercontent.com/a-/AOh14GjubdFKBR3eLD6pIteIIUdCOTSFF6qbC2XaFUVB=s96-c", "locale": "uk"}' % str(uuid.uuid4())
            self.write('''<script>localStorage.setItem('google',`%s`);window.location.href="/";</script>%s''' % (user,user))#костылиус

    class unlogin(tornado.web.RequestHandler):
        def get(self):
            self.clear_cookie("logintoken")
            self.redirect("/")

#tornado support is deprecated. but it works great because of OOP.
#better to use FastAPI, but u can use tornado as well
class WebsocketConnector(tornado.websocket.WebSocketHandler):
    def open(self) -> None:#TODO: abstract websocket
        print("WebSocket opened")
        wsconnector.clients.add(self)
        self.session=dict()
        super().open()

    async def on_message(self, message:str):
        data = wsconnector.ClientPacket(message)
        if not data.validate():
            self.close()#wrong data, go away spammer
            return
        ret = await data.consumePacket(self)#duck typing
        print(ret)
        if ret:
            await self.send_json(ret)
        else:
            await self.send_json({"pck":"ack"})

    def on_close(self) -> None:
        wsconnector.clients.remove(self)
        return super().on_close()
    async def send_json(self,data):
        self.write_message(json.dumps(data))



cookie_secret = "qidjjowkpojepqweiumvcowytojoiefjreoifjewpfj[woxpowejxfiwjfxwijefxpw"



def app()->tornado.web.Application:
    root_path=os.getcwd()
    return tornado.web.Application([
        (r"/", Mainframe.index),
        (r"/account", Mainframe.account),
        (r"/fake", Mainframe.fakelogon),
        (r"/pool", WebsocketConnector),
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
