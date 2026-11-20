import pygame
import random
import math
import sys

# --- INITIALISIERUNG & KONSTANTEN ---
pygame.init()
WIDTH, HEIGHT = 800, 650
FPS = 60

# Farben
BLACK = (10, 12, 22)
WHITE = (240, 245, 255)
CYAN = (0, 240, 255)
MAGENTA = (255, 40, 140)
YELLOW = (255, 220, 40)
GREEN = (50, 255, 100)
RED = (255, 60, 60)
ORANGE = (255, 140, 20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SPACE INVADERS BATTLE")
clock = pygame.time.Clock()

font_small = pygame.font.SysFont("consolas", 20, bold=True)
font_large = pygame.font.SysFont("consolas", 48, bold=True)


# --- PARTIKEL & STERNE ---
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.4, 2.2)
        self.size = 1 if self.speed < 1.3 else 2
        brightness = int(100 + self.speed * 70)
        self.color = (brightness, brightness, min(255, brightness + 30))

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 6.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(18, 35)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            surf.blit(s, (self.x - self.size, self.y - self.size))


# --- SPIELOBJEKTE ---
class Player:
    def __init__(self):
        self.width = 48
        self.height = 36
        self.x = WIDTH // 2
        self.y = HEIGHT - 60
        self.speed = 6
        self.lives = 3
        self.cooldown = 0
        self.triple_shot_timer = 0
        self.shield = False
        self.invulnerable = 0

    def update(self, keys):
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.x - self.width // 2 > 15:
            self.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.x + self.width // 2 < WIDTH - 15:
            self.x += self.speed

        if self.cooldown > 0:
            self.cooldown -= 1
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1

    def shoot(self, bullets):
        if self.cooldown == 0:
            if self.triple_shot_timer > 0:
                bullets.append(Bullet(self.x, self.y - 20, 0, -9, CYAN, True))
                bullets.append(Bullet(self.x - 14, self.y - 12, -1.5, -8.8, CYAN, True))
                bullets.append(Bullet(self.x + 14, self.y - 12, 1.5, -8.8, CYAN, True))
                self.cooldown = 16
            else:
                bullets.append(Bullet(self.x, self.y - 20, 0, -9, CYAN, True))
                self.cooldown = 14

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def draw(self, surf):
        if self.invulnerable > 0 and (self.invulnerable // 4) % 2 == 0:
            return

        # Triebwerksflamme
        flame_h = random.randint(10, 18)
        pygame.draw.polygon(surf, ORANGE, [
            (self.x - 8, self.y + 14),
            (self.x + 8, self.y + 14),
            (self.x, self.y + 14 + flame_h)
        ])

        # Raumschiff-Rumpf
        points = [
            (self.x, self.y - 20),
            (self.x + 8, self.y - 6),
            (self.x + 24, self.y + 12),
            (self.x + 10, self.y + 15),
            (self.x - 10, self.y + 15),
            (self.x - 24, self.y + 12),
            (self.x - 8, self.y - 6),
        ]
        pygame.draw.polygon(surf, WHITE, points)
        pygame.draw.polygon(surf, CYAN, points, 2)

        # Cockpit
        pygame.draw.ellipse(surf, CYAN, (self.x - 5, self.y - 7, 10, 14))

        # Schild-Effekt
        if self.shield:
            pygame.draw.circle(surf, GREEN, (int(self.x), int(self.y)), 34, 2)


class Enemy:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.width = 36
        self.height = 28
        self.row = row
        if row == 0:
            self.color = MAGENTA
            self.points = 30
        elif row in (1, 2):
            self.color = YELLOW
            self.points = 20
        else:
            self.color = GREEN
            self.points = 10

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def draw(self, surf, anim_frame):
        w, h = self.width // 2, self.height // 2
        # Alien-Körper
        body = [
            (self.x - w + 6, self.y - h),
            (self.x + w - 6, self.y - h),
            (self.x + w, self.y),
            (self.x + w - 4, self.y + h - 4),
            (self.x - w + 4, self.y + h - 4),
            (self.x - w, self.y),
        ]
        pygame.draw.polygon(surf, self.color, body)

        # Animierte Beine/Tentakel
        offset = 4 if anim_frame else -4
        pygame.draw.line(surf, self.color, (self.x - 10, self.y + h - 4), (self.x - 10 + offset, self.y + h + 4), 3)
        pygame.draw.line(surf, self.color, (self.x + 10, self.y + h - 4), (self.x + 10 - offset, self.y + h + 4), 3)

        # Augen
        pygame.draw.rect(surf, BLACK, (self.x - 8, self.y - 4, 5, 5))
        pygame.draw.rect(surf, BLACK, (self.x + 3, self.y - 4, 5, 5))


class Bullet:
    def __init__(self, x, y, vx, vy, color, is_player):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.is_player = is_player
        self.radius = 4

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def get_rect(self):
        return pygame.Rect(self.x - 3, self.y - 8, 6, 16)

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (self.x - 2, self.y - 8, 4, 16), border_radius=2)


class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.kind = random.choice(["TRIPLE", "SHIELD"])
        self.color = CYAN if self.kind == "TRIPLE" else GREEN
        self.vy = 2.5

    def update(self):
        self.y += self.vy

    def get_rect(self):
        return pygame.Rect(self.x - 12, self.y - 12, 24, 24)

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 12, 2)
        label = "T" if self.kind == "TRIPLE" else "S"
        txt = font_small.render(label, True, self.color)
        surf.blit(txt, (self.x - txt.get_width() // 2, self.y - txt.get_height() // 2))


# --- HILFSFUNKTIONEN ---
def spawn_wave(wave):
    enemies = []
    rows = 5
    cols = 9
    start_x = 120
    start_y = 85
    spacing_x = 68
    spacing_y = 46
    for r in range(rows):
        for c in range(cols):
            enemies.append(Enemy(start_x + c * spacing_x, start_y + r * spacing_y, r))
    return enemies


def spawn_explosion(particles, x, y, color, count=18):
    for _ in range(count):
        particles.append(Particle(x, y, color))


# --- HAUPTSPIEL ---
def main():
    stars = [Star() for _ in range(70)]
    player = Player()
    wave = 1
    score = 0
    enemies = spawn_wave(wave)
    bullets = []
    particles = []
    powerups = []

    enemy_dir = 1
    enemy_base_speed = 1.2
    anim_timer = 0
    anim_frame = False
    shake = 0
    game_over = False

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if game_over and event.key == pygame.K_r:
                    # Neustart
                    player = Player()
                    wave = 1
                    score = 0
                    enemies = spawn_wave(wave)
                    bullets.clear()
                    particles.clear()
                    powerups.clear()
                    enemy_dir = 1
                    game_over = False

        # --- UPDATE ---
        for star in stars:
            star.update()

        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        if not game_over:
            player.update(keys)
            if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
                player.shoot(bullets)

            # Animationstakt der Aliens
            anim_timer += 1
            if anim_timer >= 20:
                anim_timer = 0
                anim_frame = not anim_frame

            # Gegnerbewegung (schneller bei weniger Gegnern)
            speed_boost = 1 + (45 - len(enemies)) * 0.045 + (wave - 1) * 0.25
            current_speed = enemy_base_speed * speed_boost * enemy_dir

            hit_edge = False
            for e in enemies:
                e.x += current_speed
                if e.x + e.width // 2 >= WIDTH - 20 or e.x - e.width // 2 <= 20:
                    hit_edge = True

            if hit_edge:
                enemy_dir *= -1
                for e in enemies:
                    e.y += 18
                    if e.y + e.height // 2 >= player.y - 15:
                        game_over = True

            # Zufällige Gegnerschüsse
            shoot_chance = min(0.04, 0.012 + wave * 0.004)
            if enemies and random.random() < shoot_chance:
                shooter = random.choice(enemies)
                bullets.append(Bullet(shooter.x, shooter.y + 14, 0, 5.2 + wave * 0.3, RED, False))

            # Projektile bewegen & Kollisionen prüfen
            for b in bullets[:]:
                b.update()
                if b.y < -20 or b.y > HEIGHT + 20:
                    bullets.remove(b)
                    continue

                if b.is_player:
                    for e in enemies[:]:
                        if b.get_rect().colliderect(e.get_rect()):
                            score += e.points
                            spawn_explosion(particles, e.x, e.y, e.color)
                            if random.random() < 0.12:
                                powerups.append(PowerUp(e.x, e.y))
                            enemies.remove(e)
                            if b in bullets:
                                bullets.remove(b)
                            break
                else:
                    if b.get_rect().colliderect(player.get_rect()):
                        bullets.remove(b)
                        if player.invulnerable == 0:
                            if player.shield:
                                player.shield = False
                                spawn_explosion(particles, player.x, player.y, GREEN, 15)
                            else:
                                player.lives -= 1
                                player.invulnerable = 90
                                shake = 12
                                spawn_explosion(particles, player.x, player.y, RED, 25)
                                if player.lives <= 0:
                                    game_over = True

            # Power-Ups einsammeln
            for pu in powerups[:]:
                pu.update()
                if pu.y > HEIGHT + 20:
                    powerups.remove(pu)
                elif pu.get_rect().colliderect(player.get_rect()):
                    if pu.kind == "TRIPLE":
                        player.triple_shot_timer = 420  # 7 Sekunden
                    elif pu.kind == "SHIELD":
                        player.shield = True
                    spawn_explosion(particles, pu.x, pu.y, pu.color, 12)
                    powerups.remove(pu)

            # Nächste Welle starten
            if not enemies:
                wave += 1
                bullets.clear()
                enemies = spawn_wave(wave)

        # --- ZEICHNEN ---
        render_surf = pygame.Surface((WIDTH, HEIGHT))
        render_surf.fill(BLACK)

        for star in stars:
            star.draw(render_surf)

        for pu in powerups:
            pu.draw(render_surf)

        for e in enemies:
            e.draw(render_surf, anim_frame)

        for b in bullets:
            b.draw(render_surf)

        if not game_over:
            player.draw(render_surf)

        for p in particles:
            p.draw(render_surf)

        # HUD (Punkte, Welle, Leben)
        score_txt = font_small.render(f"SCORE: {score}", True, WHITE)
        wave_txt = font_small.render(f"WAVE: {wave}", True, CYAN)
        lives_txt = font_small.render(f"LIVES: {'♥ ' * max(0, player.lives)}", True, MAGENTA)
        render_surf.blit(score_txt, (20, 15))
        render_surf.blit(wave_txt, (WIDTH // 2 - wave_txt.get_width() // 2, 15))
        render_surf.blit(lives_txt, (WIDTH - lives_txt.get_width() - 20, 15))

        if player.triple_shot_timer > 0 and not game_over:
            t_txt = font_small.render("TRIPLE SHOT!", True, CYAN)
            render_surf.blit(t_txt, (20, 42))

        if game_over:
            over_txt = font_large.render("GAME OVER", True, RED)
            final_txt = font_small.render(f"Final Score: {score}  |  Press [R] to Restart", True, WHITE)
            render_surf.blit(over_txt, (WIDTH // 2 - over_txt.get_width() // 2, HEIGHT // 2 - 40))
            render_surf.blit(final_txt, (WIDTH // 2 - final_txt.get_width() // 2, HEIGHT // 2 + 25))

        # Screen-Shake bei Treffer
        offset_x, offset_y = 0, 0
        if shake > 0:
            offset_x = random.randint(-shake, shake)
            offset_y = random.randint(-shake, shake)
            shake -= 1

        screen.fill(BLACK)
        screen.blit(render_surf, (offset_x, offset_y))
        pygame.display.flip()


if __name__ == "__main__":
    main()
