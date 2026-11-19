import json
import os

from settings import CONFIG_FILE

DEFAULTS = {
    "player_speed": 5,
    "rewind_speed": 2,
    "max_health": 3,
    "damage_model": "Hearts",
    "screen_shake": True,
}

OPTIONS = [
    ("Move speed", "player_speed", 3, 10),
    ("Rewind speed", "rewind_speed", 1, 6),
    ("Max health", "max_health", 1, 6),
    ("Damage model", "damage_model", ("Hearts", "One Hit"), None),
    ("Screen shake", "screen_shake", False, True),
]

CONFIG = dict(DEFAULTS)


def load():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                CONFIG.update(json.load(f))
        except (OSError, ValueError):
            pass
    return CONFIG


def save():
    with open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG, f, indent=2)


def adjust(key, step, low, high):
    value = CONFIG[key]
    if isinstance(value, bool):
        CONFIG[key] = not value
    elif isinstance(value, str):
        CONFIG[key] = low[(low.index(value) + step) % len(low)]
    else:
        CONFIG[key] = max(low, min(high, value + step))
    save()


def value_text(key):
    value = CONFIG[key]
    if value is True:
        return "On"
    if value is False:
        return "Off"
    return str(value)
