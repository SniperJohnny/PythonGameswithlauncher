import os

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
GRAVITY = 1.2
ANIMATION_DELAY = 3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_BASE = os.path.join(CURRENT_DIR, "..", "assets-time-shift-runner", "assets")
LEVEL_DIR = os.path.join(CURRENT_DIR, "levels")
SAVE_FILE = os.path.join(CURRENT_DIR, "save.json")
CONFIG_FILE = os.path.join(CURRENT_DIR, "config.json")
SCORE_FILE = os.path.join(CURRENT_DIR, "scores.json")

# --- NEW TIME MECHANIC SETTINGS ---
MAX_REWIND_FRAMES = 300  # kept frames before history is coarsened (covers >= 5 seconds)
REWIND_SPEED = 2         # How many frames to rewind per game tick