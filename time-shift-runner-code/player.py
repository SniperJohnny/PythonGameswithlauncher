import os
import pygame
from os import listdir
from os.path import isfile, join
from settings import ASSET_BASE, GRAVITY, ANIMATION_DELAY, MAX_REWIND_FRAMES, REWIND_SPEED

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join(ASSET_BASE, dir1, dir2)
    if not os.path.exists(path):
        print(f"Warning: Path not found: {path}")
        return {}

    images = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    SPRITES = None

    def __init__(self, x, y, width, height):
        super().__init__()
        if Player.SPRITES is None:
            Player.SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)

        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.sprite = pygame.Surface((width, height))
        self.sprite.fill(self.COLOR)

        self.history = []
        self.is_rewinding = False


    def jump(self):
        self.y_vel = -GRAVITY * 7
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def make_hit(self):
        self.hit = True

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1
    def record_state(self):
        state = (
            self.rect.x, self.rect.y,
            self.x_vel, self.y_vel,
            self.direction, self.animation_count,
            self.fall_count, self.jump_count,
            self.hit, self.hit_count
        )
        self.history.append(state)
        if len(self.history) > MAX_REWIND_FRAMES:
            # Halve the resolution instead of dropping the past, so you can always
            # rewind back out of a vault no matter how long you stood in it.
            self.history = self.history[::2]

    def rewind(self, speed=REWIND_SPEED):
        if not self.history:
            return
        self.is_rewinding = True
        for _ in range(speed):
            if not self.history:
                break
            state = self.history.pop()


            (self.rect.x, self.rect.y,
             self.x_vel, self.y_vel,
             self.direction, self.animation_count,
             self.fall_count, self.jump_count,
             self.hit, self.hit_count) = state

        self.update_sprite()

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        name = sprite_sheet + "_" + self.direction
        if name in self.SPRITES:
            sprites = self.SPRITES[name]
            idx = (self.animation_count // ANIMATION_DELAY) % len(sprites)
            self.sprite = sprites[idx]
            self.animation_count += 1
        else:
            self.sprite = pygame.Surface((self.rect.width, self.rect.height))
            self.sprite.fill(self.COLOR)

        self.update()

    def loop(self, fps):
        # Physics are paused here while rewinding, so this is always safe to call.
        if self.is_rewinding:
            return

        self.y_vel += min(1, (self.fall_count / fps) * GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

        self.record_state()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x, offset_y=0):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))