# services/auth.py
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models_auth import AuthUser, RefreshToken
from services.jwt_token import (
    create_access_token,
    create_refresh_token,
    REFRESH_EXPIRE_DAYS,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# ============================================================
# REGISTER
# ============================================================
def register_user(db: Session, email: str, username: str, password: str) -> AuthUser:
    exists = db.query(AuthUser).filter(
        (AuthUser.email == email) | (AuthUser.username == username)
    ).first()
    if exists:
        raise HTTPException(400, "Email ou username já existe")

    user = AuthUser(
        email=email,
        username=username,
        password_hash=_hash_password(password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# LOGIN
# - cria access token
# - cria refresh token e salva no banco (sessão)
# ============================================================
def login_user(db: Session, identifier: str, password: str):
    user = db.query(AuthUser).filter(
        (AuthUser.email == identifier) | (AuthUser.username == identifier)
    ).first()

    if not user or not _verify_password(password, user.password_hash):
        raise HTTPException(401, "Credenciais inválidas")

    if not user.is_active:
        raise HTTPException(403, "Usuário inativo")

    access = create_access_token(user.id)

    refresh_value = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)

    rt = RefreshToken(
        token=refresh_value,
        user_id=user.id,
        expires_at=expires_at,
        revoked=False
    )
    db.add(rt)
    db.commit()

    return {
        "access_token": access,
        "refresh_token": refresh_value,
        "token_type": "bearer"
    }


# ============================================================
# REFRESH
# - valida refresh no banco
# - se ok: revoga o refresh antigo
# - cria e salva um novo refresh (ROTAÇÃO)
# - devolve novo access + novo refresh
# ============================================================
def refresh_access(db: Session, refresh_token: str):
    rt = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not rt:
        raise HTTPException(401, "Refresh token inválido")

    if rt.revoked:
        raise HTTPException(401, "Refresh token revogado")

    if rt.expires_at and rt.expires_at < datetime.utcnow():
        raise HTTPException(401, "Refresh token expirado")

    user = db.query(AuthUser).filter(AuthUser.id == rt.user_id).first()
    if not user:
        raise HTTPException(401, "Usuário não encontrado")

    # 1) revoga o refresh antigo (rotação)
    rt.revoked = True

    # 2) cria novo refresh
    new_refresh_value = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)

    new_rt = RefreshToken(
        token=new_refresh_value,
        user_id=user.id,
        expires_at=expires_at,
        revoked=False
    )
    db.add(new_rt)

    # 3) cria novo access
    new_access = create_access_token(user.id)

    db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh_value,
        "token_type": "bearer"
    }


# ============================================================
# LOGOUT
# - revoga refresh token
# ============================================================
def logout(db: Session, refresh_token: str):
    rt = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not rt:
        # logout idempotente: não precisa “quebrar” se já não existe
        return {"message": "Logout ok"}

    rt.revoked = True
    db.commit()

    return {"message": "Logout ok"}
