# services/streak_engine.py

from datetime import datetime, timedelta

def update_streak(habit, done_today: bool) -> None:
    """
    Atualiza o streak corretamente baseado na última data registrada.
    - Se for o primeiro dia → streak = 1
    - Se completou ontem → streak += 1
    - Se completou hoje de novo → streak não muda
    - Se quebrou mais de 1 dia → streak = 1
    """

    today = datetime.utcnow().date()

    # Se não marcou como feito → não faz nada
    if not done_today:
        return

    # Se nunca teve streak antes
    if not habit.last_done_date:
        habit.current_streak = 1
        habit.best_streak = max(habit.best_streak, habit.current_streak)
        habit.last_done_date = today.strftime("%Y-%m-%d")
        return

    last_date = datetime.strptime(habit.last_done_date, "%Y-%m-%d").date()

    # Se marcou no mesmo dia → não aumenta streak
    if last_date == today:
        return

    # Se completou ontem → incrementa
    if today - last_date == timedelta(days=1):
        habit.current_streak += 1

    # Se completou depois de vários dias → reset
    else:
        habit.current_streak = 1

    # Atualiza best streak
    habit.best_streak = max(habit.best_streak, habit.current_streak)

    # Atualiza a última data
    habit.last_done_date = today.strftime("%Y-%m-%d")
