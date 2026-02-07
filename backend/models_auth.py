from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


# ============================================================
# USER ACCOUNT (Expandido — Agora substitui User completamente)
# ============================================================
class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(String, primary_key=True, default=generate_uuid)

    # Dados do login
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Ativação
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ============================================================
    # CAMPOS DO SISTEMA DE PROGRESSO (ANTES NO MODEL User)
    # ============================================================
    xp_total = Column(Integer, default=0)
    level = Column(Integer, default=1)
    level_progress = Column(Float, default=0.0)

    # ============================================================
    # RELACIONAMENTOS
    # ============================================================
    sessions = relationship("RefreshToken", back_populates="user", cascade="all, delete")

    # Agora substitui o User antigo
    habits = relationship("Habit", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")


# ============================================================
# REFRESH TOKEN (Seguro + Revogável)
# ============================================================
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=generate_uuid)

    token = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey("auth_users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    revoked = Column(Boolean, default=False)

    user = relationship("AuthUser", back_populates="sessions")
