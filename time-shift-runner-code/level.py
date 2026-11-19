import pygame
from os.path import join

from config import CONFIG
from objects import (Arrow, ArrowShooter, Block, Checkpoint, End, Enemy, Fire, Gate, Lever,
                     MovingBlock, Saw, Spikes, Trampoline)
from settings import ASSET_BASE, WIDTH, HEIGHT

CELL = 96
HAZARDS = ("fire", "spikes", "saw", "arrow", "enemy")


def get_background(name):
    image = pygame.image.load(join(ASSET_BASE, "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            tiles.append((i * width, j * height))
    return tiles, image


def load_level(level):
    """Turns the level's rows into sprites. See levels/__init__.py for the legend."""
    objects = []
    spawn = (100, 100)
    for row_index, row in enumerate(level.rows):
        for col_index, cell in enumerate(row):
            x, y = col_index * CELL, row_index * CELL
            if cell == "#":
                objects.append(Block(x, y, CELL))
            elif cell == "M":
                objects.append(MovingBlock(x, y, CELL))
            elif cell == "P":
                spawn = (x, y)
            elif cell == "C":
                objects.append(Checkpoint(x + 16, y + CELL - 64, (x, y)))
            elif cell == "F":
                fire = Fire(x + 32, y + CELL - 64, 16, 32)
                fire.on()
                objects.append(fire)
            elif cell == "^":
                objects.append(Spikes(x, y + CELL - 24, CELL))
            elif cell == "S":
                objects.append(Saw(x + 16, y + CELL - 64))
            elif cell == "A":
                objects.append(ArrowShooter(x + 21, y + CELL - 52))
                objects.append(Arrow(x + 60, y + CELL - 36))
            elif cell == "T":
                objects.append(Trampoline(x, y + CELL - 28, CELL))
            elif cell == "X":
                objects.append(Enemy(x + 20, y + CELL - 56))
            elif cell == "L":
                objects.append(Lever(x + 30, y + CELL - 46))
            elif cell == "G":
                objects.append(Gate(x, y, CELL))
            elif cell == "E":
                goal = End(x, y)
                goal.rect.bottomleft = (x, y + CELL)
                objects.append(goal)

    hints = [(text, col * CELL, row * CELL) for text, col, row in level.hints]
    background, bg_image = get_background(level.background)
    return objects, spawn, hints, background, bg_image


def draw(window, background, bg_image, player, objects, offset_x, offset_y=0):
    for tile in background:
        window.blit(bg_image, (tile[0], tile[1] - offset_y))
    for obj in objects:
        obj.draw(window, offset_x, offset_y)
    player.draw(window, offset_x, offset_y)


def update_switches(player, objects):
    """Pulls levers the player touches, then opens every gate once all are pulled.
    Levers are not rewound, so gates stay open after you rewind out of a vault."""
    changed = False
    for obj in objects:
        if obj.name == "lever" and not obj.pulled and player.rect.colliderect(obj.rect):
            obj.pull()
            changed = True

    levers = [obj for obj in objects if obj.name == "lever"]
    if levers and all(obj.pulled for obj in levers):
        for obj in objects:
            if obj.name == "gate" and not obj.open:
                obj.open_up()
                changed = True
    return changed


def handle_move(player, objects):
    if player.is_rewinding:
        return

    solids = [obj for obj in objects if obj.solid]
    keys = pygame.key.get_pressed()
    move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
    move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
    speed = CONFIG["player_speed"]

    player.x_vel = 0
    direction = 0

    if move_left:
        direction = -1
    if move_right:
        direction = 1

    # --- 1. HORIZONTAL INPUT (the position is moved by player.loop) ---
    if direction != 0:
        player.x_vel = direction * speed
        if direction < 0:
            player.move_left(speed)
        else:
            player.move_right(speed)

        # Check horizontal collisions using Bounding Boxes (prevents walking through walls)
        for obj in solids:
            if player.rect.colliderect(obj.rect):
                # Check if we can step up (2 pixels max)
                step_height = obj.rect.top - player.rect.bottom

                if -2 <= step_height <= 0 and player.y_vel >= 0:
                    # Step up!
                    player.rect.y += step_height
                    player.landed()
                elif player.rect.bottom - player.y_vel <= obj.rect.top:
                    # Landing on top of this block; the vertical pass puts us there
                    continue
                else:
                    # Block X movement perfectly against the edge
                    if player.x_vel > 0:
                        player.rect.right = obj.rect.left
                    elif player.x_vel < 0:
                        player.rect.left = obj.rect.right

                    player.x_vel = 0  # Stop moving horizontally

    # Update the pixel-perfect mask for the new X/Y position
    player.update()

    # --- 2. VERTICAL COLLISIONS ---
    for obj in solids:
        # Use Pixel-Perfect mask for vertical floor/ceiling collisions
        if pygame.sprite.collide_mask(player, obj):
            if player.y_vel > 0:
                # Falling
                # Check if our feet are near the top of the block
                if player.rect.bottom - player.y_vel <= obj.rect.centery:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                else:
                    player.y_vel = 0

            elif player.y_vel < 0:
                # Jumping
                player.rect.top = obj.rect.bottom
                player.hit_head()

            # Update mask again after vertical snap
            player.update()
