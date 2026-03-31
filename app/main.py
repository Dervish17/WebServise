from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

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

@app.middleware("http")
async def ui_auth_middleware(request: Request, call_next):
    path = request.url.path

    if path.startswith("/static"):
        return await call_next(request)

    if path in {"/", "/app", "/app/login", "/app/logout"}:
        return await call_next(request)

    if path.startswith("/app"):
        ui_user_email = request.cookies.get("ui_user_email")
        if not ui_user_email:
            return RedirectResponse(url="/app/login", status_code=303)

    return await call_next(request)

@app.get("/")
def root():
    return RedirectResponse(url="/app/login", status_code=303)