# Erklärungsbauplan für tetris.py

> **Für absolute Anfänger:** Dieses Dokument erklärt das komplette Tetris-Programm Zeile für Zeile. Du musst noch nie etwas mit Python gemacht haben, um es zu verstehen. Wir erklären alle wichtigen Grundbegriffe direkt beim ersten Auftauchen.

---

## 0. Was ist Python und was passiert hier überhaupt?

**Python** ist eine Programmiersprache – also eine Sprache, in der wir dem Computer sagen, was er tun soll. Unser Programm läuft so ab:

1. Wir **importieren** Bibliotheken (fertige Werkzeugkästen, die andere schon geschrieben haben).
2. Wir legen **Konstanten** fest (Werte, die sich nicht ändern, wie die Bildschirmgröße).
3. Wir definieren **Klassen** (Baupläne für Objekte, z. B. „ein Spielstein").
4. Wir bauen eine **Hauptschleife** (englisch: main loop). Das ist ein `while True`-Block, der sich 60 Mal pro Sekunde wiederholt und dafür sorgt, dass sich das Spiel bewegt.

**Wichtige Grundbegriffe:**
- **Variable** = ein Name für einen gespeicherten Wert (z. B. `score = 0`).
- **Funktion** = ein benannter Codeblock, den man mehrfach aufrufen kann (erkennbar an `def name():`).
- **Klasse** = ein Bauplan für Objekte (erkennbar an `class Name:`).
- **Objekt/Instanz** = ein konkretes Ding, das nach einem Bauplan erzeugt wurde (`Piece("I")` erzeugt einen I-Stein).
- **`self`** = „dieses Objekt selbst". Innerhalb einer Klasse greift man mit `self.x` auf die eigene Variable `x` zu.
- **`import`** = „hole mir eine Bibliothek".
- **`for`-Schleife** = wiederhole etwas für jedes Element einer Liste.
- **`if`-Bedingung** = „wenn das hier stimmt, dann tue das".
- **`return`** = „gib diesen Wert zurück" (beendet gleichzeitig eine Funktion).
- **`dt`** = „delta time", die Zeit in Sekunden seit dem letzten Frame. Damit können wir Dinge unabhängig von der Bildrate bewegen.

---

## 1. Importierung der Librarys und Erstellen wichtiger Variablen

```python
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
```

**Was passiert hier?**
- `import json` – Werkzeugkasten zum Speichern/Lesen von Dateien im JSON-Format (für die Bestenliste).
- `import math` – Werkzeugkasten für Mathe (Sinus, Kosinus usw.).
- `import random` – Werkzeugkasten für Zufallszahlen.
- `import pygame` – die Spiele-Bibliothek. Sie kümmert sich um das Fenster, das Zeichnen und die Tastatureingaben.

**Was bedeuten die Großbuchstaben?**
Das sind **Konstanten** – Werte, die sich während des Spiels nicht ändern. In Python ist das nur eine Konvention (Absprache): Großbuchstaben signalisieren „bitte nicht ändern!".

- `CELL = 30` – jeder Spielblock ist 30 Pixel groß.
- `COLS, ROWS = 10, 20` – das Spielfeld ist 10 Felder breit und 20 Felder hoch.
- `BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL` – die Gesamtgröße des Spielfelds in Pixeln.
- `WIDTH, HEIGHT = 500, 600` – die Fenstergröße.
- `CLEAR_TIME = 0.4` – wie lange die Blink-Animation beim Löschen einer Reihe dauert (in Sekunden).
- Die Farben sind **RGB-Tupel**: `(255, 255, 255)` = Rot-, Grün-, Blau-Anteil von 0 bis 255. `(255, 255, 255)` ist Weiß, `(0, 0, 0)` ist Schwarz.

---

## 2. Die Formen der Spielsteine (Tetrominos) und ihre Farben

```python
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
```

**Was ist ein Dictionary (`{...}`)?**
Ein Dictionary (auf Deutsch „Wörterbuch") speichert **Schlüssel-Wert-Paare**. `"I": [[1,1,1,1]]` bedeutet: „Wenn du nach dem Schlüssel `"I"` fragst, bekommst du den Wert `[[1,1,1,1]]`".

- **`SHAPES`** – hier steht für jeden Stein-Typ, wie er aussieht. `1` = Block ist da, `0` = Block ist leer. `[[1,1,1,1]]` ist eine einzelne waagerechte Reihe (der I-Stein). `[[1,1],[1,1]]` ist ein 2×2-Quadrat (der O-Stein).
- **`COLORS`** – jeder Stein-Typ hat eine feste Farbe.
- **`LINE_POINTS`** – wie viele Punkte man für 1, 2, 3 oder 4 gleichzeitig gelöschte Reihen bekommt.
- **`LINE_NAMES`** – der Text, der als Popup erscheint (z. B. „TETRIS!" bei 4 Reihen).

---

## 3. Pygame starten und Schriften laden

```python
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()
small_font = pygame.font.Font(None, 22)
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 48)
title_font = pygame.font.Font(None, 90)
```

- `pygame.init()` – startet alle Pygame-Module (muss ganz am Anfang passieren).
- `screen = pygame.display.set_mode(...)` – erstellt das Fenster und gibt uns ein „Malbrett" namens `screen`. Alles, was wir auf `screen` zeichnen, wird angezeigt.
- `pygame.display.set_caption("Tetris")` – setzt den Fenstertitel.
- `clock = pygame.time.Clock()` – ein Helfer, mit dem wir die Framerate (Bilder pro Sekunde) kontrollieren.
- `pygame.font.Font(None, 22)` – lädt eine Standardschrift in Größe 22. `None` bedeutet „benutze die Standard-Schrift". Vier verschiedene Größen für kleine, normale, große und Titel-Texte.

---

## 4. Zwei kleine Hilfsfunktionen: `cells()` und `rotated()`

```python
def cells(shape, x, y):
    for row_index, row in enumerate(shape):
        for col_index, filled in enumerate(row):
            if filled:
                yield x + col_index, y + row_index


def rotated(shape):
    # rotate 90 degrees clockwise
    return [list(row) for row in zip(*shape[::-1])]
```

**`cells(shape, x, y)` – „Welche Felder sind gefüllt?"**
Diese Funktion nimmt eine Form (z. B. `[[1,1,1,1]]`) und eine Position (`x`, `y`) auf dem Spielfeld. Sie läuft durch jede Zelle der Form und gibt für jede gefüllte Zelle (`if filled:` also `if filled == 1:`) die konkreten Koordinaten zurück.

- `enumerate(shape)` gibt uns zu jedem Element gleich den Index dazu: `row_index` (Zeile) und `row` (die Zeile selbst).
- `yield` ist wie `return`, aber die Funktion kann mehrere Werte nacheinander liefern. Man nennt das einen **Generator**. Das ist praktisch, weil wir dann einfach `for x, y in cells(...)` schreiben können.

**`rotated(shape)` – „Drehe die Form um 90° im Uhrzeigersinn"**
- `shape[::-1]` dreht die Reihenfolge der Zeilen um (die letzte Zeile wird zur ersten).
- `zip(*...)` „kippt" dann die Form so, dass aus Zeilen Spalten werden.
- `[list(row) for row in ...]` macht daraus wieder Listen. Das ist eine sogenannte **List Comprehension** – eine kompakte Schreibweise für „baue eine neue Liste, indem du über etwas iterierst".

Für Anfänger reicht: Diese Funktion dreht einen Stein. Sie wird später beim Drücken der Pfeil-oben-Taste aufgerufen.

---

## 5. Die `Piece`-Klasse – ein fallender Spielstein

```python
class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0
```

**Was ist eine Klasse?**
Eine Klasse ist ein **Bauplan** für Objekte. Hier ist der Bauplan für „einen fallenden Spielstein".

- `__init__(self, kind)` – das ist der **Konstruktor**. Er wird automatisch aufgerufen, wenn wir `Piece("I")` schreiben. `kind` ist der Stein-Typ (also `"I"`, `"O"`, `"T"` …).
- `self.kind = kind` – speichere den Typ im Objekt.
- `self.shape = [row[:] for row in SHAPES[kind]]` – hole die Form aus dem `SHAPES`-Dictionary. `row[:]` ist ein **Kopieren** der Zeile, damit wir die Original-Form nicht versehentlich verändern, wenn wir den Stein drehen.
- `self.x = COLS // 2 - len(self.shape[0]) // 2` – setze den Stein horizontal in die Mitte. `//` ist Ganzzahl-Division (z. B. `5 // 2 = 2`).
- `self.y = 0` – der Stein startet ganz oben.

---

## 6. Die `Particle`-Klasse – Funkeleffekte beim Löschen

```python
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
```

**Zweck:** Jedes Mal, wenn eine Reihe gelöscht wird, entstehen kleine bunte Partikel, die wegfliegen. Das ist reine Optik.

- `self.vx`, `self.vy` – Geschwindigkeit in x- und y-Richtung. `random.uniform(-120, 120)` erzeugt eine zufällige Kommazahl zwischen -120 und 120.
- `self.life = 1.0` – wie lange der Partikel lebt (in Sekunden). Startet bei 1,0.
- **`update(dt)`** – wird jeden Frame aufgerufen:
  - `self.x += self.vx * dt` – bewege den Partikel (Geschwindigkeit × Zeit).
  - `self.vy += 600 * dt` – Schwerkraft: der Partikel wird nach unten beschleunigt.
  - `self.life -= dt * 1.5` – Leben nimmt ab.
- **`draw(surface)`** – zeichnet den Partikel als kleines Quadrat. Die Größe hängt vom Rest-Leben ab, damit er langsam verschwindet.

---

## 7. Die `Game`-Klasse – das Herzstück des Spiels

Das ist die längste und wichtigste Klasse. Sie verwaltet das **gesamte Spielfeld, den aktuellen Stein, den nächsten Stein, den Hold-Stein, Punktestand, Reihen, Partikel** usw.

### 7.1 Der Konstruktor `__init__`

```python
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
```

- `self.board = [[None] * COLS for _ in range(ROWS)]` – das Spielfeld als 2D-Liste. `ROWS` Zeilen mit je `COLS` Feldern, alle mit `None` (leer). Wenn ein Stein landet, wird dort der Stein-Typ (z. B. `"I"`) eingetragen.
- `self.bag = []` – der „Beutel" für die 7-Bag-Randomisierung (siehe unten).
- `self.next = Piece(self.next_kind())` – der nächste Stein, der als Vorschau angezeigt wird.
- `self.hold_kind = None` – der Stein, den man mit `C` aufbewahrt.
- `self.can_hold = True` – man darf pro Stein nur einmal tauschen.
- `self.score = 0`, `self.lines = 0` – Punktestand und Anzahl gelöschter Reihen.
- `self.fall_timer`, `self.held_dir`, `self.repeat_timer` – Timer für das automatische Fallen und das gedrückt-Halten der Pfeiltasten.
- `self.clearing`, `self.clear_timer` – für die Blink-Animation beim Reihen-Löschen.
- `self.particles` – Liste aller aktiven Partikel.
- `self.popup` – der Text, der beim Reihen-Löschen erscheint (z. B. „TETRIS!").
- `self.shake` – Bildschirm-Wackeln bei Aktionen.
- `self.over` – `True`, wenn das Spiel verloren ist.
- `self.spawn()` – setzt den ersten Stein.

### 7.2 Hilfs-Properties: `level` und `playing`

```python
    @property
    def level(self):
        return self.lines // 10 + 1

    @property
    def playing(self):
        return not self.over and not self.clearing
```

- `@property` – macht aus einer Methode eine scheinbare Variable. Man kann also `game.level` schreiben, statt `game.level()` aufzurufen.
- **`level`** – das Level steigt alle 10 gelöschte Reihen.
- **`playing`** – `True`, wenn das Spiel läuft (nicht vorbei und gerade nicht in der Lösch-Animation).

### 7.3 Die 7-Bag-Randomisierung – `next_kind()`

```python
    def next_kind(self):
        # 7-bag: every piece appears once before any repeats
        if not self.bag:
            self.bag = list(SHAPES)
            random.shuffle(self.bag)
        return self.bag.pop()
```

**Idee:** Damit nicht zufällig fünfmal derselbe Stein hintereinander kommt, benutzen wir das „7-Bag"-Verfahren: Wir packen alle 7 Stein-Typen in einen Beutel, mischen sie, und ziehen sie zufällig raus. Erst wenn der Beutel leer ist, wird neu gemischt.

- `list(SHAPES)` – alle Schlüssel (also alle Stein-Typen) als Liste.
- `random.shuffle(self.bag)` – mischt die Liste.
- `self.bag.pop()` – nimmt das letzte Element heraus und gibt es zurück.

### 7.4 Der nächste Stein – `take_next()` und `spawn()`

```python
    def take_next(self):
        piece, self.next = self.next, Piece(self.next_kind())
        return piece

    def spawn(self):
        self.piece = self.take_next()
        self.can_hold = True
        if not self.fits(self.piece.shape, self.piece.x, self.piece.y):
            self.over = True
```

- **`take_next`** – der aktuelle `next`-Stein wird zum aktuellen Stein, ein neuer `next` wird gezogen. Das ist eine „Tausch"-Operation.
- **`spawn`** – setzt den aktuellen Stein. Wenn er **nicht** an seine Startposition passt, ist das Spielfeld voll → Spiel vorbei (`self.over = True`).

### 7.5 Kollisionsprüfung – `fits()`

```python
    def fits(self, shape, x, y):
        for cx, cy in cells(shape, x, y):
            if cx < 0 or cx >= COLS or cy >= ROWS or self.board[cy][cx]:
                return False
        return True
```

Diese Funktion sagt, ob eine Form an einer bestimmten Position **eingefügt werden darf**:

- `cx < 0` – links raus.
- `cx >= COLS` – rechts raus.
- `cy >= ROWS` – unten raus.
- `self.board[cy][cx]` – dort liegt schon ein Block.

Wenn irgendeine dieser Bedingungen zutrifft → `False` (passt nicht). Sonst `True`.

### 7.6 Bewegung und Drehung – `move()` und `rotate()`

```python
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
```

- **`move(dx)`** – verschiebt den Stein um `dx` nach links (dx=-1) oder rechts (dx=+1), **wenn es passt**.
- **`rotate()`** – dreht die Form und probiert mehrere „Kicks" aus (Verschiebungen), falls der Stein neben einer Wand steht. Das nennt man **Wall Kick**: Man versucht, den gedrehten Stein minimal nach links/rechts zu schieben, damit die Drehung nicht an der Wand scheitert.

### 7.7 Hold-Tausch – `swap_hold()`

```python
    def swap_hold(self):
        if not self.can_hold:
            return
        kind = self.piece.kind
        self.piece = Piece(self.hold_kind) if self.hold_kind else self.take_next()
        self.hold_kind = kind
        self.can_hold = False
```

- **`if not self.can_hold: return`** – man darf pro fallendem Stein nur einmal tauschen.
- Der aktuelle Stein-Typ wird gemerkt (`kind`).
- Wenn schon ein Hold-Stein existiert → nimm diesen als neuen aktuellen Stein. Sonst → nimm den nächsten aus der Schlange.
- Der gemerkte Typ wird zum neuen Hold-Stein.
- `can_hold = False` sperrt einen weiteren Tausch, bis der nächste Stein spawnt.

### 7.8 Ghost-Stein – `ghost_y()`

```python
    def ghost_y(self):
        y = self.piece.y
        while self.fits(self.piece.shape, self.piece.x, y + 1):
            y += 1
        return y
```

Das ist die **Vorschau**, wo der Stein landen würde (der „Geist"). Wir schieben den Stein so weit nach unten wie möglich und geben die y-Position zurück.

### 7.9 Fallen und Landen – `step_down()`, `hard_drop()`, `lock()`

```python
    def step_down(self):
        if self.fits(self.piece.shape, self.piece.x, self.piece.y + 1):
            self.piece.y += 1
            return True
        self.lock()
        return False
```

- **`step_down()`** – versucht, einen Schritt nach unten zu gehen. Wenn es nicht geht, wird der Stein **eingelockt** (also fest im Board verbaut).

```python
    def hard_drop(self):
        start = self.piece.y
        self.piece.y = self.ghost_y()
        self.score += 2 * (self.piece.y - start)
        self.shake = 0.15
        for cx, cy in cells(self.piece.shape, self.piece.x, self.piece.y):
            self.burst(cx * CELL + CELL // 2, (cy + 1) * CELL, COLORS[self.piece.kind], 3)
        self.lock()
```

- **`hard_drop()`** – der Stein fällt sofort ganz nach unten (Leertaste).
- Es gibt Bonuspunkte: 2 pro Feld, das er gefallen ist.
- Kleiner Bildschirm-Wackler (`shake = 0.15`).
- Kleine Partikel-Bursts an der Landestelle.
- Am Ende wird `lock()` aufgerufen.

```python
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
```

- Der Stein wird ins Board eingetragen.
- `self.piece = None` – es gibt jetzt keinen fallenden Stein.
- `full` – alle Reihen, die komplett gefüllt sind (`all(row)` = alle Felder in der Reihe sind nicht-None).
- Wenn keine volle Reihe → sofort nächster Stein spawnen.
- Sonst: Löschanimation vorbereiten.
  - `self.clearing` merkt sich, welche Reihen gelöscht werden.
  - `self.clear_timer` startet den Timer.
  - `self.popup` zeigt den Text (z. B. „TETRIS!").
  - Partikel für jede Zelle der vollen Reihen.

### 7.10 Löschen abschließen – `finish_clear()`

```python
    def finish_clear(self):
        count = len(self.clearing)
        kept = [row for r, row in enumerate(self.board) if r not in self.clearing]
        self.board = [[None] * COLS for _ in range(count)] + kept
        self.score += LINE_POINTS[count] * self.level
        self.lines += count
        self.clearing = []
        self.spawn()
```

- `count` – wie viele Reihen wurden gelöscht.
- `kept` – alle Reihen, die bleiben.
- `[[None] * COLS for _ in range(count)] + kept` – oben neue leere Reihen einfügen, dann die übrigen darunter hängen.
- Punkte addieren (multipliziert mit Level).
- `self.lines += count` – Reihen-Zähler erhöhen.
- `clearing` zurücksetzen und nächsten Stein spawnen.

### 7.11 Partikel erzeugen – `burst()`

```python
    def burst(self, x, y, color, count):
        self.particles += [Particle(x, y, color) for _ in range(count)]
```

Erzeugt `count` neue Partikel an der Position `(x, y)` mit der Farbe `color`.

### 7.12 Automatisches Bewegen bei gedrückter Taste – `handle_held_keys()`

```python
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
```

- `keys[pygame.K_RIGHT]` ist `1` wenn rechts gedrückt, sonst `0`. Gleiches für links. `1 - 0 = 1` (rechts), `0 - 1 = -1` (links), `1 - 1 = 0` (nichts).
- Wenn sich die Richtung ändert → sofort bewegen (kein Delay).
- Wenn die Richtung gleich bleibt und ungleich 0 → nach 0,15 Sekunden automatisch wiederholen. Das ist das „Dauerfeuer" beim Halten der Pfeiltaste.

### 7.13 Die Hauptupdate-Methode – `update(dt, keys)`

```python
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
```

Das ist die Funktion, die **jeden Frame** aufgerufen wird und alles am Laufen hält:

1. **Shake-Timer herunterzählen.**
2. **Partikel updaten** und tote entfernen.
3. **Popup-Timer** herunterzählen.
4. **Wenn gerade Reihen gelöscht werden:** Timer laufen lassen, bei 0 → `finish_clear()`.
5. **Sonst, wenn Spiel läuft:**
   - Gedrückt-gehaltene Pfeiltasten verarbeiten.
   - `soft` – ist die Runter-Taste gedrückt? Dann fällt der Stein schneller.
   - `interval` – wie lange zwischen zwei automatischen Falls passiert (kleiner = schneller). Wird mit Level kleiner.
   - Wenn `fall_timer` groß genug → `step_down()` aufrufen. Bei Soft-Drop gibt's 1 Punkt pro Feld.

---

## 8. Die `Button`-Klasse – klickbare Menüknöpfe

```python
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
```

- `pygame.Rect(x, y, w, h)` – ein Rechteck an Position `(x, y)` mit Breite `w` und Höhe `h`.
- `self.rect.collidepoint(mouse_pos)` – prüft, ob die Maus im Rechteck ist.
- **`draw()`** – wenn die Maus drüber ist, wird der Button weiß, sonst blau. Der Text wird zentriert reingeschrieben.
- **`clicked(pos)`** – wurde der Button an der Position `pos` geklickt?

**Anfänger-Tipp:** Diese Klasse ist ein Muster, das du in jedem Menü wiederverwenden kannst. Einfach `Button("Start", x, y)` erstellen und im Event-Loop `button.clicked(event.pos)` abfragen.

---

## 9. Helferfunktionen für Bestenliste, Text und Zeichnen

### 9.1 Bestenliste laden und speichern

```python
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
```

- **`open(DATEI)`** – öffnet eine Datei. `with` sorgt dafür, dass sie automatisch wieder geschlossen wird.
- **`json.load(f)`** – liest JSON-Daten aus der Datei und wandelt sie in Python-Listen/Dictionaries um.
- **`try/except`** – probiere etwas; wenn ein Fehler passiert (`Datei existiert nicht`, `Datei kaputt`), mache stattdessen das in `except`. Hier: gib eine leere Liste zurück.
- **`scores.append({...})`** – fügt einen neuen Eintrag hinzu.
- **`sorted(..., key=lambda s: s["score"], reverse=True)`** – sortiert absteigend nach Score. `lambda` ist eine Kurz-Funktion.
- **`[:10]`** – nur die ersten 10 behalten.
- **`json.dump(scores, f, indent=2)`** – schreibt die Liste formatiert in die Datei zurück.

### 9.2 Text zeichnen – `draw_text()`

```python
def draw_text(text, text_font, color, cx, y, alpha=255):
    surf = text_font.render(text, True, color)
    surf.set_alpha(alpha)
    screen.blit(surf, (int(cx - surf.get_width() / 2), int(y)))
```

- `text_font.render(text, True, color)` – wandelt Text in ein Bild um.
- `surf.set_alpha(alpha)` – setzt die Transparenz (255 = voll sichtbar, 0 = unsichtbar).
- `screen.blit(surf, position)` – „klebt" das Bild auf den Bildschirm. `blit` ist das Standard-Wort in Pygame für „draufmalen".
- Der x-Wert wird halbiert, damit der Text **zentriert** ist.

### 9.3 Einzelne Zelle zeichnen – `draw_cell()`

```python
def draw_cell(surface, x, y, color, size=CELL):
    rect = pygame.Rect(x + 1, y + 1, size - 2, size - 2)
    pygame.draw.rect(surface, color, rect, border_radius=4)
    lighter = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surface, lighter, rect, 2, border_radius=4)
```

- Zeichnet einen farbigen Block mit abgerundeten Ecken.
- `lighter` – eine hellere Variante der Farbe (jeder Kanal wird um 60 erhöht, maximal 255), die als 2-Pixel-Rahmen drumherum gezeichnet wird. Das lässt den Stein plastischer aussehen.

### 9.4 Eine ganze Form zeichnen – `draw_shape()`

```python
def draw_shape(kind, shape, cx, cy, size, color=None):
    left = cx - len(shape[0]) * size // 2
    top = cy - len(shape) * size // 2
    for x, y in cells(shape, 0, 0):
        draw_cell(screen, left + x * size, top + y * size, color or COLORS[kind], size)
```

- `cx, cy` ist der Mittelpunkt, an dem die Form gezeichnet werden soll (z. B. für den „Next"-Vorschau-Bereich).
- `left, top` – linke obere Ecke berechnen, damit die Form um `(cx, cy)` zentriert ist.
- `color or COLORS[kind]` – wenn `color` übergeben wurde, nimm den, sonst die Standardfarbe des Typs. Das ist ein typisches Python-Idiom: „nimm das, oder fallback".

### 9.5 Das Spielfeld zeichnen – `draw_board()`

```python
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
```

Das ist die Funktion, die das **eigentliche Spielfeld** malt (ohne das Seitenpanel):

1. Neue **`Surface`** erstellen – das ist ein leeres Malbrett in der Größe des Spielfelds.
2. **Gitterlinien** zeichnen (jede Zelle 30 Pixel).
3. **Verbaute Steine** aus `game.board` zeichnen. Wenn eine Reihe gerade gelöscht wird (`flash`), blinkt sie weiß.
4. **Ghost-Stein** – nur als Umriss (`pygame.draw.rect(..., 2, ...)`) mit Dicke 2.
5. **Aktueller Stein** – als gefüllte Zellen.
6. **Partikel** obendrauf.
7. Die komplette Surface **zurückgeben** (der Aufrufer blittet sie dann an die richtige Stelle).

### 9.6 Das Seitenpanel zeichnen – `draw_panel()`

```python
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
```

Zeichnet rechts neben dem Spielfeld:
- **Next** – Vorschau des nächsten Steins.
- **Hold** – aufbewahrter Stein (ausgegraut, wenn man ihn gerade nicht tauschen darf).
- **Score/Level/Lines** – Zahlen zum aktuellen Spiel.
- **Steuerungshinweise** – welche Tasten was tun.

### 9.7 Overlays (dunkle Schichten) und Menüs

```python
def draw_overlay(alpha):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, (0, 0))
```

- Erstellt eine **transparente schwarze Fläche** und legt sie über das ganze Fenster. Damit kann man Inhalte dahinter abdunkeln. `pygame.SRCALPHA` erlaubt Transparenz.

```python
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
```

- Zeigt Game-Over-Overlay.
- Ein **Eingabefeld** für den Namen (Rechteck mit Rahmen).
- `cursor` – ein blinkender Strich. `pygame.time.get_ticks() // 500 % 2` ist alle 500 Millisekunden abwechselnd 0 und 1 → blinkt zweimal pro Sekunde.

```python
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
```

- Zeichnet den Hintergrund mit **schwebenden, abgedunkelten Steinen**.
- **Titel „TETRIS"** mit bunten Buchstaben, die per Sinuswelle auf und ab wippen. `math.sin(t * 3 + i)` erzeugt eine wellenförmige Bewegung.
- Zum Schluss alle Buttons.

```python
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
```

- Zeigt die Top 10.
- Platz 1 = **Gold**, Platz 2–3 = **Blau (Accent)**, Rest weiß.

---

## 10. Die `main()`-Funktion – die Hauptschleife des Spiels

Das ist der Einstiegspunkt. Die Funktion wird ganz unten aufgerufen.

### 10.1 Vorbereitung – Buttons, Deko, Zustand

```python
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
```

- **`state`** – in welchem Menü sind wir? Start: `"menu"`. Andere Werte: `"game"`, `"gameover"`, `"leaderboard"`.
- **`game`** – das aktuell laufende Spiel (anfangs `None`).
- **`paused`** – ist pausiert?
- **`name`** – der eingegebene Spielername.
- Buttons werden erstellt (Position, Text).
- **`decor`** – 12 zufällige Steine, die als Hintergrund-Deko im Menü herumfliegen. Jeder ist ein Dictionary mit Typ, Position und Geschwindigkeit.

### 10.2 Die Hauptschleife

```python
    while True:
        dt = clock.tick(60) / 1000
```

- **`while True:`** – Endlosschleife. Sie wiederholt sich, bis das Programm geschlossen wird.
- **`clock.tick(60)`** – begrenzt das Spiel auf 60 Frames pro Sekunde. Gibt die Millisekunden seit dem letzten Frame zurück.
- **`/ 1000`** – wandelt in Sekunden um → das ist unser `dt`.

### 10.3 Events verarbeiten

```python
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
```

**Was ist ein Event?**
Ein Event ist ein **Ereignis** wie Mausklick, Tastendruck oder Fenster schließen. `pygame.event.get()` liefert alle Events seit dem letzten Frame. Wir gehen sie mit `for` durch.

- **`pygame.QUIT`** – das Fenster-Kreuz wurde geklickt → `return` beendet `main()`.
- **`state == "menu"`** – im Menü reagieren wir auf **Mausklicks**. Je nach Button ändert sich der `state`.
- **`state == "game"`** – im Spiel reagieren wir auf **Tastendrücke**:
  - `ESC` → zurück ins Menü.
  - `P` → Pause an/aus.
  - Pfeiltasten / Leertaste / C → Steuerung.
  - `game.playing` prüft, ob Steuerung erlaubt ist (nicht wenn gerade Reihen blinken oder Spiel vorbei).
- **`state == "gameover"`** – Tippen für den Namen:
  - `ENTER` → Score speichern, zur Bestenliste.
  - `ESC` → Menü.
  - `BACKSPACE` → letzten Buchstaben löschen (`name[:-1]` = alles außer dem letzten Zeichen).
  - Sonstige druckbare Zeichen anhängen (max. 16 Zeichen).

### 10.4 Zustand aktualisieren und zeichnen

```python
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
```

- **Menü:** Deko-Steine fallen nach unten (Geschwindigkeit × Zeit). Wenn sie unten raus sind, kommen sie oben neu rein.
- **Leaderboard:** einfach zeichnen.
- **Spiel/Game Over:**
  - Wenn wir im Spiel sind und **nicht pausiert**: `game.update()` aufrufen.
  - Wenn das Spiel vorbei ist → Zustand zu `"gameover"` wechseln.
  - Danach wird immer gezeichnet.
- **`pygame.display.flip()`** – **wichtig!** Das zeigt alles, was wir gezeichnet haben, im Fenster an. Ohne `flip()` siehst du nichts.

**Tipp für Anfänger:** Diese Dreiteilung — **Events → Update → Draw** — ist das Standard-Muster für Spiele. Merk dir das; du wirst es in jedem Pygame-Projekt wiederfinden.

---

## 11. Der Einstiegspunkt – wann startet das Spiel?

```python
if __name__ == "__main__":
    main()
    pygame.quit()
```

- **`if __name__ == "__main__":`** – das ist eine spezielle Python-Konvention. Sie sorgt dafür, dass der folgende Code **nur dann** läuft, wenn die Datei **direkt** gestartet wird (nicht, wenn sie von einer anderen Datei importiert wird).
- `main()` – startet das Spiel.
- `pygame.quit()` – wird erreicht, wenn `main()` durch `return` beendet wurde → Pygame räumt auf. Danach endet das Programm.

---

## 12. Kurzfassung – was du dir merken solltest

Wenn du das ganze Skript auf einen Blick verstehen willst:

1. **Konstanten** (Farben, Größen) und **Dictionaries** (SHAPES, COLORS) legen die Spielregeln fest.
2. **Klassen** (`Piece`, `Particle`, `Game`, `Button`) sind Baupläne für Objekte mit eigenem Zustand und Verhalten.
3. **Die `Game`-Klasse** ist das Herzstück: Sie kennt das Board, den aktuellen Stein, den nächsten Stein, den Hold, Punkte und Partikel.
4. **`main()`** ist die Hauptschleife: Sie verarbeitet Events, ruft `game.update()` auf und zeichnet alles.
5. **Wichtige Konzepte**, die du in jedem Spiel brauchst:
   - `dt` – Zeit seit letztem Frame, damit sich alles gleich schnell bewegt (egal wie schnell der Computer ist).
   - **Kollisionsprüfung** mit `fits()`.
   - **Ghost-Stein** – zeigt, wo der Stein landet.
   - **7-Bag-Randomisierung** – sorgt für fairere Stein-Verteilung.
   - **Wall Kicks** – damit Drehungen an der Wand funktionieren.
   - **Screen Shake** und **Partikel** – reine Optik, die das Spiel „lebendig" aussehen lässt.
6. **Leaderboard** – wird mit `json` als Textdatei gespeichert.
