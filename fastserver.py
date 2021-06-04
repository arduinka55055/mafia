from typing import List
from mafia import PlayerRAW

from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.endpoints import WebSocketEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

import fastapi
from fastapi import FastAPI
from fastapi import responses
from fastapi.params import Cookie
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='!secret')
config = Config('.env')
oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid profile'
    }
)


@app.get("/",response_class=RedirectResponse)
async def index():
    return RedirectResponse("Lobby.html")


@app.get('/login', tags=['authentication'])
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get('/account',response_class= RedirectResponse)
async def auth(request: Request):
    # Perform Google OAuth
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    
    #запихиваем все в PlayerRAW
    data=PlayerRAW(gid=user.sub,name=user.name,avatar=user.picture)
    response=RedirectResponse('/')
    response.set_cookie(key="google",value=jsonable_encoder(vars(data)))
    return response


@app.get('/logout',response_class= RedirectResponse, tags=['authentication'])  # Tag it as "authentication" for our docs
async def logout(request: Request):
    response=RedirectResponse('/')
    response.delete_cookie("google")
    return response



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/pool")
async def websocket_endpoint(websocket: WebSocket):
    #websocket.
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client 1 says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client 1 left the chat")





    
app.mount("/", StaticFiles(directory="front-end"), name="static")
app.mount("/static", StaticFiles(directory="static"), name="static2")

app.debug=True













"""
import user_agents
import sys,os
print(os.getcwd())
REDIRURL=sys.argv[1] if len(sys.argv)>=2 else"http://127.0.0.1:8000/"
print(REDIRURL)
"""
'''
Site navigation plan:

Landing -> oauth2login - | set cookie uuid
   \\----> email login - |
                         |
        lobby selector<--#
        \\//
game itself        
'''
"""

'''def app()->tornado.web.Application:
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
"""