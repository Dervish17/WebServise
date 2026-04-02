from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.user_service import (
    create_user,
    delete_user,
    toggle_user_active,
    update_user,
)
from app.routers.ui_shared import get_current_ui_user, render_alert, templates

router = APIRouter(tags=["ui"])


@router.get("/app/users")
def users_page(request: Request):
    return templates.TemplateResponse(
        request,
        "users/page.html",
        {},
    )


@router.get("/app/users/table")
def users_table(
    request: Request,
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.desc()).all()

    return templates.TemplateResponse(
        request,
        "users/_table.html",
        {"users": users},
    )


@router.post("/app/users/create")
def create_user_ui(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    last_name: str = Form(None),
    first_name: str = Form(None),
    middle_name: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(
            request, "Только администратор может создавать пользователей.", "error"
        )

    create_user(
        db=db,
        email=email,
        password=password,
        role=role,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
    )

    response = templates.TemplateResponse(
        request,
        "users/_create_result.html",
        {},
    )
    response.headers["HX-Trigger"] = "refreshUsers"
    return response


@router.get("/app/users/{user_id}/edit")
def edit_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(
            request, "Только администратор может редактировать пользователей.", "error"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return render_alert(request, "Пользователь не найден.", "error")

    return templates.TemplateResponse(
        request,
        "users/_edit.html",
        {"user": user},
    )


@router.post("/app/users/{user_id}/edit")
def edit_user_submit(
    user_id: int,
    request: Request,
    email: str = Form(...),
    role: str = Form(...),
    last_name: str = Form(None),
    first_name: str = Form(None),
    middle_name: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(
            request, "Только администратор может редактировать пользователей.", "error"
        )

    try:
        update_user(
            db=db,
            user_id=user_id,
            email=email,
            role=role,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
        )
    except ValueError:
        return render_alert(request, "Пользователь не найден.", "error")

    response = HTMLResponse("")
    response.headers["HX-Trigger"] = "refreshUsers"
    return response


@router.delete("/app/users/{user_id}")
def delete_user_ui(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(
            request, "Только администратор может удалять пользователей.", "error"
        )

    try:
        delete_user(
            db=db,
            user_id=user_id,
            current_user_id=current_user.id,
        )

        response = HTMLResponse("")
        response.headers["HX-Trigger"] = "refreshUsers"
        return response

    except HTTPException as e:
        return render_alert(request, e.detail, "error")


@router.post("/app/users/{user_id}/toggle-active")
def toggle_user_active_ui(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ui_user),
):
    if current_user.role != "admin":
        return render_alert(
            request, "Только администратор может менять статус пользователей.", "error"
        )

    try:
        toggle_user_active(
            db=db,
            user_id=user_id,
            current_user_id=current_user.id,
        )

        response = HTMLResponse("")
        response.headers["HX-Trigger"] = "refreshUsers"
        return response

    except HTTPException as e:
        return render_alert(request, e.detail, "error")
