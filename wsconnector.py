import os
import io
import json
import random
import urllib
import asyncio
import datetime
import aiomysql
from wsconnector import WebsocketHandler
import tornado.ioloop
import tornado.httpclient
import tornado.web
import tornado.auth
import tornado.template
import tornado.websocket
import user_agents
"""
basic connection:
|   nickname    |
|   google ID   |
|               |
|               |
"""
class WebsocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")