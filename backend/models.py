from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from models_auth import AuthUser  # garante que o mapper exista

import uuid


def generate_uuid():
    return str(uuid.uuid4())


# ============================================================
# HABIT
# ============================================================
class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, default=generate_uuid)

    # AuthUser.id é String (uuid) -> aqui também tem que ser String
    user_id = Column(String, ForeignKey("auth_users.id"), nullable=False)

    title = Column(String, nullable=False)

    difficulty = Column(String, default="easy")  # easy / medium / hard
    importance_weight = Column(Integer, default=1)
    frequency_per_week = Column(Integer, default=1)

    xp = Column(Integer, default=0)

    # STREAKS
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)

    last_done_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # RELACIONAMENTOS
    user = relationship("AuthUser", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")


# ============================================================
# HABIT LOG
# ============================================================
class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    date = Column(String)
    done = Column(Boolean, default=False)

    habit_id = Column(String, ForeignKey("habits.id"), nullable=False)
    habit = relationship("Habit", back_populates="logs")


# ============================================================
# ACHIEVEMENT
# ============================================================
class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, nullable=True)

    # tipo da condição: xp_total, streak, habits_completed, perfect_day, etc.
    condition_type = Column(String, nullable=False)

    # valor necessário (ex: 7 dias, 500 XP, 5 hábitos…)
    condition_value = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


# ============================================================
# USER ↔ ACHIEVEMENT
# ============================================================
class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(String, primary_key=True, default=generate_uuid)

    # AuthUser.id é String (uuid) -> aqui também tem que ser String
    user_id = Column(String, ForeignKey("auth_users.id"), nullable=False)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False)

    unlocked_at = Column(DateTime, default=datetime.utcnow)

    # RELACIONAMENTOS
    user = relationship("AuthUser", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="users")
