from fastapi import FastAPI
from app.db.database import Base, engine
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router
from app.routers.order import router as order_router
from app.routers import client, equipment

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