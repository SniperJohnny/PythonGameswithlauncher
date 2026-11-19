import os

import pygame
from os.path import join
from settings import ASSET_BASE, ANIMATION_DELAY, GRAVITY
from player import load_sprite_sheets


def first_frame(path, size):
    """Loads a texture (or the first square frame of a sheet) scaled to size x size."""
    image = pygame.image.load(path).convert_alpha()
    square = min(image.get_width(), image.get_height())
    return pygame.transform.scale(image.subsurface((0, 0, square, square)), (size, size))


def get_block(size):
    path = join(ASSET_BASE, "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha() # This is fine because it's called after display init
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Object(pygame.sprite.Sprite):
    solid = False
    damage = 0

    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x, offset_y=0):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))


class Block(Object):
    solid = True

    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "block")
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Gate(Block):
    """Solid wall that opens for good once every lever is pulled."""

    def __init__(self, x, y, size):
        super().__init__(x, y, size)
        self.name = "gate"
        self.open = False
        glass = pygame.Surface((size, size), pygame.SRCALPHA)
        glass.fill((95, 170, 255, 95))
        self.image.blit(glass, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

    def open_up(self):
        self.open = True
        self.solid = False
        self.image.set_alpha(45)


class Lever(Object):
    """Switch at the bottom of a vault. Levers stay pulled, even through rewind."""

    def __init__(self, x, y):
        super().__init__(x, y, 36, 46, "lever")
        self.pulled = False
        self._paint()

    def _paint(self):
        self.image.fill((0, 0, 0, 0))
        color = (120, 235, 170) if self.pulled else (240, 95, 95)
        pygame.draw.rect(self.image, (50, 58, 82), (10, 18, 16, 28))
        pygame.draw.rect(self.image, color, (4, 0, 28, 22), border_radius=6)
        self.mask = pygame.mask.from_surface(self.image)

    def pull(self):
        self.pulled = True
        self._paint()


class MovingBlock(Block):
    """Solid block that slides horizontally. loop() returns the pixels it moved."""
    SPEED = 1
    PATROL = 192

    def __init__(self, x, y, size):
        super().__init__(x, y, size)
        self.start_x = x
        self.direction = 1

    def loop(self, step=1):
        dx = self.direction * self.SPEED * step
        if abs(self.rect.x + dx - self.start_x) > self.PATROL:
            self.direction *= -1
            dx = self.direction * self.SPEED * step
        self.rect.x += dx
        return dx


class End(Object):
    def __init__(self, x, y):
        image = pygame.transform.scale2x(
            pygame.image.load(join(ASSET_BASE, "Items", "Checkpoints", "End", "End (Idle).png")).convert_alpha()
        )
        super().__init__(x, y, image.get_width(), image.get_height(), "end")
        self.image.blit(image, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Checkpoint(Object):
    """Activating it moves the respawn point here."""

    def __init__(self, x, y, spawn):
        super().__init__(x, y, 64, 64, "checkpoint")
        self.spawn = spawn
        self.activated = False
        self._load("Checkpoint (No Flag).png")

    def _load(self, name):
        path = join(ASSET_BASE, "Items", "Checkpoints", "Checkpoint", name)
        if os.path.exists(path):
            self.image = first_frame(path, 64)
        self.mask = pygame.mask.from_surface(self.image)

    def activate(self):
        if not self.activated:
            self.activated = True
            self._load("Checkpoint (Flag Idle)(64x64).png")

    def reset(self):
        self.activated = False
        self._load("Checkpoint (No Flag).png")


class Fire(Object):
    damage = 2

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0] if "off" in self.fire else pygame.Surface((width, height))
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self, step=1):
        if self.animation_name not in self.fire:
            return
        sprites = self.fire[self.animation_name]
        idx = (self.animation_count // ANIMATION_DELAY) % len(sprites)
        self.image = sprites[idx]
        self.animation_count += 1
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)
        if self.animation_count // ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Spikes(Object):
    """Hazard that sits on the ground of a cell."""
    damage = 1

    def __init__(self, x, y, width):
        super().__init__(x, y, width, 24, "spikes")
        image = pygame.image.load(join(ASSET_BASE, "Traps", "Spikes", "Idle.png")).convert_alpha()
        self.image = pygame.transform.scale(image, (width, 24))
        self.mask = pygame.mask.from_surface(self.image)


class Trampoline(Object):
    """Bounces the player much higher than a normal jump."""
    BOUNCE = -GRAVITY * 12

    def __init__(self, x, y, width):
        super().__init__(x, y, width, 28, "trampoline")
        image = pygame.image.load(join(ASSET_BASE, "Traps", "Trampoline", "Idle.png")).convert_alpha()
        self.image = pygame.transform.scale(image, (width, 28))
        self.mask = pygame.mask.from_surface(self.image)


class ArrowShooter(Object):
    """Decorative spike head; the level places its Arrow next to it."""

    def __init__(self, x, y):
        super().__init__(x, y, 54, 52, "shooter")
        image = pygame.image.load(join(ASSET_BASE, "Traps", "Spike Head", "Idle.png")).convert_alpha()
        self.image = pygame.transform.scale(image, (54, 52))
        self.mask = pygame.mask.from_surface(self.image)


class Arrow(Object):
    """Arrow that flies sideways and loops back to its launcher."""
    SPEED = 4
    RANGE = 288
    damage = 1

    def __init__(self, x, y):
        super().__init__(x, y, 36, 36, "arrow")
        image = first_frame(join(ASSET_BASE, "Traps", "Arrow", "Idle (18x18).png"), 18)
        self.image = pygame.transform.scale(image, (36, 36))
        self.mask = pygame.mask.from_surface(self.image)
        self.start_x = x

    def loop(self, step=1):
        self.rect.x += self.SPEED * step
        if self.rect.x - self.start_x > self.RANGE:
            self.rect.x = self.start_x
        elif self.rect.x < self.start_x:
            self.rect.x = self.start_x + self.RANGE


class Saw(Object):
    """Spinning blade that slides back and forth along the ground."""
    SPEED = 2
    PATROL = 96
    damage = 2

    def __init__(self, x, y):
        super().__init__(x, y, 64, 64, "saw")
        self.image = first_frame(join(ASSET_BASE, "Traps", "Saw", "on.png"), 64)
        self.mask = pygame.mask.from_surface(self.image)
        self.start_x = x
        self.direction = 1

    def loop(self, step=1):
        self.rect.x += self.direction * self.SPEED * step
        if abs(self.rect.x - self.start_x) >= self.PATROL:
            self.direction *= -1


class Enemy(Object):
    """Patrolling hazard. Uses Enemies/Patroller art when present (see assets.md)."""
    SPEED = 2
    PATROL = 96
    damage = 1

    def __init__(self, x, y):
        super().__init__(x, y, 56, 56, "enemy")
        path = join(ASSET_BASE, "Enemies", "Patroller", "Idle.png")
        if os.path.exists(path):
            self.image = first_frame(path, 56)
        else:
            self.image.fill((165, 45, 60))
            pygame.draw.rect(self.image, (235, 120, 120), self.image.get_rect(), 2)
        self.mask = pygame.mask.from_surface(self.image)
        self.start_x = x
        self.direction = 1

    def loop(self, step=1):
        self.rect.x += self.direction * self.SPEED * step
        if abs(self.rect.x - self.start_x) >= self.PATROL:
            self.direction *= -1
