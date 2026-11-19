import json
import os

import pygame

from settings import WIDTH, HEIGHT, SCORE_FILE
from ui import Button, draw_text

MAX_SCORES = 5


def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {}
    try:
        with open(SCORE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def add_score(level, name, seconds):
    scores = load_scores()
    scores.setdefault(level, []).append({"name": name, "time": round(seconds, 2)})
    scores[level].sort(key=lambda entry: entry["time"])
    scores[level] = scores[level][:MAX_SCORES]
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)


def best_time(level):
    runs = load_scores().get(level)
    return runs[0]["time"] if runs else None


def format_time(seconds):
    return f"{seconds:.2f}s"


def name_entry(window, clock, seconds):
    """Returns the typed name, or None on quit."""
    name = ""
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_RETURN:
                return name.strip() or "Player"
            if event.key == pygame.K_BACKSPACE:
                name = name[:-1]
            elif event.unicode and event.unicode.isprintable() and len(name) < 12:
                name += event.unicode

        window.fill((16, 18, 30))
        draw_text(window, "LEVEL CLEARED", WIDTH // 2, 180, 56)
        draw_text(window, f"Time: {format_time(seconds)}", WIDTH // 2, 250, 32, (150, 200, 255))
        draw_text(window, "Enter your name", WIDTH // 2, 360, 26)

        box = pygame.Rect(0, 0, 340, 58)
        box.center = (WIDTH // 2, 420)
        pygame.draw.rect(window, (30, 34, 50), box, border_radius=8)
        pygame.draw.rect(window, (110, 140, 200), box, 2, border_radius=8)
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
        draw_text(window, name + cursor, box.centerx, box.centery, 32)

        draw_text(window, "ENTER to submit", WIDTH // 2, 510, 20, (130, 140, 160))
        pygame.display.update()


def show_leaderboard(window, clock, title, level):
    back = Button(WIDTH // 2 - 110, HEIGHT - 130, 220, 54, "Back")

    while True:
        clock.tick(60)
        back.hover = back.rect.collidepoint(pygame.mouse.get_pos())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return
            if back.handle(event):
                return

        window.fill((16, 18, 30))
        draw_text(window, "LEADERBOARD", WIDTH // 2, 120, 52)
        draw_text(window, title, WIDTH // 2, 185, 28, (150, 200, 255))

        runs = load_scores().get(level, [])
        if not runs:
            draw_text(window, "No runs yet", WIDTH // 2, 300, 28, (140, 150, 170))
        for i, entry in enumerate(runs):
            y = 260 + i * 50
            draw_text(window, f"{i + 1}. {entry['name']}", WIDTH // 2 - 130, y, 30, center=False)
            draw_text(window, format_time(entry["time"]), WIDTH // 2 + 150, y, 30, (150, 200, 255), center=False)

        back.draw(window)
        pygame.display.update()
