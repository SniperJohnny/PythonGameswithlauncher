import json
import math
import random

import pygame

# --- SETUP & CONSTANTS ---
pygame.init()
WIDTH, HEIGHT = 800, 600
FPS = 60
WIN_SCORE = 7                     # first to 7 wins (dumb / normal / 2 players)
START_LIVES = 3                   # lives in endless (smart) mode
LEADERBOARD_FILE = "leaderboard.pong"

# Colors
BLACK = (10, 12, 22)
WHITE = (240, 245, 255)
GREY = (120, 125, 150)
CYAN = (0, 240, 255)
MAGENTA = (255, 40, 140)
YELLOW = (255, 220, 40)
GREEN = (50, 255, 100)
RED = (255, 60, 60)

PADDLE_W, PADDLE_H, PADDLE_SPEED = 14, 90, 7
BALL_R, BALL_SPEED, BALL_MAX = 8, 6.0, 14.0

# AI settings: paddle speed factor, reaction time (frames), aim error (px), predicts wall bounces
AI_LEVELS = {
    "dumb": (0.55, 24, 60, False),
    "normal": (0.80, 11, 28, True),
    "smart": (1.00, 3, 8, True),
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PONG")
clock = pygame.time.Clock()

font_small = pygame.font.SysFont("consolas", 20, bold=True)
font_large = pygame.font.SysFont("consolas", 48, bold=True)
font_score = pygame.font.SysFont("consolas", 64, bold=True)
font_title = pygame.font.SysFont("consolas", 72, bold=True)


# --- PARTICLES & STARS ---
class Star:  # a background star that drifts down the screen
    def __init__(self):  # random position, speed and brightness
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.4, 2.2)
        self.size = 1 if self.speed < 1.3 else 2
        b = int(100 + self.speed * 70)
        self.color = (b, b, min(255, b + 30))

    def update(self):  # move down, wrap back to the top
        self.y += self.speed
        if self.y > HEIGHT:
            self.y, self.x = 0, random.randint(0, WIDTH)

    def draw(self, surf):  # draw the star as a small dot
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)


class Particle:  # a spark that flies out from hits and goals and fades away
    def __init__(self, x, y, color):  # random direction and speed
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 6.0)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.life = self.max_life = random.randint(18, 35)
        self.color = color
        self.size = random.randint(2, 4)

    def update(self):  # move, slow down, lose life
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf):  # draw a circle that fades out as life runs out
        alpha = int(255 * self.life / self.max_life)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surf.blit(s, (self.x - self.size, self.y - self.size))


# --- GAME OBJECTS ---
class Paddle:  # a player or CPU paddle
    def __init__(self, x, color):  # start in the middle of the screen
        self.x, self.y = x, HEIGHT / 2
        self.color = color
        self.flash = 0  # frames left of the white "hit" flash

    def get_rect(self):  # rectangle used for collisions and drawing
        return pygame.Rect(int(self.x - PADDLE_W / 2), int(self.y - PADDLE_H / 2), PADDLE_W, PADDLE_H)

    def move(self, direction):  # move up (-1) / down (+1), stay on screen
        self.y += max(-1, min(1, direction)) * PADDLE_SPEED
        self.y = max(PADDLE_H / 2 + 5, min(HEIGHT - PADDLE_H / 2 - 5, self.y))
        if self.flash > 0:
            self.flash -= 1

    def draw(self, surf):  # filled paddle with a neon outline, white when just hit
        r = self.get_rect().inflate(4, 8) if self.flash else self.get_rect()
        pygame.draw.rect(surf, WHITE if self.flash else self.color, r, border_radius=6)
        pygame.draw.rect(surf, WHITE, r, 2, border_radius=6)


class Ball:  # the ball with its fading trail
    def __init__(self):  # start resting in the middle
        self.reset()

    def reset(self):  # put the ball back in the middle, not moving
        self.x, self.y = WIDTH / 2, HEIGHT / 2
        self.vx = self.vy = 0.0
        self.speed = BALL_SPEED
        self.color = WHITE
        self.trail = []

    def serve(self, direction):  # launch towards one side (-1 left, +1 right) at a random angle
        angle = math.radians(random.uniform(-30, 30))
        self.vx = direction * self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

    def draw(self, surf, blink=False):  # draw the trail and the glowing ball
        for i, (tx, ty) in enumerate(self.trail):
            pygame.draw.circle(surf, self.color, (int(tx), int(ty)), max(1, BALL_R - i))
        if not blink:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), BALL_R + 3, 2)
            pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), BALL_R - 2)


class AI:  # computer player that steers a paddle towards where the ball will be
    def __init__(self, level, paddle, side):  # side: +1 = right paddle, -1 = left paddle
        self.speed, self.reaction, self.error, self.predicts = AI_LEVELS[level]
        self.paddle, self.side = paddle, side
        self.target, self.timer = HEIGHT / 2, 0

    def predict_y(self, ball):  # where the ball will hit our side, bouncing off top/bottom walls
        face_x = self.paddle.x - self.side * (PADDLE_W / 2 + BALL_R)
        y = ball.y + ball.vy * (face_x - ball.x) / ball.vx
        span = HEIGHT - 2 * BALL_R
        y = (y - BALL_R) % (2 * span)          # "unfold" the bounces
        return (2 * span - y if y > span else y) + BALL_R

    def decide(self, ball):  # returns how to move this frame (-1 .. 1)
        self.timer -= 1
        if self.timer <= 0:  # only "thinks" every few frames (slower = dumber)
            self.timer = self.reaction
            if ball.vx * self.side > 0:  # ball is coming towards us
                y = self.predict_y(ball) if self.predicts else ball.y
                self.target = y + random.uniform(-1, 1) * self.error * ball.speed / BALL_SPEED
            else:
                self.target = HEIGHT / 2  # go back to the middle
        diff = self.target - self.paddle.y
        return 0 if abs(diff) < 5 else max(-1, min(1, diff / 30)) * self.speed


class Match:  # one game of pong: paddles, ball, score, lives and effects
    def __init__(self, mode, level="normal"):  # mode: "1p", "2p", "endless" or "demo" (menu background)
        self.mode, self.level = mode, level
        self.left, self.right = Paddle(40, CYAN), Paddle(WIDTH - 40, MAGENTA)
        self.ball = Ball()
        self.scores = [0, 0]
        self.points, self.lives = 0, START_LIVES  # used in endless mode
        self.particles = []
        self.shake = 0
        self.winner, self.over = None, False
        self.intro = mode != "demo"                 # show 3-2-1 before the first serve
        self.countdown = 180 if self.intro else 30  # frames until the ball is served
        self.serve_dir = random.choice((-1, 1))
        self.ai_left = AI("normal", self.left, -1) if mode == "demo" else None
        right_level = {"endless": "smart", "demo": "normal", "1p": level}.get(mode)
        self.ai_right = AI(right_level, self.right, 1) if right_level else None

    def update(self, keys):  # one frame: input, AI, ball physics, effects
        if keys and not self.over:
            if self.mode == "2p":
                self.left.move(keys[pygame.K_s] - keys[pygame.K_w])
                self.right.move(keys[pygame.K_DOWN] - keys[pygame.K_UP])
            else:
                self.left.move((keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]))
        if self.ai_left:
            self.left.move(self.ai_left.decide(self.ball))
        if self.ai_right and not self.over:
            self.right.move(self.ai_right.decide(self.ball))

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
        if self.shake > 0:
            self.shake -= 1
        if self.over:
            return
        if self.countdown > 0:  # waiting to serve
            self.countdown -= 1
            if self.countdown == 0:
                self.intro = False
                self.ball.serve(self.serve_dir)
            return

        b = self.ball
        steps = int(b.speed / 4) + 1  # move in small steps so the ball can't skip through a paddle
        for _ in range(steps):
            if self.step(b, 1 / steps):
                return
        b.trail = [(b.x, b.y)] + b.trail[:6]

    def step(self, b, frac):  # move the ball a bit and handle walls, paddles and goals
        b.x += b.vx * frac
        b.y += b.vy * frac
        if b.y < BALL_R or b.y > HEIGHT - BALL_R:  # bounce off top / bottom
            b.vy = abs(b.vy) if b.y < BALL_R else -abs(b.vy)
            b.y = max(BALL_R, min(HEIGHT - BALL_R, b.y))
            self.burst(b.x, b.y, b.color, 5)

        ball_rect = pygame.Rect(b.x - BALL_R, b.y - BALL_R, BALL_R * 2, BALL_R * 2)
        for paddle, d in ((self.left, 1), (self.right, -1)):
            if b.vx * d < 0 and paddle.get_rect().colliderect(ball_rect):
                self.hit(b, paddle, d)

        if b.x < -BALL_R * 3:
            self.goal(1)
            return True
        if b.x > WIDTH + BALL_R * 3:
            self.goal(0)
            return True
        return False

    def hit(self, b, paddle, d):  # ball hits a paddle: bounce back faster, angle depends on where it hit
        offset = max(-1, min(1, (b.y - paddle.y) / (PADDLE_H / 2)))  # -1 top edge .. +1 bottom edge
        angle = math.radians(offset * 60)
        b.speed = min(b.speed * 1.05, BALL_MAX)
        b.vx, b.vy = d * b.speed * math.cos(angle), b.speed * math.sin(angle)
        b.x = paddle.x + d * (PADDLE_W / 2 + BALL_R)
        b.color = paddle.color
        paddle.flash = 8
        self.shake = max(self.shake, 4)
        self.burst(b.x, b.y, paddle.color, 12)
        if self.mode == "endless" and paddle is self.left:
            self.points += 10

    def goal(self, scorer):  # someone scored (0 = left, 1 = right)
        color = CYAN if scorer == 0 else MAGENTA
        self.scores[scorer] += 1
        self.shake = 14
        self.burst(WIDTH if scorer == 0 else 0, self.ball.y, color, 40)
        self.ball.reset()
        if self.mode == "endless":
            if scorer == 0:
                self.points += 100
            else:
                self.lives -= 1
                self.over = self.lives <= 0
        elif self.mode == "demo":
            if max(self.scores) >= WIN_SCORE:
                self.scores = [0, 0]
        elif self.scores[scorer] >= WIN_SCORE:
            self.winner, self.over = scorer, True
            self.burst(WIDTH / 2, HEIGHT / 2, color, 80)
        self.serve_dir = 1 if scorer == 0 else -1  # serve towards whoever lost the point
        self.countdown = 50

    def burst(self, x, y, color, count):  # spawn a bunch of particles
        self.particles += [Particle(x, y, color) for _ in range(count)]

    def draw(self, surf):  # draw the whole match (field, HUD, paddles, ball)
        for y in range(0, HEIGHT, 30):
            pygame.draw.rect(surf, (35, 40, 70), (WIDTH // 2 - 2, y + 8, 4, 16))

        if self.mode == "endless":
            surf.blit(font_small.render(f"SCORE: {self.points}", True, WHITE), (20, 15))
            draw_text(surf, "ENDLESS", font_small, YELLOW, WIDTH // 2, 15)
            lives = font_small.render(f"LIVES: {'♥ ' * max(0, self.lives)}", True, MAGENTA)
            surf.blit(lives, (WIDTH - lives.get_width() - 20, 15))
        elif self.mode != "demo":
            names = ("YOU", f"CPU ({self.level.upper()})") if self.mode == "1p" else ("PLAYER 1", "PLAYER 2")
            for i, (x, color) in enumerate(((WIDTH // 2 - 100, CYAN), (WIDTH // 2 + 100, MAGENTA))):
                draw_text(surf, str(self.scores[i]), font_score, color, x, 15)
                draw_text(surf, names[i], font_small, GREY, x, 85)

        for p in self.particles:
            p.draw(surf)
        self.left.draw(surf)
        self.right.draw(surf)
        if not self.over:
            self.ball.draw(surf, blink=self.countdown > 0 and self.countdown // 8 % 2 == 0)

        if self.intro and self.countdown > 0:  # 3-2-1 that pops in and shrinks
            num = math.ceil(self.countdown / 60)
            size = 1 + (self.countdown % 60) / 60
            img = font_title.render(str(num), True, YELLOW)
            img = pygame.transform.smoothscale(img, (int(img.get_width() * size), int(img.get_height() * size)))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)))
            hint = "P1: W/S   P2: UP/DOWN   ESC: PAUSE" if self.mode == "2p" else "MOVE: W/S OR UP/DOWN   ESC: PAUSE"
            draw_text(surf, hint, font_small, GREY, WIDTH // 2, HEIGHT - 40)


class Button:  # clickable menu button that fills up when the mouse hovers over it
    def __init__(self, text, x, y, w=260, h=48):  # text and position of the button
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def clicked(self, pos):  # was this button clicked?
        return self.rect.collidepoint(pos)

    def draw(self, surf):  # draw outline, filled + slightly bigger when hovered
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        r = self.rect.inflate(10, 6) if hovered else self.rect
        if hovered:
            pygame.draw.rect(surf, CYAN, r, border_radius=8)
        pygame.draw.rect(surf, CYAN, r, 2, border_radius=8)
        txt = font_small.render(self.text, True, BLACK if hovered else CYAN)
        surf.blit(txt, txt.get_rect(center=r.center))


# --- HELPERS ---
def load_leaderboard():  # read the saved top 10 (empty list if there is none yet)
    try:
        with open(LEADERBOARD_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def add_score(name, score):  # save a new score and keep only the best 10
    scores = load_leaderboard()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(scores, f, indent=2)
    return scores


def draw_text(surf, text, fnt, color, cx, y):  # draw text centered horizontally at cx
    img = fnt.render(text, True, color)
    surf.blit(img, (cx - img.get_width() // 2, y))


def draw_title(surf, title, y, t):  # rainbow title with letters waving up and down
    widths = [font_title.size(letter)[0] for letter in title]
    x = WIDTH // 2 - sum(widths) // 2
    for i, letter in enumerate(title):
        color = pygame.Color(0)
        color.hsva = ((t * 60 + i * 20) % 360, 80, 100, 100)
        surf.blit(font_title.render(letter, True, color), (x, y + math.sin(t * 3 + i * 0.5) * 12))
        x += widths[i]


def draw_overlay(surf, alpha):  # darken everything behind a menu
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surf.blit(overlay, (0, 0))


def draw_leaderboard(surf, scores):  # top 10 list for endless mode
    draw_text(surf, "LEADERBOARD", font_large, CYAN, WIDTH // 2, 40)
    draw_text(surf, "ENDLESS MODE", font_small, YELLOW, WIDTH // 2, 95)
    if not scores:
        draw_text(surf, "No scores yet!", font_small, WHITE, WIDTH // 2, 250)
    for i, entry in enumerate(scores):
        y = 135 + i * 36
        color = YELLOW if i == 0 else CYAN if i < 3 else WHITE
        surf.blit(font_small.render(f"#{i + 1}", True, color), (190, y))
        surf.blit(font_small.render(entry["name"], True, WHITE), (260, y))
        score_img = font_small.render(str(entry["score"]), True, color)
        surf.blit(score_img, (610 - score_img.get_width(), y))


# --- MAIN GAME ---
def main():  # menu / game loop
    stars = [Star() for _ in range(70)]
    demo = Match("demo")  # AI vs AI game playing behind the menu
    match = None
    state = "menu"
    name = ""
    scores = []
    last = ("1p", "normal")
    fade = 255  # black fade-in after every screen change
    bx = WIDTH // 2 - 130

    buttons = {  # state -> {action: button}
        "menu": {"1p": Button("1 PLAYER", bx, 290), "2p": Button("2 PLAYERS", bx, 350),
                 "leaderboard": Button("LEADERBOARD", bx, 410), "quit": Button("QUIT", bx, 470)},
        "difficulty": {"dumb": Button("DUMB", bx, 230), "normal": Button("NORMAL", bx, 290),
                       "smart": Button("SMART  (ENDLESS)", bx, 350), "menu": Button("BACK", bx, 450)},
        "pause": {"resume": Button("RESUME", bx, 260), "rematch": Button("RESTART", bx, 320),
                  "menu": Button("MAIN MENU", bx, 380)},
        "gameover": {"rematch": Button("REMATCH", bx, 320), "menu": Button("MAIN MENU", bx, 380)},
        "leaderboard": {"menu": Button("BACK", bx, 530)},
    }

    def start(mode, level="normal"):  # begin a new match
        nonlocal match, state, last
        last = (mode, level)
        match = Match(mode, level)
        state = "playing"

    def do(action):  # run a button's action, returns False when the game should close
        nonlocal state, scores, fade
        fade = 255 if action != "resume" else 0
        if action == "1p":
            state = "difficulty"
        elif action == "2p":
            start("2p")
        elif action in ("dumb", "normal"):
            start("1p", action)
        elif action == "smart":
            start("endless")
        elif action == "leaderboard":
            scores = load_leaderboard()
            state = "leaderboard"
        elif action == "menu":
            state = "menu"
        elif action == "resume":
            state = "playing"
        elif action == "rematch":
            start(*last)
        elif action == "quit":
            return False
        return True

    while True:
        clock.tick(FPS)
        t = pygame.time.get_ticks() / 1000

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state in buttons:
                for action, button in buttons[state].items():
                    if button.clicked(event.pos):
                        if not do(action):
                            return
                        break
            elif event.type == pygame.KEYDOWN:
                if state == "playing" and event.key in (pygame.K_ESCAPE, pygame.K_p):
                    state = "pause"
                elif state == "pause" and event.key in (pygame.K_ESCAPE, pygame.K_p):
                    do("resume")
                elif state in ("difficulty", "leaderboard", "gameover") and event.key == pygame.K_ESCAPE:
                    do("menu")
                elif state == "entername":  # typing a name for the leaderboard
                    if event.key == pygame.K_RETURN:
                        add_score(name.strip() or "Anonymous", match.points)
                        do("leaderboard")
                    elif event.key == pygame.K_ESCAPE:
                        do("menu")
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.unicode.isprintable() and event.unicode and len(name) < 14:
                        name += event.unicode

        # --- UPDATE ---
        for star in stars:
            star.update()
        if state in ("menu", "difficulty", "leaderboard"):
            demo.update(None)
        elif state in ("playing", "gameover", "entername"):
            match.update(pygame.key.get_pressed() if state == "playing" else None)
            if state == "playing" and match.over:
                if match.mode == "endless":
                    state, name = "entername", ""
                else:
                    state = "gameover"

        # --- DRAW ---
        render_surf = pygame.Surface((WIDTH, HEIGHT))
        render_surf.fill(BLACK)
        for star in stars:
            star.draw(render_surf)

        if state in ("menu", "difficulty", "leaderboard"):
            demo.draw(render_surf)
            draw_overlay(render_surf, 150)
        else:
            match.draw(render_surf)
            if state != "playing":
                draw_overlay(render_surf, 170)

        if state == "menu":
            draw_title(render_surf, "PONG", 90, t)
            pulse = int(180 + 75 * math.sin(t * 4))
            draw_text(render_surf, "N E O N   R A L L Y", font_small, (pulse, 40, 140), WIDTH // 2, 190)
        elif state == "difficulty":
            draw_title(render_surf, "CPU LEVEL", 90, t)
            draw_text(render_surf, "Smart = endless mode with lives & leaderboard", font_small, GREY, WIDTH // 2, 520)
        elif state == "pause":
            draw_title(render_surf, "PAUSED", 120, t)
        elif state == "gameover":
            if match.mode == "1p":
                text, color = ("YOU WIN!", GREEN) if match.winner == 0 else ("CPU WINS", RED)
            else:
                text, color = f"PLAYER {match.winner + 1} WINS!", CYAN if match.winner == 0 else MAGENTA
            draw_text(render_surf, text, font_large, color, WIDTH // 2, 170)
            draw_text(render_surf, f"{match.scores[0]}  -  {match.scores[1]}", font_small, WHITE, WIDTH // 2, 240)
        elif state == "entername":
            draw_text(render_surf, "GAME OVER", font_large, RED, WIDTH // 2, 170)
            draw_text(render_surf, f"Final Score: {match.points}", font_small, WHITE, WIDTH // 2, 235)
            draw_text(render_surf, "Enter your name:", font_small, CYAN, WIDTH // 2, 290)
            box = pygame.Rect(WIDTH // 2 - 130, 325, 260, 42)
            pygame.draw.rect(render_surf, (30, 35, 60), box, border_radius=6)
            pygame.draw.rect(render_surf, CYAN, box, 2, border_radius=6)
            cursor = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else ""
            draw_text(render_surf, name + cursor, font_small, WHITE, WIDTH // 2, box.y + 11)
            draw_text(render_surf, "ENTER to save, ESC to skip", font_small, WHITE, WIDTH // 2, 385)
        elif state == "leaderboard":
            draw_overlay(render_surf, 100)
            draw_leaderboard(render_surf, scores)

        for button in buttons.get(state, {}).values():
            button.draw(render_surf)

        # screen shake on hits and goals
        offset_x = offset_y = 0
        if state == "playing" and match.shake > 0:
            offset_x = random.randint(-match.shake // 2, match.shake // 2)
            offset_y = random.randint(-match.shake // 2, match.shake // 2)

        screen.fill(BLACK)
        screen.blit(render_surf, (offset_x, offset_y))
        if fade > 0:  # fade in from black
            draw_overlay(screen, fade)
            fade = max(0, fade - 20)
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
