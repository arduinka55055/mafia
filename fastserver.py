from typing import Dict, List
from mafia import PlayerRAW

from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route, WebSocketRoute
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
import wsconnector
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
'''
Site navigation plan:

Landing -> oauth2login - | set cookie uuid
   \\----> email login - |
                         |
        lobby selector<--#
        \\//
game itself        
'''

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


WebSocket.__hash__=lambda self: hash(self.client)


class WebsocketConnector(WebSocketEndpoint):
    async def on_connect(self, websocket: WebSocket) -> None:
        print("WebSocket opened")
        wsconnector.clients.add(websocket)
        return await super().on_connect(websocket)

    async def on_receive(self, client:WebSocket,message:Dict):
        data = wsconnector.ClientPacket(message)
        if not data.validate():
            await client.close()#wrong data, go away spammer
            return
        ret = await data.consumePacket(client)
        print(ret)
        if ret:
            await client.send_json(ret)
        else:
            await client.send_json({"pck":"ack"})

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        wsconnector.clients.remove(websocket)
        return await super().on_disconnect(websocket, close_code)
    



rr=WebSocketRoute("/pool", WebsocketConnector)
app.router.add_websocket_route("/pool",rr)


app.mount("/", StaticFiles(directory="front-end"), name="static")

app.debug=True

