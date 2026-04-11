import hmac
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
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
from app.core.csrf import generate_csrf_token
from app.core.template_helpers import can_manage, has_role, is_admin

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["has_role"] = has_role
templates.env.globals["is_admin"] = is_admin
templates.env.globals["can_manage"] = can_manage

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(client.router)
app.include_router(equipment.router)
app.include_router(ui_router)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    is_app = request.url.path.startswith("/app")
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_app:
        if is_htmx:
            if exc.status_code == 401:
                response = HTMLResponse("")
                response.headers["HX-Redirect"] = "/app/login"
                return response

            if exc.status_code in {403, 404}:
                text = (
                    "Доступ запрещён."
                    if exc.status_code == 403
                    else "Запрошенный объект не найден."
                )
                response = templates.TemplateResponse(
                    request,
                    "shared/_alert.html",
                    {
                        "text": text,
                        "kind": "error",
                    },
                    status_code=200,
                )
                response.headers["HX-Retarget"] = "#global-alert"
                response.headers["HX-Reswap"] = "innerHTML"
                return response

        if exc.status_code == 401:
            return RedirectResponse(url="/app/login", status_code=303)

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
    csrf_cookie = request.cookies.get("csrf_token")

    is_app_path = path.startswith("/app")
    is_htmx = request.headers.get("HX-Request") == "true"
    is_mutating = request.method in {"POST", "PUT", "PATCH", "DELETE"}

    if path in {"/", "/app", "/app/login", "/app/logout"}:
        if access_token:
            db = SessionLocal()
            try:
                user = get_user_from_token_value(access_token, db)
                request.state.current_user = user
            finally:
                db.close()

        response = await call_next(request)

        if is_app_path and request.method == "GET" and not csrf_cookie:
            response.set_cookie(
                key="csrf_token",
                value=generate_csrf_token(),
                httponly=False,
                samesite="lax",
                secure=request.url.scheme == "https",
                path="/",
            )

        return response

    if is_app_path:
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

        if is_mutating:
            csrf_header = request.headers.get("X-CSRF-Token")

            if (
                not csrf_cookie
                or not csrf_header
                or not hmac.compare_digest(csrf_cookie, csrf_header)
            ):
                if is_htmx:
                    response = templates.TemplateResponse(
                        request,
                        "shared/_alert.html",
                        {
                            "text": "CSRF validation failed. Обновите страницу и повторите действие.",
                            "kind": "error",
                        },
                        status_code=200,
                    )
                    response.headers["HX-Retarget"] = "#global-alert"
                    response.headers["HX-Reswap"] = "innerHTML"
                    return response

                return templates.TemplateResponse(
                    request,
                    "errors/403.html",
                    {},
                    status_code=403,
                )

    response = await call_next(request)

    if is_app_path and request.method == "GET" and not csrf_cookie:
        response.set_cookie(
            key="csrf_token",
            value=generate_csrf_token(),
            httponly=False,
            samesite="lax",
            secure=request.url.scheme == "https",
            path="/",
        )

    return response

@app.get("/")
def root():
    return RedirectResponse(url="/app/login", status_code=303)