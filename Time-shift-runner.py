import json
import math
import random

import pygame

CELL = 30
COLS, ROWS = 10, 20
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
WIDTH, HEIGHT = 500, 600
LEADERBOARD_FILE = "leaderboard.json"
CLEAR_TIME = 0.4

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (70, 70, 80)
ACCENT = (0, 200, 255)
GOLD = (255, 220, 0)
RED = (255, 80, 80)
MUTED = (150, 150, 170)
MENU_BG = (15, 15, 25)
PANEL_BG = (30, 30, 40)
GRID_LINE = (40, 40, 50)

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}
COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 220, 0),
    "Z": (240, 0, 0),
    "J": (30, 60, 255),
    "L": (255, 150, 0),
}
LINE_POINTS = {1: 100, 2: 300, 3: 500, 4: 800}
LINE_NAMES = {1: "SINGLE", 2: "DOUBLE", 3: "TRIPLE", 4: "TETRIS!"}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()
small_font = pygame.font.Font(None, 22)
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 48)
title_font = pygame.font.Font(None, 90)


def cells(shape, x, y):
    for row_index, row in enumerate(shape):
        for col_index, filled in enumerate(row):
            if filled:
                yield x + col_index, y + row_index


def rotated(shape):
    # rotate 90 degrees clockwise
    return [list(row) for row in zip(*shape[::-1])]


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-120, 120)
        self.vy = random.uniform(-250, -50)
        self.color = color
        self.life = 1.0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 600 * dt
        self.life -= dt * 1.5

    def draw(self, surface):
        size = max(1, int(5 * self.life))
        pygame.draw.rect(surface, self.color, (self.x, self.y, size, size))


class Game:
    def __init__(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.bag = []
        self.next = Piece(self.next_kind())
        self.hold_kind = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.fall_timer = 0
        self.held_dir = 0
        self.repeat_timer = 0
        self.clearing = []
        self.clear_timer = 0
        self.particles = []
        self.popup = None
        self.shake = 0
        self.over = False
        self.spawn()

    @property
    def level(self):
        return self.lines // 10 + 1

    @property
    def playing(self):
        return not self.over and not self.clearing

    def next_kind(self):
        # 7-bag: every piece appears once before any repeats
        if not self.bag:
            self.bag = list(SHAPES)
            random.shuffle(self.bag)
        return self.bag.pop()

    def take_next(self):
        piece, self.next = self.next, Piece(self.next_kind())
        return piece

    def spawn(self):
        self.piece = self.take_next()
        self.can_hold = True
        if not self.fits(self.piece.shape, self.piece.x, self.piece.y):
            self.over = True

    def fits(self, shape, x, y):
        for cx, cy in cells(shape, x, y):
            if cx < 0 or cx >= COLS or cy >= ROWS or self.board[cy][cx]:
                return False
        return True

    def move(self, dx):
        if self.fits(self.piece.shape, self.piece.x + dx, self.piece.y):
            self.piece.x += dx

    def rotate(self):
        shape = rotated(self.piece.shape)
        for kick in (0, -1, 1, -2, 2):
            if self.fits(shape, self.piece.x + kick, self.piece.y):
                self.piece.shape = shape
                self.piece.x += kick
                return

    def swap_hold(self):
        if not self.can_hold:
            return
        kind = self.piece.kind
        self.piece = Piece(self.hold_kind) if self.hold_kind else self.take_next()
        self.hold_kind = kind
        self.can_hold = False

    def ghost_y(self):
        y = self.piece.y
        while self.fits(self.piece.shape, self.piece.x, y + 1):
            y += 1
        return y

    def step_down(self):
        if self.fits(self.piece.shape, self.piece.x, self.piece.y + 1):
            self.piece.y += 1
            return True
        self.lock()
        return False

    def hard_drop(self):
        start = self.piece.y
        self.piece.y = self.ghost_y()
        self.score += 2 * (self.piece.y - start)
        self.shake = 0.15
        for cx, cy in cells(self.piece.shape, self.piece.x, self.piece.y):
            self.burst(cx * CELL + CELL // 2, (cy + 1) * CELL, COLORS[self.piece.kind], 3)
        self.lock()

    def lock(self):
        for cx, cy in cells(self.piece.shape, self.piece.x, self.piece.y):
            self.board[cy][cx] = self.piece.kind
        self.piece = None
        full = [r for r, row in enumerate(self.board) if all(row)]
        if not full:
            self.spawn()
            return
        self.clearing = full
        self.clear_timer = CLEAR_TIME
        self.shake = 0.3 if len(full) == 4 else 0.15
        self.popup = [LINE_NAMES[len(full)], 1.0]
        for r in full:
            for c in range(COLS):
                self.burst(c * CELL + CELL // 2, r * CELL + CELL // 2,
                           COLORS[self.board[r][c]], 4)

    def finish_clear(self):
        count = len(self.clearing)
        kept = [row for r, row in enumerate(self.board) if r not in self.clearing]
        self.board = [[None] * COLS for _ in range(count)] + kept
        self.score += LINE_POINTS[count] * self.level
        self.lines += count
        self.clearing = []
        self.spawn()

    def burst(self, x, y, color, count):
        self.particles += [Particle(x, y, color) for _ in range(count)]

    def handle_held_keys(self, dt, keys):
        direction = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        if direction != self.held_dir:
            self.held_dir = direction
            self.repeat_timer = 0
        elif direction:
            self.repeat_timer += dt
            if self.repeat_timer >= 0.15:
                self.repeat_timer -= 0.05
                self.move(direction)

    def update(self, dt, keys):
        self.shake = max(0, self.shake - dt)
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        if self.popup:
            self.popup[1] -= dt
            if self.popup[1] <= 0:
                self.popup = None

        if self.clearing:
            self.clear_timer -= dt
            if self.clear_timer <= 0:
                self.finish_clear()
        elif not self.over:
            self.handle_held_keys(dt, keys)
            soft = keys[pygame.K_DOWN]
            interval = 0.04 if soft else max(0.08, 0.8 - 0.07 * (self.level - 1))
            self.fall_timer += dt
            if self.fall_timer >= interval:
                self.fall_timer = 0
                if self.step_down() and soft:
                    self.score += 1


class Button:
    def __init__(self, text, x, y, w=150, h=45):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, WHITE if hovered else ACCENT, self.rect, border_radius=8)
        draw_text(self.text, font, BLACK, self.rect.centerx,
                  self.rect.centery - font.get_height() // 2)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def add_score(name, score):
    scores = load_leaderboard()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(scores, f, indent=2)


def draw_text(text, text_font, color, cx, y, alpha=255):
    surf = text_font.render(text, True, color)
    surf.set_alpha(alpha)
    screen.blit(surf, (int(cx - surf.get_width() / 2), int(y)))


def draw_cell(surface, x, y, color, size=CELL):
    rect = pygame.Rect(x + 1, y + 1, size - 2, size - 2)
    pygame.draw.rect(surface, color, rect, border_radius=4)
    lighter = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surface, lighter, rect, 2, border_radius=4)


def draw_shape(kind, shape, cx, cy, size, color=None):
    left = cx - len(shape[0]) * size // 2
    top = cy - len(shape) * size // 2
    for x, y in cells(shape, 0, 0):
        draw_cell(screen, left + x * size, top + y * size, color or COLORS[kind], size)


def draw_board(game):
    surface = pygame.Surface((BOARD_W, BOARD_H))
    for i in range(COLS + 1):
        pygame.draw.line(surface, GRID_LINE, (i * CELL, 0), (i * CELL, BOARD_H))
    for i in range(ROWS + 1):
        pygame.draw.line(surface, GRID_LINE, (0, i * CELL), (BOARD_W, i * CELL))

    for r, row in enumerate(game.board):
        flash = r in game.clearing and int(game.clear_timer * 20) % 2 == 0
        for c, kind in enumerate(row):
            if kind:
                draw_cell(surface, c * CELL, r * CELL, WHITE if flash else COLORS[kind])

    if game.piece:
        piece = game.piece
        for x, y in cells(piece.shape, piece.x, game.ghost_y()):
            rect = (x * CELL + 2, y * CELL + 2, CELL - 4, CELL - 4)
            pygame.draw.rect(surface, COLORS[piece.kind], rect, 2, border_radius=4)
        for x, y in cells(piece.shape, piece.x, piece.y):
            draw_cell(surface, x * CELL, y * CELL, COLORS[piece.kind])

    for p in game.particles:
        p.draw(surface)
    return surface


def draw_panel(game):
    left = BOARD_W + 10
    pygame.draw.rect(screen, PANEL_BG, (left, 0, WIDTH - left, HEIGHT))
    pygame.draw.line(screen, ACCENT, (left, 0), (left, HEIGHT), 2)
    cx = (left + WIDTH) // 2

    draw_text("Next", font, WHITE, cx, 20)
    draw_shape(game.next.kind, game.next.shape, cx, 85, 25)

    draw_text("Hold", font, WHITE, cx, 140)
    if game.hold_kind:
        color = COLORS[game.hold_kind] if game.can_hold else GRAY
        draw_shape(game.hold_kind, SHAPES[game.hold_kind], cx, 205, 25, color)

    draw_text("Score", font, WHITE, cx, 270)
    draw_text(str(game.score), big_font, GOLD, cx, 295)
    draw_text("Level", font, WHITE, cx, 360)
    draw_text(str(game.level), font, ACCENT, cx, 385)
    draw_text("Lines", font, WHITE, cx, 430)
    draw_text(str(game.lines), font, ACCENT, cx, 455)

    draw_text("Space: drop   C: hold", small_font, MUTED, cx, 530)
    draw_text("Up: rotate   P: pause", small_font, MUTED, cx, 555)


def draw_game(game, paused):
    screen.fill(MENU_BG)
    shake = 5 if game.shake > 0 else 0
    offset = (random.randint(-shake, shake), random.randint(-shake, shake))
    screen.blit(draw_board(game), offset)

    if game.popup:
        text, life = game.popup
        draw_text(text, big_font, GOLD, BOARD_W // 2, 250 - (1 - life) * 60, int(255 * life))

    draw_panel(game)

    if paused:
        draw_overlay(120)
        draw_text("PAUSED", big_font, WHITE, BOARD_W // 2, 270)
        draw_text("Press P to resume", small_font, MUTED, BOARD_W // 2, 320)


def draw_overlay(alpha):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, (0, 0))


def draw_game_over(score, name):
    draw_overlay(180)
    draw_text("GAME OVER", big_font, RED, WIDTH // 2, 150)
    draw_text(f"Final Score: {score}", font, WHITE, WIDTH // 2, 210)
    draw_text("Enter your name:", font, ACCENT, WIDTH // 2, 270)
    box = pygame.Rect(WIDTH // 2 - 120, 310, 240, 40)
    pygame.draw.rect(screen, (40, 40, 60), box, border_radius=6)
    pygame.draw.rect(screen, ACCENT, box, 2, border_radius=6)
    cursor = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else ""
    draw_text(name + cursor, font, WHITE, WIDTH // 2, box.y + 11)
    draw_text("ENTER to save, ESC to skip", small_font, MUTED, WIDTH // 2, 365)


def draw_menu(decor, buttons):
    screen.fill(MENU_BG)
    for d in decor:
        dim = tuple(c // 4 for c in COLORS[d["kind"]])
        draw_shape(d["kind"], SHAPES[d["kind"]], d["x"], d["y"], 20, dim)

    t = pygame.time.get_ticks() / 1000
    letters = "TETRIS"
    for i, letter in enumerate(letters):
        surf = title_font.render(letter, True, list(COLORS.values())[i])
        x = WIDTH // 2 - len(letters) * 30 + i * 60 + (60 - surf.get_width()) // 2
        screen.blit(surf, (x, 110 + math.sin(t * 3 + i) * 10))

    for button in buttons:
        button.draw()


def draw_leaderboard(back_button):
    screen.fill(MENU_BG)
    draw_text("LEADERBOARD", big_font, ACCENT, WIDTH // 2, 40)
    scores = load_leaderboard()
    if not scores:
        draw_text("No scores yet!", font, MUTED, WIDTH // 2, 200)
    for i, entry in enumerate(scores):
        y = 110 + i * 35
        color = GOLD if i == 0 else ACCENT if i < 3 else WHITE
        screen.blit(small_font.render(f"#{i + 1}", True, color), (140, y + 3))
        screen.blit(font.render(entry["name"], True, WHITE), (180, y))
        score = font.render(str(entry["score"]), True, color)
        screen.blit(score, (380 - score.get_width(), y))
    back_button.draw()


def main():
    state = "menu"
    game = None
    paused = False
    name = ""

    start_button = Button("Start Game", 175, 250)
    leaderboard_button = Button("Leaderboard", 175, 310)
    quit_button = Button("Quit", 175, 370)
    back_button = Button("Back", 175, 520)
    menu_buttons = [start_button, leaderboard_button, quit_button]

    decor = [{"kind": random.choice(list(SHAPES)),
              "x": random.randint(0, WIDTH),
              "y": random.randint(-100, HEIGHT),
              "speed": random.randint(40, 100)} for _ in range(12)]

    while True:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if state == "menu" and event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.clicked(event.pos):
                    game = Game()
                    paused = False
                    state = "game"
                elif leaderboard_button.clicked(event.pos):
                    state = "leaderboard"
                elif quit_button.clicked(event.pos):
                    return

            elif state == "leaderboard" and event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.clicked(event.pos):
                    state = "menu"

            elif state == "game" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
                elif event.key == pygame.K_p:
                    paused = not paused
                elif game.playing and not paused:
                    if event.key == pygame.K_LEFT:
                        game.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1)
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()
                    elif event.key == pygame.K_c:
                        game.swap_hold()

            elif state == "gameover" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    add_score(name.strip() or "Anonymous", game.score)
                    state = "leaderboard"
                elif event.key == pygame.K_ESCAPE:
                    state = "menu"
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode.isprintable() and len(name) < 16:
                    name += event.unicode

        if state == "menu":
            for d in decor:
                d["y"] += d["speed"] * dt
                if d["y"] > HEIGHT + 100:
                    d["x"], d["y"] = random.randint(0, WIDTH), -100
            draw_menu(decor, menu_buttons)

        elif state == "leaderboard":
            draw_leaderboard(back_button)

        elif state in ("game", "gameover"):
            if state == "game" and not paused:
                game.update(dt, pygame.key.get_pressed())
                if game.over:
                    state = "gameover"
                    name = ""
            draw_game(game, paused)
            if state == "gameover":
                draw_game_over(game.score, name)

        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()