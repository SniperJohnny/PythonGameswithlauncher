import json
import os

import pygame

import config
import scores
from settings import WIDTH, HEIGHT, FPS, SAVE_FILE
from levels import LEVELS
from ui import Button, draw_text


def load_progress():
    """Number of levels finished so far."""
    if not os.path.exists(SAVE_FILE):
        return 0
    try:
        with open(SAVE_FILE) as f:
            return json.load(f)["completed"]
    except (OSError, ValueError, KeyError):
        return 0


def save_progress(completed):
    with open(SAVE_FILE, "w") as f:
        json.dump({"completed": completed}, f)


def _paint(window, title, subtitle=""):
    window.fill((16, 18, 30))
    draw_text(window, title, WIDTH // 2, 130, 60)
    if subtitle:
        draw_text(window, subtitle, WIDTH // 2, 195, 24, (140, 155, 180))


def _button_menu(window, clock, title, entries, subtitle=""):
    """entries: (label, enabled). Returns clicked index, None on ESC, -1 on quit."""
    buttons = [Button(WIDTH // 2 - 280, 300 + i * 72, 560, 56, label, 24, enabled)
               for i, (label, enabled) in enumerate(entries)]

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()
        for button in buttons:
            button.hover = button.rect.collidepoint(mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return -1
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            for index, button in enumerate(buttons):
                if button.handle(event):
                    return index

        _paint(window, title, subtitle)
        for button in buttons:
            button.draw(window)
        pygame.display.update()


def settings_screen(window, clock):
    top = 250
    minus = [Button(WIDTH // 2 + 45, top + i * 80, 48, 44, "-", 30) for i in range(len(config.OPTIONS))]
    plus = [Button(WIDTH // 2 + 205, top + i * 80, 48, 44, "+", 30) for i in range(len(config.OPTIONS))]
    back = Button(WIDTH // 2 - 110, HEIGHT - 120, 220, 54, "Back")

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()
        for button in [back] + minus + plus:
            button.hover = button.rect.collidepoint(mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if back.handle(event):
                return
            for i, (_, key, low, high) in enumerate(config.OPTIONS):
                if minus[i].handle(event):
                    config.adjust(key, -1, low, high)
                if plus[i].handle(event):
                    config.adjust(key, 1, low, high)

        _paint(window, "SETTINGS", "ESC to go back")
        for i, (label, key, low, high) in enumerate(config.OPTIONS):
            y = top + i * 80
            draw_text(window, label, 160, y + 8, 30, center=False)
            draw_text(window, config.value_text(key), WIDTH // 2 + 150, y + 22, 28)

        for button in minus + plus + [back]:
            button.draw(window)
        pygame.display.update()


def level_select(window, clock):
    completed = load_progress()
    entries = []
    for level in LEVELS:
        label = level.title
        best = scores.best_time(level.key)
        if best is not None:
            label += f"   best {best:.2f}s"
        unlocked = level.number <= completed + 1
        if not unlocked:
            label += "   [locked]"
        entries.append((label, unlocked))

    choice = _button_menu(window, clock, "LEVEL SELECT", entries, "ESC to go back")
    if choice is None or choice == -1:
        return choice
    return LEVELS[choice]


def run_menu(window, clock):
    """Returns the level to play, or None to quit."""
    while True:
        choice = _button_menu(window, clock, "TIME-SHIFT RUNNER", [
            ("Start Game", True),
            ("Level Select", True),
            ("Settings", True),
            ("Quit", True),
        ])

        if choice is None or choice == -1 or choice == 3:
            return None
        if choice == 2:
            settings_screen(window, clock)
        elif choice == 0:
            return LEVELS[min(load_progress(), len(LEVELS) - 1)]
        else:
            level = level_select(window, clock)
            if level == -1:
                return None
            if level:
                return level
