from fastapi import FastAPI
from app.db.database import Base, engine
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router
from app.routers.order import router as order_router
from app.routers import client, equipment
from app.models.user import User
from app.models.client import Client
from app.models.equipment import Equipment
from app.models.order import Order
from app.models.status_history import StatusHistory
from app.models.order_log import OrderLog

app = FastAPI()
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(client.router)
app.include_router(equipment.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "ok"}