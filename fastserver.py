from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/", StaticFiles(directory="front-end"), name="static")

app.mount("/static", StaticFiles(directory="static"), name="static2")

@app.get("/")
async def root():
    return "hello"
app.debug=True