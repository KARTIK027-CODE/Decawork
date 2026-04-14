from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from backend.services.db import db

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

# Mock session handling (in reality we would use cookies/JWT)
# For simplicity, we just check query params or assume logged in based on state in a real app.
# Since it's a mock admin panel, we'll use a simple cookie.
# BUT to make UI purely browser interactable without strict auth blocks, let's use cookies.

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    user = db.get_user_by_email(email)
    if user and user.password == password:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="session_user", value=email)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_user")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_email = request.cookies.get("session_user")
    if not user_email:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    user = db.get_user_by_email(user_email)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request):
    user_email = request.cookies.get("session_user")
    if not user_email:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    users = db.list_users()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.get("/users/create", response_class=HTMLResponse)
async def create_user_page(request: Request):
    return templates.TemplateResponse("create_user.html", {"request": request})

@router.post("/users/create")
async def create_user_submit(request: Request, email: str = Form(...), name: str = Form(...), password: str = Form(...)):
    if db.get_user_by_email(email):
        return templates.TemplateResponse("create_user.html", {"request": request, "error": "User already exists"})
    db.create_user(email, name, password)
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)

@router.get("/users/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str):
    user = db.get_user_by_email(email)
    if not user:
        return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("reset_password.html", {"request": request, "user": user})

@router.post("/users/reset-password")
async def reset_password_submit(request: Request, email: str = Form(...), new_password: str = Form(...)):
    db.update_password(email, new_password)
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)
