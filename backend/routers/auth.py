# routers/auth.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from services.auth import register_user, login_user, refresh_access, logout
from dependencies.auth_user import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterIn(BaseModel):
    email: str
    username: str
    password: str


class LoginIn(BaseModel):
    identifier: str
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user = register_user(db, data.email, data.username, data.password)
    return {"message": "Usuário registrado", "user_id": user.id}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    return login_user(db, data.identifier, data.password)


@router.post("/refresh")
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    return refresh_access(db, data.refresh_token)


@router.post("/logout")
def do_logout(data: RefreshIn, db: Session = Depends(get_db)):
    return logout(db, data.refresh_token)


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "active": user.is_active
    }
