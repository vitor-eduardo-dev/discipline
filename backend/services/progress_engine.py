from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import Habit, HabitLog, UserAchievement

# timezone Brasil (consistente com o resto do projeto)
from services.timezone import today_brazil_str, now_brazil


# ============================================================
# 📌 RESUMO DO DIA
# ============================================================
def get_today_summary(user, db: Session):
    today = today_brazil_str()

    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    total = len(habits)

    if total == 0:
        return {
            "date": today,
            "total_habits": 0,
            "done_today": 0,
            "percent": 0
        }

    habit_ids = [h.id for h in habits]

    done = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.date == today,
        HabitLog.done == True
    ).count()

    percent = round((done / total) * 100, 2)

    return {
        "date": today,
        "total_habits": total,
        "done_today": done,
        "percent": percent
    }


# ============================================================
# 📌 STREAKS GLOBAIS
# ============================================================
def get_global_streaks(user, db: Session):
    habits = db.query(Habit).filter(Habit.user_id == user.id).all()

    if not habits:
        return {
            "best_global_streak": 0,
            "average_streak": 0,
            "top_habits": []
        }

    streaks = [h.current_streak for h in habits]

    best_streak = max(streaks)
    avg_streak = round(sum(streaks) / len(streaks), 2)

    top = sorted(
        [{"title": h.title, "streak": h.current_streak} for h in habits],
        key=lambda x: x["streak"],
        reverse=True
    )[:3]

    return {
        "best_global_streak": best_streak,
        "average_streak": avg_streak,
        "top_habits": top
    }


# ============================================================
# 📌 RESUMO DOS ÚLTIMOS 7 DIAS
# ============================================================
def get_week_summary(user, db: Session):
    today = now_brazil().date()
    result = []

    habits = db.query(Habit).filter(Habit.user_id == user.id).all()
    if not habits:
        return []

    habit_ids = [h.id for h in habits]
    total = len(habits)

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")

        logs = db.query(HabitLog).filter(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.date == day_str
        ).all()

        done = sum(1 for log in logs if log.done)

        percent = round((done / total) * 100, 2) if total > 0 else 0

        result.append({
            "date": day_str,
            "percent": percent
        })

    return result


# ============================================================
# 📌 LISTA DE CONQUISTAS JÁ DESBLOQUEADAS
# ============================================================
def get_user_achievements(user, db: Session):
    achs = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()

    return [
        {
            "id": a.achievement.id,
            "name": a.achievement.name,
            "description": a.achievement.description,
            "icon": a.achievement.icon,
            "unlocked_at": a.unlocked_at
        }
        for a in achs
    ]
