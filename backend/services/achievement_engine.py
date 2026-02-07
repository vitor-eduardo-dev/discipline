from models import Achievement, UserAchievement
from sqlalchemy.orm import Session


DEFAULT_ACHIEVEMENTS = [
    {
        "name": "Primeiro Passo",
        "description": "Conclua seu primeiro hábito.",
        "icon": "🚀",
        "condition_type": "habit_completion",
        "condition_value": 1
    },
    {
        "name": "Disciplina 7 Dias",
        "description": "Mantenha um streak de 7 dias seguidos.",
        "icon": "🔥",
        "condition_type": "streak",
        "condition_value": 7
    },
    {
        "name": "Nível 5",
        "description": "Alcance o nível 5.",
        "icon": "🎖️",
        "condition_type": "xp_total",
        "condition_value": 250
    },
    {
        "name": "Dia Perfeito",
        "description": "Complete 100% dos hábitos do dia.",
        "icon": "🌟",
        "condition_type": "perfect_day",
        "condition_value": 1
    }
]


def create_default_achievements(db: Session):

    # Se já existem conquistas, não cria novamente
    if db.query(Achievement).count() > 0:
        return

    # Criar conquistas padrão
    for item in DEFAULT_ACHIEVEMENTS:
        db.add(Achievement(
            name=item["name"],
            description=item["description"],
            icon=item["icon"],
            condition_type=item["condition_type"],
            condition_value=item["condition_value"]
        ))

    db.commit()


def check_achievements(user, streak, habits_completed_today, perfect_day, db: Session):

    unlocked = []

    all_achs = db.query(Achievement).all()
    user_achs = {ua.achievement_id for ua in user.achievements}

    for ach in all_achs:

        # já desbloqueou?
        if ach.id in user_achs:
            continue

        unlock = False

        # regras de desbloqueio
        if ach.condition_type == "streak" and streak >= ach.condition_value:
            unlock = True

        elif ach.condition_type == "habit_completion" and habits_completed_today >= ach.condition_value:
            unlock = True

        elif ach.condition_type == "xp_total" and user.xp_total >= ach.condition_value:
            unlock = True

        elif ach.condition_type == "perfect_day" and perfect_day:
            unlock = True

        if unlock:
            db.add(UserAchievement(
                user_id=user.id,
                achievement_id=ach.id
            ))
            unlocked.append(ach.name)

    db.commit()
    return unlocked
