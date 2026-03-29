from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models
from app.routers.auth import router as auth_router
from app.routers.order import router as order_router
from app.routers.user import router as user_router
from app.routers import client, equipment
from app.routers.ui import router as ui_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(client.router)
app.include_router(equipment.router)
app.include_router(ui_router)


@app.get("/")
def root():
    return {"status": "ok"}