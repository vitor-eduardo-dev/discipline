# services/jwt_token.py
import os
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

# ============================================================
# CONFIG (use .env em produção)
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_EXPIRE_MINUTES = int(os.getenv("ACCESS_EXPIRE_MINUTES", "30"))
REFRESH_EXPIRE_DAYS = int(os.getenv("REFRESH_EXPIRE_DAYS", "30"))


def _utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# ACCESS TOKEN (JWT)
# ============================================================
def create_access_token(user_id: str):
    expire = _utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": _utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ============================================================
# REFRESH TOKEN (string aleatória)
# ============================================================
def create_refresh_token():
    return str(uuid.uuid4())


# ============================================================
# DECODE + VALIDATE
# ============================================================
def decode_token(token: str, expected_type: str = "access"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(401, f"Token inválido (type={token_type})")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido")
