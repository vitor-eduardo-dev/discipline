def calculate_level(xp: int) -> int:
    """
    Retorna o nível baseado no XP total usando o modelo:
    xp_needed = 50 * (level^2)
    """
    level = 1
    while xp >= 50 * (level ** 2):
        level += 1
    return level


def xp_for_next_level(level: int) -> int:
    """
    XP necessário para o próximo level.
    """
    return 50 * (level ** 2)


def level_progress(xp: int):
    """
    Retorna:
    - nível atual
    - xp necessário para o próximo
    - percentual da barra
    """

    level = calculate_level(xp)
    next_xp = xp_for_next_level(level)

    # XP para o início do level atual
    prev_xp = 50 * ((level - 1) ** 2)

    # Progresso dentro do nível atual
    progress = xp - prev_xp
    progress_total = next_xp - prev_xp

    percent = (progress / progress_total * 100) if progress_total > 0 else 0

    return {
        "level": level,
        "current_xp": xp,
        "next_level_xp": next_xp,
        "progress_percent": round(percent, 2)
    }
