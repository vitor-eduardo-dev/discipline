# services/xp_engine.py

import math

# ============================================================
# XP POR HÁBITO
# ============================================================

def calculate_xp_for_habit(
    difficulty: str,
    importance: int,
    frequency_per_week: int,
    done: bool = True
) -> int:
    """
    Calcula o XP ganho ou perdido ao concluir/desmarcar um hábito.

    Fórmula base do XP:
        XP = 10 * D * I * (7 / F)

    Onde:
        D  → multiplicador de dificuldade
        I  → importância (1 a 5)
        F  → frequência semanal (1 a 7)

    Se done=False → retorna XP negativo com penalidade reduzida.
    """

    difficulty_map = {
        "easy": 0.8,
        "medium": 1.0,
        "hard": 1.3
    }

    # Validações
    D = difficulty_map.get(difficulty, 1.0)
    I = max(1, min(int(importance), 5))
    F = max(1, min(int(frequency_per_week), 7))

    # XP base
    xp = 10 * D * I * (7 / F)

    # Se foi desmarcado → XP negativo
    if not done:
        xp = -(xp * 0.6)  # penalidade 40%

    return int(round(xp))


# ============================================================
# SISTEMA DE LEVEL
# ============================================================

def xp_required_for_level(level: int) -> int:
    """
    XP necessário para *atingir* o nível `level`.

    Regra:
      - Level 1 = 0 XP
      - Level 2 = 50 XP
      - Level 3 = 200 XP
      - ...

    Fórmula (quadrática):
      XP(level) = 50 * (level - 1)^2
    """
    level = max(1, int(level))
    return 50 * ((level - 1) ** 2)


def get_level_from_xp(total_xp: int) -> dict:
    """
    Retorna:
      - nível atual
      - XP necessário para próximo nível
      - progresso (0 a 1)
    """
    total_xp = int(total_xp or 0)
    if total_xp < 0:
        total_xp = 0

    # Descobre nível atual (nível mais alto cujo requisito <= total_xp)
    level = 1
    while total_xp >= xp_required_for_level(level + 1):
        level += 1

    xp_current = xp_required_for_level(level)
    xp_next = xp_required_for_level(level + 1)

    denom = xp_next - xp_current
    if denom <= 0:
        progress = 1.0
    else:
        progress = (total_xp - xp_current) / denom
        progress = max(0.0, min(progress, 1.0))

    return {
        "level": level,
        "next_level_xp": xp_next,
        "progress": round(progress, 4)
    }


# ============================================================
# APLICA XP E ATUALIZA O USER
# ============================================================

def apply_xp_gain(user, habit, db, done=True):
    """
    Aplica XP ao usuário com base no hábito.
    Se done=False → remove XP proporcional.
    """

    gained_xp = calculate_xp_for_habit(
        difficulty=habit.difficulty,
        importance=habit.importance_weight,
        frequency_per_week=habit.frequency_per_week,
        done=done
    )

    user.xp_total = int(user.xp_total or 0) + gained_xp
    if user.xp_total < 0:
        user.xp_total = 0

    level_info = get_level_from_xp(user.xp_total)

    # (Opcional) se você quiser sincronizar no banco:
    user.level = level_info["level"]
    user.level_progress = level_info["progress"]

    db.commit()
    try:
        db.refresh(user)
    except:
        pass

    return {
        "gained_xp": gained_xp,
        "total_xp": user.xp_total,
        "level": level_info["level"],
        "level_progress": level_info["progress"],
        "next_level_xp": level_info["next_level_xp"]
    }
