from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.db.session import SessionLocal

from app import models
from app.models import User
from app.routers.auth import router as auth_router
from app.routers.order import router as order_router
from app.routers.user import router as user_router
from app.routers import client, equipment
from app.routers.ui import router as ui_router, get_user_from_token_value

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(client.router)
app.include_router(equipment.router)
app.include_router(ui_router)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/app"):
        if exc.status_code == 403:
            return templates.TemplateResponse(
                request,
                "errors/403.html",
                {},
                status_code=403,
            )

        if exc.status_code == 404:
            return templates.TemplateResponse(
                request,
                "errors/404.html",
                {},
                status_code=404,
            )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def custom_internal_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/app"):
        return templates.TemplateResponse(
            request,
            "errors/500.html",
            {},
            status_code=500,
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

@app.middleware("http")
async def ui_auth_middleware(request: Request, call_next):
    path = request.url.path
    request.state.current_user = None

    if path.startswith("/static"):
        return await call_next(request)

    access_token = request.cookies.get("access_token")

    if path in {"/", "/app", "/app/login", "/app/logout"}:
        if access_token:
            db = SessionLocal()
            try:
                user = get_user_from_token_value(access_token, db)
                request.state.current_user = user
            finally:
                db.close()

        return await call_next(request)

    if path.startswith("/app"):
        if not access_token:
            return RedirectResponse(url="/app/login", status_code=303)

        db = SessionLocal()
        try:
            user = get_user_from_token_value(access_token, db)
            if not user:
                return RedirectResponse(url="/app/login", status_code=303)

            request.state.current_user = user
        finally:
            db.close()

    return await call_next(request)

@app.get("/")
def root():
    return RedirectResponse(url="/app/login", status_code=303)