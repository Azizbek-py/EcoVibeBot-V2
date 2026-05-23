# Daraja tizimi

LEVELS = [
    (0,    "Askar 🪖"),
    (50,   "Serjant ⚔️"),
    (100,  "Leytenant 🎯"),
    (150,  "Kapitan 🛡"),
    (200,  "Mayor 🔥"),
    (250,  "Polkovnik 👑"),
    (300,  "Imperator 🏆"),
]


def get_level(score: float) -> str:
    """Balga qarab unvon qaytaradi."""
    level = LEVELS[0][1]
    for min_score, name in LEVELS:
        if score >= min_score:
            level = name
    return level


def get_next_level(score: float):
    """Keyingi daraja va qancha ball qolganligi. (next_name, balls_needed) yoki None."""
    for i, (min_score, name) in enumerate(LEVELS):
        if score < min_score:
            return name, min_score - score
    return None, 0  # eng yuqori daraja
