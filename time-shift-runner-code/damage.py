"""Damage models. "Hearts" loses health per hazard, "One Hit" dies instantly."""
from config import CONFIG


def start_health():
    return CONFIG["max_health"] if CONFIG["damage_model"] == "Hearts" else 1


def apply_hit(health, hazard):
    if CONFIG["damage_model"] != "Hearts":
        return 0
    return health - (hazard.damage if hazard is not None else 1)
