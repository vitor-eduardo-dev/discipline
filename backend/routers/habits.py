from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from schemas import HabitCreate, HabitOut
from models import Habit, HabitLog
from models_auth import AuthUser  # << NOVO

from datetime import datetime, timedelta

# Serviços
from services.xp_engine import calculate_xp_for_habit, apply_xp_gain
from services.streak_engine import update_streak
from services.achievement_engine import check_achievements
from services.level_engine import level_progress, calculate_level

# Timezone Brasil
from services.timezone import today_brazil_str, now_brazil

# Auth
from dependencies.auth_user import get_current_user


router = APIRouter(prefix="/habits", tags=["Habits"])


# ============================================================
# 1) CRIAR HÁBITO  (AGORA AUTENTICADO)
# ============================================================
@router.post("/")
def create_habit(
    data: HabitCreate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)  # << AQUI!
):
    new_habit = Habit(
        title=data.title,
        user_id=user.id,  # << AGORA VEM DO JWT
        difficulty=data.difficulty,
        importance_weight=data.importance,
        frequency_per_week=data.frequency
    )

    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)

    return {
        "message": "Hábito criado",
        "id": new_habit.id,
        "difficulty": new_habit.difficulty,
        "importance": new_habit.importance_weight,
        "frequency": new_habit.frequency_per_week
    }


# ============================================================
# 2) LISTAR HÁBITOS
# ============================================================
@router.get("/", response_model=list[HabitOut])
def list_habits(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    return db.query(Habit).filter(Habit.user_id == user.id).all()


# ============================================================
# 3) MARCAR / DESMARCAR HÁBITO
# ============================================================
@router.post("/{habit_id}/toggle")
def toggle_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    today = today_brazil_str()

    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user.id
    ).first()

    if not habit:
        raise HTTPException(404, "Hábito não encontrado")

    # LOG DO DIA
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit.id,
        HabitLog.date == today
    ).first()

    # ❌ DESMARCAR
    if log and log.done:
        log.done = False

        xp_change = calculate_xp_for_habit(
            habit.difficulty, habit.importance_weight, habit.frequency_per_week
        )

        habit.xp = max(0, habit.xp - xp_change)

        update_streak(habit, done_today=False)

        db.commit()

        return {
            "done": False,
            "xp_lost": xp_change,
            "habit_xp": habit.xp,
            "current_streak": habit.current_streak,
            "best_streak": habit.best_streak,
            "global_xp": user.xp_total,
            "level": user.level,
            "level_progress": user.level_progress
        }

    # ✅ MARCAR COMO FEITO
    if not log:
        log = HabitLog(
            habit_id=habit_id,
            date=today,
            done=True
        )
        db.add(log)
    else:
        log.done = True

    xp_change = calculate_xp_for_habit(
        habit.difficulty, habit.importance_weight, habit.frequency_per_week
    )

    habit.xp += xp_change

    update_streak(habit, done_today=True)

    xp_data = apply_xp_gain(user, habit, db)

    db.commit()

    return {
        "done": True,
        "xp_gained": xp_change,
        "habit_xp": habit.xp,
        "current_streak": habit.current_streak,
        "best_streak": habit.best_streak,
        "global_xp": xp_data["total_xp"],
        "level": xp_data["level"],
        "level_progress": xp_data["level_progress"],
        "next_level_xp": xp_data["next_level_xp"]
    }


# ============================================================
# 4) ESTATÍSTICAS DO HÁBITO
# ============================================================
@router.get("/{habit_id}/stats")
def habit_stats(
    habit_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user.id
    ).first()

    if not habit:
        raise HTTPException(404, "Hábito não encontrado")

    logs = db.query(HabitLog).filter(HabitLog.habit_id == habit.id).all()

    total_logs = len(logs)
    done_logs = len([l for l in logs if l.done])
    adherence = (done_logs / total_logs * 100) if total_logs else 0

    return {
        "habit_id": habit.id,
        "title": habit.title,
        "current_streak": habit.current_streak,
        "best_streak": habit.best_streak,
        "total_logs": total_logs,
        "done_logs": done_logs,
        "adherence_percent": round(adherence, 2),
        "history": [{"date": l.date, "done": l.done} for l in logs]
    }


# ============================================================
# 5) HISTÓRICO COMPACTO POR MÊS
# ============================================================
@router.get("/{habit_id}/history")
def habit_history(
    habit_id: str,
    month: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    try:
        year, mon = map(int, month.split("-"))
    except:
        raise HTTPException(400, "Formato inválido. Use YYYY-MM")

    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user.id
    ).first()

    if not habit:
        raise HTTPException(404, "Hábito não encontrado")

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date.like(f"{month}-%")
    ).all()

    total_logs = len(logs)
    done_logs = len([l for l in logs if l.done])

    percent = (done_logs / total_logs * 100) if total_logs else 0

    return {
        "habit_id": habit.id,
        "title": habit.title,
        "month": month,
        "days_total": total_logs,
        "days_done": done_logs,
        "percent": round(percent, 2),
        "history": [{"date": l.date, "done": l.done} for l in logs]
    }


# ============================================================
# 6) WEEKLY TREND
# ============================================================
@router.get("/{habit_id}/weekly-trend")
def weekly_trend(
    habit_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user.id
    ).first()

    if not habit:
        raise HTTPException(404, "Hábito não encontrado")

    today = now_brazil().date()
    week_data = []

    for i in range(7):
        day = today - timedelta(days=i)
        logs = db.query(HabitLog).filter(
            HabitLog.habit_id == habit.id,
            HabitLog.date == day.strftime("%Y-%m-%d")
        ).first()

        week_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "done": bool(logs and logs.done)
        })

    week_data.reverse()

    return week_data


# ============================================================
# 7) DAILY SUMMARY
# ============================================================
@router.get("/daily-summary")
def daily_summary(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    today = today_brazil_str()

    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    logs_today = db.query(HabitLog).filter(HabitLog.date == today).all()

    done_ids = {l.habit_id for l in logs_today if l.done}

    return {
        "date": today,
        "total_habits": len(habits),
        "done_today": len(done_ids),
        "percent": round((len(done_ids) / len(habits) * 100) if habits else 0, 2),
        "details": [{
            "id": h.id,
            "title": h.title,
            "done": h.id in done_ids
        } for h in habits]
    }


# ============================================================
# 8) MONTHLY CALENDAR
# ============================================================
@router.get("/{habit_id}/monthly-chart")
def monthly_chart(
    habit_id: str,
    month: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    import calendar

    try:
        year, mon = map(int, month.split("-"))
    except:
        raise HTTPException(400, "Formato inválido")

    days = calendar.monthrange(year, mon)[1]

    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user.id
    ).first()

    if not habit:
        raise HTTPException(404, "Hábito não encontrado")

    dates = [f"{year}-{mon:02d}-{d:02d}" for d in range(1, days + 1)]

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id == habit.id,
        HabitLog.date.like(f"{month}-%")
    ).all()

    log_map = {l.date: l.done for l in logs}

    calendar_list = [{"date": d, "done": log_map.get(d, False)} for d in dates]

    return {
        "habit_id": habit.id,
        "title": habit.title,
        "month": month,
        "days": days,
        "calendar": calendar_list
    }


# ============================================================
# 9) ANALYTICS AVANÇADO
# ============================================================
@router.get("/{habit_id}/analytics")
def habit_analytics(
    habit_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user.id
    ).first()

    if not habit:
        raise HTTPException(404, "Hábito não encontrado")

    logs = db.query(HabitLog).filter(HabitLog.habit_id == habit.id).all()

    total_logs = len(logs)
    done_logs = len([l for l in logs if l.done])
    adherence = (done_logs / total_logs * 100) if total_logs else 0

    today = now_brazil().date()
    last_30 = today - timedelta(days=30)

    logs_30 = [
        {"date": l.date, "done": l.done}
        for l in logs
        if datetime.strptime(l.date, "%Y-%m-%d").date() >= last_30
    ]

    sorted_logs = sorted(
        logs, key=lambda l: datetime.strptime(l.date, "%Y-%m-%d"), reverse=True
    )

    streak_done = 0
    streak_failed = 0

    for l in sorted_logs:
        if l.done:
            streak_done += 1
        else:
            break

    for l in sorted_logs:
        if not l.done:
            streak_failed += 1
        else:
            break

    return {
        "habit": {
            "id": habit.id,
            "title": habit.title,
            "created_at": habit.created_at,
            "current_streak": habit.current_streak,
            "best_streak": habit.best_streak,
            "total_logs": total_logs,
            "done_logs": done_logs,
            "adherence_percent": round(adherence, 2),
        },
        "last_30_days": logs_30,
        "week_stats": {
            "done": streak_done,
            "failed": streak_failed
        },
        "common_completion_time": None
    }

