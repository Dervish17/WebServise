from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import login_user
from app.routers.ui_shared import templates

router = APIRouter(tags=["ui"])


@router.get("/app/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {},
    )


@router.post("/app/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        result = login_user(db, email, password)
    except HTTPException:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Неверный email, пароль или пользователь деактивирован.",
                "email": email,
            },
            status_code=400,
        )

    token = None

    if isinstance(result, str):
        token = result
    elif isinstance(result, dict):
        token = result.get("access_token")

    if not token:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Неверный email, пароль или пользователь деактивирован.",
                "email": email,
            },
            status_code=400,
        )

    response = RedirectResponse(url="/app/orders", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )

    response.set_cookie(
        key="ui_user_email",
        value=email,
        httponly=True,
        samesite="lax",
        path="/",
    )

    return response


@router.get("/app/logout")
def logout():
    response = RedirectResponse(url="/app/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("ui_user_email", path="/")
    return response
