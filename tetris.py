from collections import OrderedDict
import random
import json
import os

from pygame import Rect
import pygame
import numpy as np

WINDOW_WIDTH, WINDOW_HEIGHT = 500, 601
GRID_WIDTH, GRID_HEIGHT = 300, 600
TILE_SIZE = 30
LEADERBOARD_FILE = "leaderboard.json"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
DARK = (20, 20, 20)
ACCENT = (0, 200, 255)
HIGHLIGHT = (255, 220, 0)
MENU_BG = (15, 15, 25)


def remove_empty_columns(arr, _x_offset=0, _keep_counting=True):
    for colid, col in enumerate(arr.T):
        if col.max() == 0:
            if _keep_counting:
                _x_offset += 1
            arr, _x_offset = remove_empty_columns(
                np.delete(arr, colid, 1), _x_offset, _keep_counting)
            break
        else:
            _keep_counting = False
    return arr, _x_offset


class BottomReached(Exception):
    pass


class TopReached(Exception):
    pass


class Block(pygame.sprite.Sprite):

    @staticmethod
    def collide(block, group):
        for other_block in group:
            if block == other_block:
                continue
            if pygame.sprite.collide_mask(block, other_block) is not None:
                return True
        return False

    def __init__(self):
        super().__init__()
        self.color = random.choice((
            (200, 200, 200),
            (215, 133, 133),
            (30, 145, 255),
            (0, 170, 0),
            (180, 0, 140),
            (200, 200, 0),
            (255, 140, 0),
            (0, 200, 200),
        ))
        self.current = True
        self.struct = np.array(self.struct)
        if random.randint(0, 1):
            self.struct = np.rot90(self.struct)
        if random.randint(0, 1):
            self.struct = np.flip(self.struct, 0)
        self._draw()

    def _draw(self, x=4, y=0):
        width = len(self.struct[0]) * TILE_SIZE
        height = len(self.struct) * TILE_SIZE
        self.image = pygame.surface.Surface([width, height], pygame.SRCALPHA)
        self.rect = Rect(0, 0, width, height)
        self.x = x
        self.y = y
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    r = Rect(x*TILE_SIZE + 1, y*TILE_SIZE + 1,
                             TILE_SIZE - 2, TILE_SIZE - 2)
                    pygame.draw.rect(self.image, self.color, r, border_radius=4)
                    lighter = tuple(min(255, c + 60) for c in self.color)
                    pygame.draw.rect(self.image, lighter, r, width=2, border_radius=4)
        self._create_mask()

    def redraw(self):
        self._draw(self.x, self.y)

    def _create_mask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def draw_ghost(self, screen, target_y):
        ghost_surf = pygame.surface.Surface(
            (len(self.struct[0]) * TILE_SIZE, len(self.struct) * TILE_SIZE),
            pygame.SRCALPHA)
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    r = Rect(x*TILE_SIZE + 2, y*TILE_SIZE + 2,
                             TILE_SIZE - 4, TILE_SIZE - 4)
                    ghost_color = (*self.color, 90)
                    pygame.draw.rect(ghost_surf, ghost_color, r, border_radius=4)
                    border = (*self.color, 160)
                    pygame.draw.rect(ghost_surf, border, r, width=2, border_radius=4)
        screen.blit(ghost_surf, (int(self.x * TILE_SIZE), int(target_y * TILE_SIZE)))

    def initial_draw(self):
        raise NotImplementedError

    @property
    def group(self):
        return self.groups()[0]

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value*TILE_SIZE

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.rect.top = value*TILE_SIZE

    def move_left(self, group):
        self.x -= 1
        if self.x < 0 or Block.collide(self, group):
            self.x += 1

    def move_right(self, group):
        self.x += 1
        if self.rect.right > GRID_WIDTH or Block.collide(self, group):
            self.x -= 1

    def move_down(self, group):
        self.y += 1
        if self.rect.bottom > GRID_HEIGHT or Block.collide(self, group):
            self.y -= 1
            self.current = False
            raise BottomReached

    def rotate(self, group):
        self.image = pygame.transform.rotate(self.image, 90)
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self._create_mask()
        while self.rect.right > GRID_WIDTH:
            self.x -= 1
        while self.rect.left < 0:
            self.x += 1
        while self.rect.bottom > GRID_HEIGHT:
            self.y -= 1
        while True:
            if not Block.collide(self, group):
                break
            self.y -= 1
        self.struct = np.rot90(self.struct)

    def update(self):
        if self.current:
            self.move_down()


class SquareBlock(Block):
    struct = ((1, 1), (1, 1))


class TBlock(Block):
    struct = ((1, 1, 1), (0, 1, 0))


class LineBlock(Block):
    struct = ((1,), (1,), (1,), (1,))


class LBlock(Block):
    struct = ((1, 1), (1, 0), (1, 0))


class JBlock(Block):
    struct = ((1, 1), (0, 1), (0, 1))


class ZBlock(Block):
    struct = ((0, 1), (1, 1), (1, 0))


class SBlock(Block):
    struct = ((1, 0), (1, 1), (0, 1))


class TSpinBlock(Block):
    struct = ((0, 1, 0), (1, 1, 1), (0, 0, 0))


class BlocksGroup(pygame.sprite.OrderedUpdates):

    @staticmethod
    def get_random_block():
        return random.choice(
            (SquareBlock, TBlock, LineBlock, LBlock, JBlock,
             ZBlock, SBlock, TSpinBlock))()

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self._reset_grid()
        self._ignore_next_stop = False
        self.score = 0
        self.next_block = None
        self.lines_cleared = 0
        self.stop_moving_current_block()
        self._create_new_block()

    def _check_line_completion(self):
        for i, row in enumerate(self.grid[::-1]):
            if all(row):
                self.score += 5
                self.lines_cleared += 1
                affected_blocks = list(
                    OrderedDict.fromkeys(self.grid[-1 - i]))
                for block, y_offset in affected_blocks:
                    block.struct = np.delete(block.struct, y_offset, 0)
                    if block.struct.any():
                        block.struct, x_offset = \
                            remove_empty_columns(block.struct)
                        block.x += x_offset
                        block.redraw()
                    else:
                        self.remove(block)
                for block in self:
                    if block.current:
                        continue
                    while True:
                        try:
                            block.move_down(self)
                        except BottomReached:
                            break
                self.update_grid()
                self._check_line_completion()
                break

    def _reset_grid(self):
        self.grid = [[0 for _ in range(10)] for _ in range(20)]

    def _create_new_block(self):
        new_block = self.next_block or BlocksGroup.get_random_block()
        if Block.collide(new_block, self):
            raise TopReached
        self.add(new_block)
        self.next_block = BlocksGroup.get_random_block()
        self.update_grid()
        self._check_line_completion()

    def update_grid(self):
        self._reset_grid()
        for block in self:
            for y_offset, row in enumerate(block.struct):
                for x_offset, digit in enumerate(row):
                    if digit == 0:
                        continue
                    rowid = block.y + y_offset
                    colid = block.x + x_offset
                    self.grid[rowid][colid] = (block, y_offset)

    def _can_place(self, block, y, x):
        rows = len(block.struct)
        cols = len(block.struct[0])
        for by in range(rows):
            for bx in range(cols):
                if block.struct[by][bx] == 0:
                    continue
                gy = int(y) + by
                gx = int(x) + bx
                if gy >= 20 or gx < 0 or gx >= 10:
                    return False
                cell = self.grid[gy][gx]
                if cell != 0 and cell[0] != block:
                    return False
        return True

    def get_landing_y(self):
        block = self.current_block
        y = block.y
        while self._can_place(block, y + 1, block.x):
            y += 1
        return y

    @property
    def current_block(self):
        return self.sprites()[-1]

    def update_current_block(self):
        try:
            self.current_block.move_down(self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()

    def move_current_block(self):
        if self._current_block_movement_heading is None:
            return
        action = {
            pygame.K_DOWN: self.current_block.move_down,
            pygame.K_LEFT: self.current_block.move_left,
            pygame.K_RIGHT: self.current_block.move_right
        }
        try:
            action[self._current_block_movement_heading](self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()

    def start_moving_current_block(self, key):
        if self._current_block_movement_heading is not None:
            self._ignore_next_stop = True
        self._current_block_movement_heading = key

    def stop_moving_current_block(self):
        if self._ignore_next_stop:
            self._ignore_next_stop = False
        else:
            self._current_block_movement_heading = None

    def rotate_current_block(self):
        if not isinstance(self.current_block, SquareBlock):
            self.current_block.rotate(self)
            self.update_grid()


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.life = 1.0
        self.color = color
        self.size = random.randint(2, 5)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 8 * dt
        self.life -= dt * 1.5

    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * min(1, self.life))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class Button:
    def __init__(self, text, x, y, w, h, color=ACCENT, hover_color=WHITE):
        self.text = text
        self.rect = Rect(x, y, w, h)
        self.color = color
        self.hover_color = hover_color
        self.hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        surf = font.render(self.text, True, BLACK)
        screen.blit(surf, (self.rect.centerx - surf.get_width()//2,
                           self.rect.centery - surf.get_height()//2))

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def check_click(self, pos):
        return self.rect.collidepoint(pos)


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_leaderboard(leaderboard):
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f, indent=2)
    except IOError:
        pass


def add_to_leaderboard(name, score):
    lb = load_leaderboard()
    lb.append({"name": name, "score": score})
    lb.sort(key=lambda x: x["score"], reverse=True)
    lb = lb[:10]
    save_leaderboard(lb)
    return lb


def draw_grid(background):
    grid_color = (40, 40, 50)
    for i in range(11):
        x = TILE_SIZE * i
        pygame.draw.line(background, grid_color, (x, 0), (x, GRID_HEIGHT))
    for i in range(21):
        y = TILE_SIZE * i
        pygame.draw.line(background, grid_color, (0, y), (GRID_WIDTH, y))


def draw_centered_surface(screen, surface, y):
    screen.blit(surface, (400 - surface.get_width()//2, y))


def draw_rounded_rect(surface, color, rect, radius=8):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def main():
    pygame.init()
    pygame.display.set_caption("Tetris")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    try:
        font = pygame.font.Font("Roboto-Regular.ttf", 20)
        title_font = pygame.font.Font("Roboto-Regular.ttf", 48)
        big_font = pygame.font.Font("Roboto-Regular.ttf", 36)
        small_font = pygame.font.Font("Roboto-Regular.ttf", 16)
    except OSError:
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        title_font = pygame.font.Font(pygame.font.get_default_font(), 48)
        big_font = pygame.font.Font(pygame.font.get_default_font(), 36)
        small_font = pygame.font.Font(pygame.font.get_default_font(), 16)

    background = pygame.Surface(screen.get_size())
    background.fill(BLACK)
    draw_grid(background)
    background = background.convert()

    state = "menu"
    paused = False
    game_over = False
    player_name = ""
    name_input_active = False
    particles = []

    start_btn = Button("Start Game", 175, 250, 150, 45)
    leaderboard_btn = Button("Leaderboard", 175, 310, 150, 45)
    quit_btn = Button("Quit", 175, 370, 150, 45)
    back_btn = Button("Back", 175, 520, 150, 45)
    menu_buttons = [start_btn, leaderboard_btn, quit_btn]

    MOVEMENT_KEYS = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN
    EVENT_UPDATE_CURRENT_BLOCK = pygame.USEREVENT + 1
    EVENT_MOVE_CURRENT_BLOCK = pygame.USEREVENT + 2
    pygame.time.set_timer(EVENT_UPDATE_CURRENT_BLOCK, 1000)
    pygame.time.set_timer(EVENT_MOVE_CURRENT_BLOCK, 100)

    blocks = None
    run = True

    def reset_game():
        nonlocal blocks, game_over, paused, particles
        blocks = BlocksGroup()
        game_over = False
        paused = False
        particles = []

    while run:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if state == "menu":
                if event.type == pygame.MOUSEMOTION:
                    for btn in menu_buttons:
                        btn.check_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_btn.check_click(event.pos):
                        reset_game()
                        state = "game"
                    elif leaderboard_btn.check_click(event.pos):
                        state = "leaderboard"
                    elif quit_btn.check_click(event.pos):
                        run = False
                        break

            elif state == "leaderboard":
                if event.type == pygame.MOUSEMOTION:
                    back_btn.check_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_btn.check_click(event.pos):
                        state = "menu"

            elif state == "game" and game_over:
                if event.type == pygame.KEYDOWN:
                    if name_input_active:
                        if event.key == pygame.K_RETURN:
                            name = player_name.strip() or "Anonymous"
                            add_to_leaderboard(name, blocks.score)
                            name_input_active = False
                            state = "leaderboard"
                        elif event.key == pygame.K_BACKSPACE:
                            player_name = player_name[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            name_input_active = False
                            state = "menu"
                        elif event.unicode and event.unicode.isprintable():
                            if len(player_name) < 24:
                                player_name += event.unicode
                    else:
                        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                            state = "menu"

            elif state == "game":
                if event.type == pygame.KEYUP:
                    if not paused:
                        if event.key in MOVEMENT_KEYS:
                            blocks.stop_moving_current_block()
                        elif event.key == pygame.K_UP:
                            blocks.rotate_current_block()
                    if event.key == pygame.K_p:
                        paused = not paused
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"

                if paused:
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key in MOVEMENT_KEYS:
                        blocks.start_moving_current_block(event.key)

                try:
                    if event.type == EVENT_UPDATE_CURRENT_BLOCK:
                        blocks.update_current_block()
                    elif event.type == EVENT_MOVE_CURRENT_BLOCK:
                        blocks.move_current_block()
                except TopReached:
                    game_over = True
                    name_input_active = True
                    player_name = ""

        if state == "menu":
            screen.fill(MENU_BG)
            t = pygame.time.get_ticks() / 1000.0
            pulse = 0.5 + 0.5 * abs(pygame.math.Vector2(1, 0).rotate(t * 60).x)
            r = max(0, min(255, int(ACCENT[0] * pulse + 100)))
            g = max(0, min(255, int(ACCENT[1] * pulse + 100)))
            b = 255
            title_color = (r, g, b)
            title = title_font.render("TETRIS", True, title_color)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 120))
            sub = small_font.render("Modern Edition", True, (150, 150, 170))
            screen.blit(sub, (WINDOW_WIDTH//2 - sub.get_width()//2, 180))
            for btn in menu_buttons:
                btn.draw(screen, font)

        elif state == "leaderboard":
            screen.fill(MENU_BG)
            title = big_font.render("LEADERBOARD", True, ACCENT)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 40))
            lb = load_leaderboard()
            if not lb:
                msg = font.render("No scores yet!", True, (150, 150, 170))
                screen.blit(msg, (WINDOW_WIDTH//2 - msg.get_width()//2, 200))
            else:
                for i, entry in enumerate(lb):
                    y = 110 + i * 35
                    rank_color = HIGHLIGHT if i == 0 else (ACCENT if i < 3 else WHITE)
                    rank = small_font.render(f"#{i+1}", True, rank_color)
                    name = font.render(entry["name"][:24], True, WHITE)
                    score = font.render(str(entry["score"]), True, rank_color)
                    screen.blit(rank, (140, y))
                    screen.blit(name, (180, y))
                    screen.blit(score, (380 - score.get_width(), y))
            back_btn.draw(screen, font)

        elif state == "game":
            screen.blit(background, (0, 0))

            if not game_over and blocks is not None:
                try:
                    landing_y = blocks.get_landing_y()
                    if int(landing_y) != int(blocks.current_block.y):
                        blocks.current_block.draw_ghost(screen, landing_y)
                except Exception:
                    pass

            blocks.draw(screen)

            for p in particles:
                p.draw(screen)

            draw_rounded_rect(screen, (30, 30, 40), Rect(310, 0, 190, 601))
            pygame.draw.line(screen, ACCENT, (310, 0), (310, 601), 2)

            next_text = font.render("Next", True, WHITE)
            screen.blit(next_text, (400 - next_text.get_width()//2, 20))
            if blocks and blocks.next_block:
                draw_centered_surface(screen, blocks.next_block.image, 60)

            score_label = font.render("Score", True, WHITE)
            screen.blit(score_label, (400 - score_label.get_width()//2, 240))
            score_val = big_font.render(str(blocks.score), True, HIGHLIGHT)
            screen.blit(score_val, (400 - score_val.get_width()//2, 270))

            lines_label = font.render("Lines", True, WHITE)
            screen.blit(lines_label, (400 - lines_label.get_width()//2, 340))
            lines_val = font.render(str(blocks.lines_cleared), True, ACCENT)
            screen.blit(lines_val, (400 - lines_val.get_width()//2, 370))

            if paused:
                overlay = pygame.Surface((GRID_WIDTH, GRID_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))
                pause_text = big_font.render("PAUSED", True, WHITE)
                screen.blit(pause_text, (GRID_WIDTH//2 - pause_text.get_width()//2,
                                         GRID_HEIGHT//2 - pause_text.get_height()//2))
                hint = small_font.render("Press P to resume", True, (150, 150, 170))
                screen.blit(hint, (GRID_WIDTH//2 - hint.get_width()//2,
                                   GRID_HEIGHT//2 + 40))

            if game_over:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                go_text = big_font.render("GAME OVER", True, (255, 80, 80))
                screen.blit(go_text, (WINDOW_WIDTH//2 - go_text.get_width()//2, 150))
                final_score = font.render(f"Final Score: {blocks.score}", True, WHITE)
                screen.blit(final_score, (WINDOW_WIDTH//2 - final_score.get_width()//2, 210))

                if name_input_active:
                    prompt = font.render("Enter your name:", True, ACCENT)
                    screen.blit(prompt, (WINDOW_WIDTH//2 - prompt.get_width()//2, 270))
                    input_rect = Rect(WINDOW_WIDTH//2 - 120, 310, 240, 40)
                    pygame.draw.rect(screen, (40, 40, 60), input_rect, border_radius=6)
                    pygame.draw.rect(screen, ACCENT, input_rect, 2, border_radius=6)
                    cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                    name_surf = font.render(player_name + cursor, True, WHITE)
                    screen.blit(name_surf, (input_rect.x + 10, input_rect.y + 8))
                    hint = small_font.render("ENTER to save, ESC to skip", True, (150, 150, 170))
                    screen.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, 365))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()