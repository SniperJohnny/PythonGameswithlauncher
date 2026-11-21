# Erklärungsbauplan für spaceinvaders.py

## 1. Importierung der Librarys und Erstellen wichtiger Variablen
```python
import pygame
import random
import math
import json
import sys

# --- INITIALISIERUNG & KONSTANTEN ---
pygame.init()
WIDTH, HEIGHT = 800, 650
FPS = 60
LEADERBOARD_FILE = "leaderboards.spaceinvaders"

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
font_title = pygame.font.SysFont("consolas", 72, bold=True)
```
Diese Variablen sind wichtig für das spätere Programm zum Funktionieren, Deshalb setzen wir diese schon am Anfang des Programmes in Python. `sys` brauchen wir hier zusätzlich, damit wir das Programm später sauber mit `sys.exit()` beenden können.

## 2. Erstellungen der Partikel Klassen für Explosionen und den Hintergrund
### 2.1. Erstellung der Stern Klasse
```python
# --- PARTIKEL & STERNE ---
class Star:
    def __init__(self):
        #als erstes sagen wir den sternen, das sie eine random Position auf der x axe haben sollen, welche in der breite des programmes ist und das sie eine random höhe haben soll, welche immernoch im Bereich des Programmes vorhanden ist
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.4, 2.2)#fallgeschwindigkeit
        self.size = 1 if self.speed < 1.3 else 2
        brightness = int(100 + self.speed * 70)
        self.color = (brightness, brightness, min(255, brightness + 30))

    def update(self):  # move down, wrap back to the top
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self, surf):  # draw the star as a small dot
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)
```

### 2.2. Erstellung der Partikel Klasse
```python
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        #wir geben jedem Partikel eine zufällige Richtung (Winkel) und Geschwindigkeit
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
        #die Partikel werden mit der Zeit langsamer (Reibung) und verlieren Leben
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            #Alpha-Wert wird kleiner, damit die Partikel langsam ausblenden
            alpha = int(255 * (self.life / self.max_life))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            surf.blit(s, (self.x - self.size, self.y - self.size))
```
**Wir nutzen hier das Stichwort `class`, weil damit die Organisation von unseren Objekten, wie die Partikel und Sterne, einfacher ist für unseren späteren main loop**

## 3. Erstellung des Spielers, der Gegner, der Kugeln und der Power-Ups
### 3.1. Die Player Klasse
```python
# --- SPIELOBJEKTE ---
class Player:
    def __init__(self):
        self.width = 48
        self.height = 36
        self.x = WIDTH // 2
        self.y = HEIGHT - 60
        self.speed = 6
        self.lives = 3
        self.cooldown = 0                 #Abklingzeit zwischen zwei Schüssen
        self.triple_shot_timer = 0        #Restzeit für den Dreifachschuss
        self.shield = False               #hat der Spieler gerade einen Schild?
        self.invulnerable = 0             #Frames, in denen der Spieler unverwundbar ist

    def update(self, keys):
        #Bewegung nach links (Pfeil links ODER A)
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.x - self.width // 2 > 15:
            self.x -= self.speed
        #Bewegung nach rechts (Pfeil rechts ODER D)
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.x + self.width // 2 < WIDTH - 15:
            self.x += self.speed

        #Timer werden jede Frame heruntergezählt
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1

    def shoot(self, bullets):
        if self.cooldown == 0:
            if self.triple_shot_timer > 0:
                #drei Kugeln gleichzeitig, eine gerade und zwei schräg
                bullets.append(Bullet(self.x, self.y - 20, 0, -9, CYAN, True))
                bullets.append(Bullet(self.x - 14, self.y - 12, -1.5, -8.8, CYAN, True))
                bullets.append(Bullet(self.x + 14, self.y - 12, 1.5, -8.8, CYAN, True))
                self.cooldown = 16
            else:
                #nur eine normale Kugel
                bullets.append(Bullet(self.x, self.y - 20, 0, -9, CYAN, True))
                self.cooldown = 14

    def get_rect(self):
        #wir lassen pygame ein Rechteck erstellen, welches für Kollisionen genutzt wird
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def draw(self, surf):
        #während der Unverwundbarkeit blinkt das Raumschiff
        if self.invulnerable > 0 and (self.invulnerable // 4) % 2 == 0:
            return

        # Triebwerksflamme (zufällige Höhe = flackernde Flamme)
        flame_h = random.randint(10, 18)
        pygame.draw.polygon(surf, ORANGE, [
            (self.x - 8, self.y + 14),
            (self.x + 8, self.y + 14),
            (self.x, self.y + 14 + flame_h)
        ])

        # Raumschiff-Rumpf als Polygon
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

        # Cockpit (kleine Ellipse)
        pygame.draw.ellipse(surf, CYAN, (self.x - 5, self.y - 7, 10, 14))

        # Schild-Effekt als grüner Kreis
        if self.shield:
            pygame.draw.circle(surf, GREEN, (int(self.x), int(self.y)), 34, 2)
```

### 3.2. Die Enemy Klasse
```python
class Enemy:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.width = 36
        self.height = 28
        self.row = row
        #je nach Reihe bekommt der Gegner eine andere Farbe und andere Punkte
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
        # Alien-Körper als Polygon
        body = [
            (self.x - w + 6, self.y - h),
            (self.x + w - 6, self.y - h),
            (self.x + w, self.y),
            (self.x + w - 4, self.y + h - 4),
            (self.x - w + 4, self.y + h - 4),
            (self.x - w, self.y),
        ]
        pygame.draw.polygon(surf, self.color, body)

        # Animierte Beine/Tentakel (wechseln je nach anim_frame die Richtung)
        offset = 4 if anim_frame else -4
        pygame.draw.line(surf, self.color, (self.x - 10, self.y + h - 4), (self.x - 10 + offset, self.y + h + 4), 3)
        pygame.draw.line(surf, self.color, (self.x + 10, self.y + h - 4), (self.x + 10 - offset, self.y + h + 4), 3)

        # Augen
        pygame.draw.rect(surf, BLACK, (self.x - 8, self.y - 4, 5, 5))
        pygame.draw.rect(surf, BLACK, (self.x + 3, self.y - 4, 5, 5))
```

### 3.3. Die Bullet Klasse
```python
class Bullet:
    def __init__(self, x, y, vx, vy, color, is_player):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.is_player = is_player        #True = Spielerkugel, False = Gegnerkugel
        self.radius = 4

    def update(self):
        #die Kugel bewegt sich einfach mit ihrer Geschwindigkeit weiter
        self.x += self.vx
        self.y += self.vy

    def get_rect(self):
        return pygame.Rect(self.x - 3, self.y - 8, 6, 16)

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (self.x - 2, self.y - 8, 4, 16), border_radius=2)
```
**Hier sieht man gut, warum `is_player` wichtig ist: die Kollisionslogik im Main Loop entscheidet damit, ob die Kugel Gegner oder den Spieler treffen kann.**

### 3.4. Die PowerUp Klasse
```python
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        #zufällig entweder Dreifachschuss oder Schild
        self.kind = random.choice(["TRIPLE", "SHIELD"])
        self.color = CYAN if self.kind == "TRIPLE" else GREEN
        self.vy = 2.5

    def update(self):
        #Power-Up fällt langsam nach unten
        self.y += self.vy

    def get_rect(self):
        return pygame.Rect(self.x - 12, self.y - 12, 24, 24)

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 12, 2)
        #Buchstabe zeigt, welche Art Power-Up es ist: T = Triple, S = Shield
        label = "T" if self.kind == "TRIPLE" else "S"
        txt = font_small.render(label, True, self.color)
        surf.blit(txt, (self.x - txt.get_width() // 2, self.y - txt.get_height() // 2))
```

## 4. Buttons und Helfermethoden, welche wir brauchen
```python
class Button:
    def __init__(self, text, x, y, w=220, h=48):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def clicked(self, pos):
        #wurde der Button an der Mausposition geklickt?
        return self.rect.collidepoint(pos)

    def draw(self, surf):
        #wenn die Maus über dem Button ist, wird er ausgefüllt
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if hovered:
            pygame.draw.rect(surf, CYAN, self.rect, border_radius=8)
        pygame.draw.rect(surf, CYAN, self.rect, 2, border_radius=8)
        txt = font_small.render(self.text, True, BLACK if hovered else CYAN)
        surf.blit(txt, txt.get_rect(center=self.rect.center))
```

**die Button Klasse ist für und um einfacher buttons zu erstellen später**

```python
# --- HILFSFUNKTIONEN ---
def spawn_wave(wave):
    #erstellt eine neue Welle mit 5 Reihen und 9 Spalten an Gegnern
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
    #erstellt eine Explosion aus vielen Partikeln an einer Stelle
    for _ in range(count):
        particles.append(Particle(x, y, color))


def load_leaderboard():
    #liest die gespeicherten Top 10 (leere Liste wenn noch keine Datei existiert)
    try:
        with open(LEADERBOARD_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def add_score(name, score):
    #speichert einen neuen Score und behält nur die besten 10
    scores = load_leaderboard()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda s: s["score"], reverse=True)[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(scores, f, indent=2)
    return scores


def draw_text(surf, text, fnt, color, cx, y):
    #zeichnet Text horizontal zentriert bei cx
    img = fnt.render(text, True, color)
    surf.blit(img, (cx - img.get_width() // 2, y))


def draw_menu(surf, menu_enemies, buttons, t):
    #Regenbogen-Titel mit wippenden Buchstaben
    title = "SPACE INVADERS"
    widths = [font_title.size(letter)[0] for letter in title]
    x = WIDTH // 2 - sum(widths) // 2
    for i, letter in enumerate(title):
        color = pygame.Color(0)
        color.hsva = ((t * 60 + i * 20) % 360, 80, 100, 100)
        y = 90 + math.sin(t * 3 + i * 0.5) * 12
        surf.blit(font_title.render(letter, True, color), (x, y))
        x += widths[i]

    #pulsierender Untertitel
    pulse = int(180 + 75 * math.sin(t * 4))
    draw_text(surf, "B A T T L E", font_small, (pulse, 40, 140), WIDTH // 2, 185)

    #die kleinen Gegner im Menü schweben hin und her
    for i, e in enumerate(menu_enemies):
        e.x = 110 + i * 97 + math.sin(t * 1.5) * 35
        e.y = 270 + math.sin(t * 2 + i) * 8
        e.draw(surf, int(t * 3) % 2 == 0)

    for button in buttons:
        button.draw(surf)


def draw_leaderboard(surf, scores, back_button):
    #Top-10 Liste für den Game-Over-Screen
    draw_text(surf, "LEADERBOARD", font_large, CYAN, WIDTH // 2, 50)
    if not scores:
        draw_text(surf, "No scores yet!", font_small, WHITE, WIDTH // 2, 250)
    for i, entry in enumerate(scores):
        y = 130 + i * 40
        color = YELLOW if i == 0 else CYAN if i < 3 else WHITE
        surf.blit(font_small.render(f"#{i + 1}", True, color), (190, y))
        surf.blit(font_small.render(entry["name"], True, WHITE), (260, y))
        score_img = font_small.render(str(entry["score"]), True, color)
        surf.blit(score_img, (610 - score_img.get_width(), y))
    back_button.draw(surf)
```

## 5. Der Main loop
**Dieser wird am Anfang des Programmes gecallt, welcher die ganze Logik definiert**

### 5.1 Anfang der main function, nicht das was jeden frame ausgeführt wird
Sie definiert Variablen, erstellt die Buttons und Gegner fürs Menü und gibt uns eine `reset()`-Funktion, welche das Spiel in den Startzustand zurücksetzt.
```python
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

    enemy_dir = 1                     #1 = nach rechts, -1 = nach links
    enemy_base_speed = 1.2
    anim_timer = 0                    #zählt Frames bis zur nächsten Animation
    anim_frame = False                #wechselt zwischen zwei "Bildern" der Gegner
    shake = 0                         #Stärke des Screen-Shakes
    game_over = False

    state = "menu"
    name = ""
    scores = []
    start_button = Button("START GAME", WIDTH // 2 - 110, 360)
    leaderboard_button = Button("LEADERBOARD", WIDTH // 2 - 110, 425)
    quit_button = Button("QUIT", WIDTH // 2 - 110, 490)
    back_button = Button("BACK", WIDTH // 2 - 110, 570)
    menu_buttons = [start_button, leaderboard_button, quit_button]
    menu_enemies = [Enemy(0, 0, i % 5) for i in range(7)]

    def reset():
        #setzt alle spielrelevanten Variablen wieder auf den Startwert zurück
        nonlocal player, wave, score, enemies, bullets, particles, powerups
        nonlocal enemy_dir, shake, game_over
        player = Player()
        wave = 1
        score = 0
        enemies = spawn_wave(wave)
        bullets, particles, powerups = [], [], []
        enemy_dir = 1
        shake = 0
        game_over = False
```

### 5.2 Das wird jeden einzelnen Frame (Bild was der Computer ausspuckt, welche beim schnellen hintereinander abspielen flüssig aussehen)
```python
    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

            #im Menü: Klick auf einen der Buttons
            if state == "menu" and left_click:
                if start_button.clicked(event.pos):
                    reset()
                    state = "playing"
                elif leaderboard_button.clicked(event.pos):
                    scores = load_leaderboard()
                    state = "leaderboard"
                elif quit_button.clicked(event.pos):
                    pygame.quit()
                    sys.exit()

            #in der Bestenliste: zurück zum Menü
            elif state == "leaderboard" and left_click:
                if back_button.clicked(event.pos):
                    state = "menu"

            #im Spiel: ESC bringt zurück ins Menü
            elif state == "playing" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"

            #Game Over: Namen eingeben für die Bestenliste
            elif state == "gameover" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    scores = add_score(name.strip() or "Anonymous", score)
                    state = "leaderboard"
                elif event.key == pygame.K_ESCAPE:
                    state = "menu"
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode.isprintable() and len(name) < 14:
                    name += event.unicode

        # --- UPDATE ---
        for star in stars:
            star.update()

        #Partikel werden aktualisiert und sterben irgendwann
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        if state == "playing":
            player.update(keys)
            #Schießen mit LEERTASTE, PFEIL HOCH oder W
            if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
                player.shoot(bullets)

            # Animationstakt der Aliens (alle 20 Frames wechseln)
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
                #prüfen, ob ein Gegner den Rand berührt
                if e.x + e.width // 2 >= WIDTH - 20 or e.x - e.width // 2 <= 20:
                    hit_edge = True

            #wenn ein Gegner den Rand berührt: Richtung umdrehen + alle einen Schritt runter
            if hit_edge:
                enemy_dir *= -1
                for e in enemies:
                    e.y += 18
                    #wenn die Gegner den Spieler erreichen -> Game Over
                    if e.y + e.height // 2 >= player.y - 15:
                        game_over = True

            # Zufällige Gegnerschüsse (Chance steigt mit der Welle)
            shoot_chance = min(0.04, 0.012 + wave * 0.004)
            if enemies and random.random() < shoot_chance:
                shooter = random.choice(enemies)
                bullets.append(Bullet(shooter.x, shooter.y + 14, 0, 5.2 + wave * 0.3, RED, False))

            # Projektile bewegen & Kollisionen prüfen
            for b in bullets[:]:
                b.update()
                #Kugel verlässt den Bildschirm
                if b.y < -20 or b.y > HEIGHT + 20:
                    bullets.remove(b)
                    continue

                if b.is_player:
                    #Spielerkugel trifft Gegner
                    for e in enemies[:]:
                        if b.get_rect().colliderect(e.get_rect()):
                            score += e.points
                            spawn_explosion(particles, e.x, e.y, e.color)
                            #12% Chance auf ein Power-Up
                            if random.random() < 0.12:
                                powerups.append(PowerUp(e.x, e.y))
                            enemies.remove(e)
                            if b in bullets:
                                bullets.remove(b)
                            break
                else:
                    #Gegnerkugel trifft Spieler
                    if b.get_rect().colliderect(player.get_rect()):
                        bullets.remove(b)
                        if player.invulnerable == 0:
                            if player.shield:
                                #Schild wird zerstört statt Leben zu verlieren
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
                #Power-Up fällt unten aus dem Bildschirm
                if pu.y > HEIGHT + 20:
                    powerups.remove(pu)
                elif pu.get_rect().colliderect(player.get_rect()):
                    if pu.kind == "TRIPLE":
                        player.triple_shot_timer = 420  # 7 Sekunden
                    elif pu.kind == "SHIELD":
                        player.shield = True
                    spawn_explosion(particles, pu.x, pu.y, pu.color, 12)
                    powerups.remove(pu)

            # Nächste Welle starten, wenn alle Gegner weg sind
            if not enemies:
                wave += 1
                bullets.clear()
                enemies = spawn_wave(wave)

            #wenn der Spieler verloren hat -> Name eingeben
            if game_over:
                state = "gameover"
                name = ""
```

### 5.3 Zeichnen des Menüs und der Bestenliste (eigener, früher `continue`-Block)
```python
        # --- MENÜ & BESTENLISTE ---
        if state in ("menu", "leaderboard"):
            screen.fill(BLACK)
            for star in stars:
                star.draw(screen)
            if state == "menu":
                draw_menu(screen, menu_enemies, menu_buttons, pygame.time.get_ticks() / 1000)
            else:
                draw_leaderboard(screen, scores, back_button)
            pygame.display.flip()
            #wichtig: continue, damit der restliche Zeichencode für das eigentliche Spiel nicht läuft
            continue
```

### 5.4 Zeichnen des Spiels (HUD, Objekte, Game-Over-Overlay)
```python
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

        #Anzeige, wenn der Dreifachschuss aktiv ist
        if player.triple_shot_timer > 0 and not game_over:
            t_txt = font_small.render("TRIPLE SHOT!", True, CYAN)
            render_surf.blit(t_txt, (20, 42))

        #Game-Over-Overlay mit Namenseingabe
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            render_surf.blit(overlay, (0, 0))
            draw_text(render_surf, "GAME OVER", font_large, RED, WIDTH // 2, 190)
            draw_text(render_surf, f"Final Score: {score}", font_small, WHITE, WIDTH // 2, 255)
            draw_text(render_surf, "Enter your name:", font_small, CYAN, WIDTH // 2, 310)
            box = pygame.Rect(WIDTH // 2 - 130, 345, 260, 42)
            pygame.draw.rect(render_surf, (30, 35, 60), box, border_radius=6)
            pygame.draw.rect(render_surf, CYAN, box, 2, border_radius=6)
            cursor = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else ""
            draw_text(render_surf, name + cursor, font_small, WHITE, WIDTH // 2, box.y + 11)
            draw_text(render_surf, "ENTER to save, ESC to skip", font_small, WHITE, WIDTH // 2, 405)

        # Screen-Shake bei Treffer
        offset_x, offset_y = 0, 0
        if shake > 0:
            offset_x = random.randint(-shake, shake)
            offset_y = random.randint(-shake, shake)
            shake -= 1

        screen.fill(BLACK)
        screen.blit(render_surf, (offset_x, offset_y))
        #updated unser Bild
        pygame.display.flip()
```

## 6. Definition das main am anfang des programmes gerufen werden muss
```python
if __name__ == "__main__":
    main()
    #mainloop, when uner whilestatement stoppt wird pygame.quit ausgeführt und das programm schließt sich
    pygame.quit()
```

## 7. Kurzfassung: Wie das Spiel funktioniert
Die `main()`-Funktion ist der **Spielleiter von Space Invaders Battle**. Sie verwaltet Spieler, Gegnerwellen, Kugeln, Power-Ups und die Menüzustände (`menu`, `playing`, `gameover`, `leaderboard`).

### Wichtige Konzepte im Code
- **`state`-Variable** – entscheidet, was gerade angezeigt wird (Menü, Spiel, Game Over, Bestenliste).
- **`update()`-Methoden** – jede Klasse aktualisiert sich selbst pro Frame (Bewegung, Timer, Leben).
- **`get_rect()`** – liefert ein Rechteck für Kollisionsprüfungen (`colliderect`).
- **Gegnerbewegung** – alle Gegner bewegen sich synchron, drehen am Rand um und rücken dann eine Reihe nach unten. Je weniger Gegner übrig sind, desto schneller werden sie (`speed_boost`).
- **Power-Ups** – fallen von zerstörten Gegnern herunter und geben entweder Dreifachschuss (7 Sekunden) oder einen Schild.
- **Wellen** – sobald alle Gegner zerstört sind, startet eine neue, schnellere Welle.
- **Leaderboard** – wird als JSON-Datei gespeichert und beim Game Over mit dem eingegebenen Namen erweitert.
- **Screen-Shake** – bei Treffer am Spieler wird die ganze Zeichenfläche kurz zufällig verschoben, um einen Impact-Effekt zu erzeugen.