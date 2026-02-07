from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db

from models import Habit, HabitLog
from models_auth import AuthUser

from datetime import timedelta

# XP system
from services.xp_engine import get_level_from_xp

# Timezone Brasil
from services.timezone import today_brazil_str, now_brazil

# Auth
from dependencies.auth_user import get_current_user


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ============================================================
# DASHBOARD PRINCIPAL (AUTENTICADO)
# ============================================================
@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    today = today_brazil_str()

    # ===============================
    # 📌 LEVEL SYSTEM
    # ===============================
    level_info = get_level_from_xp(user.xp_total)

    # ===============================
    # 📌 HÁBITOS DO USUÁRIO
    # ===============================
    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    habit_ids = [h.id for h in habits]

    # ===============================
    # 📌 LOGS DO DIA (SÓ DO USUÁRIO)
    # ===============================
    logs_today = []
    if habit_ids:
        logs_today = db.query(HabitLog).filter(
            HabitLog.date == today,
            HabitLog.habit_id.in_(habit_ids)
        ).all()

    done_ids = {log.habit_id for log in logs_today if log.done}

    habits_data = []
    for h in habits:
        habits_data.append({
            "id": h.id,
            "title": h.title,
            "difficulty": h.difficulty,
            "importance": h.importance_weight,
            "frequency_per_week": h.frequency_per_week,
            "habit_xp": h.xp,
            "done_today": h.id in done_ids,
            "current_streak": h.current_streak,
            "best_streak": h.best_streak,
        })

    # ===============================
    # 📌 ESTATÍSTICAS DO DIA
    # ===============================
    total_habits = len(habits)
    done_today = len(done_ids)
    percent_today = (done_today / total_habits * 100) if total_habits > 0 else 0

    # ===============================
    # 📌 WEEK SUMMARY (SÓ DO USUÁRIO)
    # ===============================
    today_date = now_brazil().date()
    start_date = today_date - timedelta(days=6)
    dates = [(start_date + timedelta(days=i)) for i in range(7)]

    logs_week = []
    if habit_ids:
        logs_week = db.query(HabitLog).filter(
            HabitLog.date >= start_date.strftime("%Y-%m-%d"),
            HabitLog.habit_id.in_(habit_ids)
        ).all()

    # organiza por dia: "YYYY-MM-DD" -> [True/False...]
    day_map = {d.strftime("%Y-%m-%d"): [] for d in dates}
    for log in logs_week:
        if log.date in day_map:
            day_map[log.date].append(log.done)

    week_summary = []
    for d in dates:
        ds = d.strftime("%Y-%m-%d")
        values = day_map[ds]
        percent = (values.count(True) / len(values) * 100) if values else 0

        week_summary.append({
            "date": ds,
            "percent": round(percent, 2)
        })

    # ===============================
    # 📌 RETORNO FINAL
    # ===============================
    return {
        "user": {
            "xp_total": user.xp_total,
            "level": level_info["level"],
            "level_progress": level_info["progress"],
            "next_level_xp": level_info["next_level_xp"]
        },
        "today": {
            "date": today,
            "total_habits": total_habits,
            "done_today": done_today,
            "percent": round(percent_today, 2)
        },
        "habits": habits_data,
        "week_summary": week_summary,
        "achievements": []
    }


# ============================================================
# 5.1 — WEEKLY OVERVIEW GLOBAL (AUTENTICADO)
# ============================================================
@router.get("/weekly-overview")
def weekly_overview(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    total_habits = len(habits)
    habit_ids = [h.id for h in habits]

    today = now_brazil().date()
    output = []

    # se não tem hábitos, devolve semana zerada
    if total_habits == 0:
        for i in range(7):
            day = today - timedelta(days=i)
            ds = day.strftime("%Y-%m-%d")
            output.append({"date": ds, "done": 0, "total": 0, "percent": 0})
        output.reverse()
        return output

    for i in range(7):
        day = today - timedelta(days=i)
        ds = day.strftime("%Y-%m-%d")

        logs_day = db.query(HabitLog).filter(
            HabitLog.date == ds,
            HabitLog.habit_id.in_(habit_ids)
        ).all()

        done_day = len([l for l in logs_day if l.done])
        percent = (done_day / total_habits * 100) if total_habits else 0

        output.append({
            "date": ds,
            "done": done_day,
            "total": total_habits,
            "percent": round(percent, 2)
        })

    output.reverse()
    return output
