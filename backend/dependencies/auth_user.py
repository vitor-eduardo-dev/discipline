from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from services.jwt_token import decode_token
from models_auth import AuthUser

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials  # <- JWT puro (sem "Bearer ")

    payload = decode_token(token)

    # opcional, mas recomendado:
    if payload.get("type") != "access":
        raise HTTPException(401, "Token inválido (não é access)")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token inválido (sem sub)")

    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if not user:
        raise HTTPException(401, "Usuário não encontrado")

    return user
