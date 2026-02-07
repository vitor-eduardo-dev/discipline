from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from datetime import timedelta, datetime

from models import Habit, HabitLog
from models_auth import AuthUser

# funções do engine
from services.progress_engine import (
    get_today_summary,
    get_global_streaks,
    get_week_summary,
    get_user_achievements
)

# autenticação real
from dependencies.auth_user import get_current_user

# timezone Brasil
from services.timezone import now_brazil


router = APIRouter(prefix="/progress", tags=["Progress"])


# ============================================================
# 📌 ENDPOINT PRINCIPAL — PROGRESSO GLOBAL
# ============================================================
@router.get("/")
def get_full_progress(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    # IMPORTANTE: estas funções do progress_engine PRECISAM usar user.id / habits do user
    today_summary = get_today_summary(user, db)
    streaks = get_global_streaks(user, db)
    week = get_week_summary(user, db)
    achievements = get_user_achievements(user, db)

    return {
        "user": {
            "xp_total": user.xp_total,
            "level": user.level,
            "level_progress": user.level_progress
        },
        "today": today_summary,
        "streaks": streaks,
        "week_summary": week,
        "achievements": achievements
    }


# ============================================================
# 5.2 — MONTHLY OVERVIEW GLOBAL
# ============================================================
@router.get("/monthly-overview")
def monthly_overview(
    month: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    import calendar

    try:
        year, mon = map(int, month.split("-"))
    except:
        return {"error": "Formato inválido. Use YYYY-MM"}

    total_days = calendar.monthrange(year, mon)[1]

    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    habit_ids = [h.id for h in habits]
    total_habits = len(habits)

    if total_habits == 0:
        return {
            "month": month,
            "total_days": total_days,
            "perfect_days": 0,
            "days": [
                {"date": f"{year}-{mon:02d}-{d:02d}", "done": 0, "total": 0, "percent": 0}
                for d in range(1, total_days + 1)
            ]
        }

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.date.like(f"{month}-%")
    ).all()

    log_map = {f"{year}-{mon:02d}-{d:02d}": [] for d in range(1, total_days + 1)}
    for log in logs:
        if log.date in log_map:
            log_map[log.date].append(log)

    days_output = []
    perfect_days = 0

    for d in range(1, total_days + 1):
        ds = f"{year}-{mon:02d}-{d:02d}"
        logs_day = log_map[ds]

        done = len([l for l in logs_day if l.done])
        percent = (done / total_habits * 100) if total_habits else 0

        if total_habits > 0 and done == total_habits:
            perfect_days += 1

        days_output.append({
            "date": ds,
            "done": done,
            "total": total_habits,
            "percent": round(percent, 2)
        })

    return {
        "month": month,
        "total_days": total_days,
        "perfect_days": perfect_days,
        "days": days_output
    }


# ============================================================
# 5.3 — WEEKLY OVERVIEW GLOBAL
# ============================================================
@router.get("/weekly-overview")
def weekly_overview(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    today = now_brazil().date()
    start_date = today - timedelta(days=6)

    dates = [(start_date + timedelta(days=i)) for i in range(7)]

    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    habit_ids = [h.id for h in habits]
    total_habits = len(habits)

    if total_habits == 0:
        output = []
        for d in dates:
            ds = d.strftime("%Y-%m-%d")
            output.append({"date": ds, "done": 0, "total": 0, "percent": 0})
        return {
            "week_start": dates[0].strftime("%Y-%m-%d"),
            "week_end": dates[-1].strftime("%Y-%m-%d"),
            "total_habits": 0,
            "days": output,
            "perfect_days": 0,
            "week_completion_percent": 0
        }

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.date >= start_date.strftime("%Y-%m-%d")
    ).all()

    log_map = {d.strftime("%Y-%m-%d"): [] for d in dates}
    for log in logs:
        if log.date in log_map:
            log_map[log.date].append(log.done)

    output = []
    perfect_days = 0

    for d in dates:
        ds = d.strftime("%Y-%m-%d")
        values = log_map[ds]

        done = values.count(True)
        percent = (done / total_habits * 100) if total_habits else 0
        percent = round(percent, 2)

        if total_habits > 0 and done == total_habits:
            perfect_days += 1

        output.append({
            "date": ds,
            "done": done,
            "total": total_habits,
            "percent": percent
        })

    avg_percent = sum([d["percent"] for d in output]) / 7 if output else 0

    return {
        "week_start": dates[0].strftime("%Y-%m-%d"),
        "week_end": dates[-1].strftime("%Y-%m-%d"),
        "total_habits": total_habits,
        "days": output,
        "perfect_days": perfect_days,
        "week_completion_percent": round(avg_percent, 2)
    }


# ============================================================
# 5.4 — FULL HISTORY GLOBAL
# ============================================================
@router.get("/full-history")
def full_history(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    habit_ids = [h.id for h in habits]
    total_habits = len(habits)

    if total_habits == 0:
        return {
            "start": None,
            "end": None,
            "total_days": 0,
            "perfect_days": 0,
            "timeline": []
        }

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids)
    ).all()

    if not logs:
        return {
            "start": None,
            "end": None,
            "total_days": 0,
            "perfect_days": 0,
            "timeline": []
        }

    first_date = min(datetime.strptime(l.date, "%Y-%m-%d").date() for l in logs)
    last_date = now_brazil().date()

    delta = (last_date - first_date).days + 1
    dates = [first_date + timedelta(days=i) for i in range(delta)]

    log_map = {}
    for log in logs:
        log_map.setdefault(log.date, []).append(log.done)

    timeline = []
    perfect_days = 0

    for d in dates:
        ds = d.strftime("%Y-%m-%d")
        values = log_map.get(ds, [])

        done = values.count(True)
        percent = (done / total_habits * 100) if total_habits else 0
        percent = round(percent, 2)

        if done == total_habits and total_habits > 0:
            perfect_days += 1

        timeline.append({
            "date": ds,
            "done": done,
            "total": total_habits,
            "percent": percent
        })

    return {
        "start": first_date.strftime("%Y-%m-%d"),
        "end": last_date.strftime("%Y-%m-%d"),
        "total_days": len(timeline),
        "perfect_days": perfect_days,
        "timeline": timeline
    }


# ============================================================
# 5.5 — INSIGHTS AVANÇADOS
# ============================================================
@router.get("/insights")
def insights(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    from collections import defaultdict

    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    habit_ids = [h.id for h in habits]

    if not habits:
        return {"error": "Nenhum hábito encontrado"}

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids)
    ).all()

    # ---------------------------------------------------------
    # PREPARAÇÃO DE MAPAS
    # ---------------------------------------------------------
    logs_by_habit = defaultdict(list)
    logs_by_day = defaultdict(list)
    logs_last_30 = []

    today = now_brazil().date()
    last_30 = today - timedelta(days=30)

    for log in logs:
        logs_by_habit[log.habit_id].append(log)
        logs_by_day[log.date].append(log)

        d = datetime.strptime(log.date, "%Y-%m-%d").date()
        if d >= last_30:
            logs_last_30.append(log)

    # ---------------------------------------------------------
    # 1️⃣ CONSISTENCY SCORE
    # ---------------------------------------------------------
    if logs_last_30:
        done_30 = len([l for l in logs_last_30 if l.done])
        pct_30 = (done_30 / len(logs_last_30)) * 100
    else:
        pct_30 = 0

    avg_current_streak = sum(h.current_streak for h in habits) / len(habits)
    avg_best_streak = sum(h.best_streak for h in habits) / len(habits)

    streak_score = min((avg_current_streak / (avg_best_streak + 0.0001)) * 100, 100) if avg_best_streak else 0

    perfect_days = 0
    for d, logs_day in logs_by_day.items():
        total = len(logs_day)
        done = len([l for l in logs_day if l.done])
        if total > 0 and done == total:
            perfect_days += 1

    perfect_days_pct = min((perfect_days / 30) * 100, 100)

    consistency_score = round(
        (pct_30 * 0.5) + (streak_score * 0.3) + (perfect_days_pct * 0.2),
        2
    )

    # ---------------------------------------------------------
    # 2️⃣ MELHOR / PIOR DIA DA SEMANA
    # ---------------------------------------------------------
    week_map = defaultdict(lambda: {"done": 0, "total": 0})
    week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for d, logs_day in logs_by_day.items():
        dt = datetime.strptime(d, "%Y-%m-%d")
        weekday = dt.weekday()

        week_map[weekday]["total"] += len(logs_day)
        week_map[weekday]["done"] += len([l for l in logs_day if l.done])

    week_stats = []
    for wd in range(7):
        total = week_map[wd]["total"]
        done = week_map[wd]["done"]
        pct = (done / total * 100) if total else 0
        week_stats.append({"day": week_names[wd], "percent": round(pct, 2)})

    best_day = max(week_stats, key=lambda x: x["percent"])
    worst_day = min(week_stats, key=lambda x: x["percent"])

    # ---------------------------------------------------------
    # 3️⃣ HÁBITO MAIS FÁCIL / MAIS DIFÍCIL
    # ---------------------------------------------------------
    habit_performance = []

    for h in habits:
        logs_h = logs_by_habit[h.id]
        total = len(logs_h)
        done = len([l for l in logs_h if l.done])
        pct = (done / total * 100) if total else 0

        habit_performance.append({
            "id": h.id,
            "title": h.title,
            "percent": pct
        })

    easiest = max(habit_performance, key=lambda x: x["percent"])
    hardest = min(habit_performance, key=lambda x: x["percent"])

    # ---------------------------------------------------------
    # 4️⃣ ROLLING AVERAGE
    # ---------------------------------------------------------
    all_dates = sorted(logs_by_day.keys())
    rolling = []
    window = 7

    for i in range(len(all_dates)):
        slice_days = all_dates[max(0, i - window + 1): i + 1]

        done_count = sum(
            len([l for l in logs_by_day[d] if l.done])
            for d in slice_days
        )
        total_count = sum(len(logs_by_day[d]) for d in slice_days)

        pct = (done_count / total_count * 100) if total_count else 0

        rolling.append({
            "date": all_dates[i],
            "rolling_percent": round(pct, 2)
        })

    return {
        "consistency_score": consistency_score,
        "days_of_week": week_stats,
        "best_day": best_day,
        "worst_day": worst_day,
        "habit_difficulty": {
            "easiest": easiest,
            "hardest": hardest
        },
        "rolling_average": rolling,
        "streaks": {
            "average_current": round(avg_current_streak, 2),
            "average_best": round(avg_best_streak, 2)
        },
        "perfect_days_last_30": perfect_days,
        "completion_last_30_percent": round(pct_30, 2)
    }
