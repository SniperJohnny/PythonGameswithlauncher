import random

import pygame

from settings import WIDTH, HEIGHT, FPS
from player import Player
from level import load_level, draw, handle_move, update_switches, HAZARDS
from menu import run_menu, load_progress, save_progress
from config import CONFIG, load as load_config
import audio
import damage
import scores
import ui
from effects import spawn_particles, update_particles, draw_particles


def place(player, pos):
    player.rect.topleft = pos
    player.x_vel = player.y_vel = 0
    player.history.clear()
    player.hit = False
    player.hit_count = 0
    player.update()


def play_level(window, clock, level):
    """Runs one level. Returns "menu" or "quit"."""
    objects, spawn, hints, background, bg_image = load_level(level)
    goal = next((obj for obj in objects if obj.name == "end"), None)
    player = Player(spawn[0], spawn[1], 50, 50)

    spawn_point = spawn
    health = damage.start_health()
    iframe = 0
    was_rewinding = False
    camera_center = player.rect.centerx
    camera_look_ahead = 0
    particles = []
    shake_frames = 0
    start_time = pygame.time.get_ticks()

    tint = pygame.Surface((WIDTH, HEIGHT))
    tint.set_alpha(45)
    tint.fill((70, 130, 255))

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
                    audio.play("jump")

        # Rewinding stays on while R is held, even once the player's history is used up
        if pygame.key.get_pressed()[pygame.K_r] and (player.history or player.is_rewinding):
            player.is_rewinding = True
            player.rewind(CONFIG["rewind_speed"])
            if not was_rewinding:
                audio.play("rewind")
        else:
            player.is_rewinding = False
        was_rewinding = player.is_rewinding

        prev_y_vel = player.y_vel
        # ALWAYS called; gravity is paused inside while rewinding
        player.loop(FPS)
        handle_move(player, objects)

        # Hazards run backwards while rewinding; platforms carry the player forwards only
        step = -1 if player.is_rewinding else 1
        for obj in objects:
            dx = obj.loop(step) if hasattr(obj, "loop") else 0
            if dx and not player.is_rewinding and abs(player.rect.bottom - obj.rect.top) <= 4 \
                    and player.rect.right > obj.rect.left and player.rect.left < obj.rect.right:
                player.move(dx, 0)
                player.update()

        # Trampolines bounce the player far higher than a jump
        spring = next((obj for obj in objects if obj.name == "trampoline"
                       and player.y_vel >= 0 and player.rect.colliderect(obj.rect)), None)
        if spring:
            player.y_vel = spring.BOUNCE
            player.jump_count = 0
            audio.play("bounce")
            spawn_particles(particles, player.rect.centerx, player.rect.bottom, 8, (150, 235, 255))

        if not player.is_rewinding and prev_y_vel > 1 and player.y_vel == 0:
            spawn_particles(particles, player.rect.centerx, player.rect.bottom, 5, (215, 215, 215))
            audio.play("land")
        if player.is_rewinding:
            spawn_particles(particles, player.rect.centerx, player.rect.centery, 1, (120, 180, 255))
        update_particles(particles)

        for obj in objects:
            if obj.name == "checkpoint" and not obj.activated and player.rect.colliderect(obj.rect):
                obj.activate()
                spawn_point = obj.spawn
                audio.play("checkpoint")

        if update_switches(player, objects):
            audio.play("switch")
            spawn_particles(particles, player.rect.centerx, player.rect.centery, 10, (130, 240, 190))

        hazard = next((obj for obj in objects if obj.name in HAZARDS and player.rect.colliderect(obj.rect)), None)
        if iframe > 0:
            iframe -= 1
        elif hazard or player.rect.top > HEIGHT:
            health = damage.apply_hit(health, hazard)
            audio.play("hit")
            spawn_particles(particles, player.rect.centerx, player.rect.centery, 12, (255, 90, 90))
            shake_frames = 12 if CONFIG["screen_shake"] else 0

            if health > 0:
                place(player, spawn_point)
                iframe = 60
            else:
                for obj in objects:
                    if obj.name == "checkpoint":
                        obj.reset()
                spawn_point = spawn
                health = damage.start_health()
                start_time = pygame.time.get_ticks()
                place(player, spawn)

        if goal and player.rect.colliderect(goal.rect):
            seconds = (pygame.time.get_ticks() - start_time) / 1000
            audio.play("clear")
            save_progress(max(load_progress(), level.number))
            name = scores.name_entry(window, clock, seconds)
            if name is None:
                return "quit"
            scores.add_score(level.key, name, seconds)
            scores.show_leaderboard(window, clock, level.title, level.key)
            return "menu"

        # --- CAMERA ---
        target_x = player.rect.centerx
        look_ahead_distance = 150
        look_ahead_speed = 0.03

        if player.x_vel > 0:
            camera_look_ahead += (look_ahead_distance - camera_look_ahead) * look_ahead_speed
        elif player.x_vel < 0:
            camera_look_ahead += (-look_ahead_distance - camera_look_ahead) * look_ahead_speed
        else:
            camera_look_ahead += (0 - camera_look_ahead) * look_ahead_speed

        target_x += camera_look_ahead

        smoothness = 0.08
        camera_center += (target_x - camera_center) * smoothness
        offset_x = camera_center - (WIDTH // 2)

        shake_x = shake_y = 0
        if shake_frames > 0:
            shake_frames -= 1
            shake_x = random.randint(-5, 5)
            shake_y = random.randint(-5, 5)

        draw(window, background, bg_image, player, objects, offset_x + shake_x, shake_y)
        draw_particles(window, particles, offset_x + shake_x, shake_y)
        if player.is_rewinding:
            window.blit(tint, (0, 0))

        for text, hint_x, hint_y in hints:
            if abs(player.rect.centerx - hint_x) < 240:
                x = hint_x - offset_x - shake_x
                y = hint_y - shake_y
                ui.draw_text(window, text, x + 1, y + 1, 26, (10, 10, 20))
                ui.draw_text(window, text, x, y, 26, (255, 235, 170))

        elapsed = (pygame.time.get_ticks() - start_time) / 1000
        ui.draw_text(window, f"{elapsed:.1f}s", 20, 20, 28, (230, 240, 255), center=False)
        for i in range(health):
            pygame.draw.circle(window, (230, 70, 90), (30 + i * 26, 74), 9)
        ui.draw_text(window, "R  rewind", 20, 104, 20, (135, 155, 195), center=False)
        pygame.display.update()


def main():
    pygame.init()
    load_config()
    audio.init()
    pygame.display.set_caption("Time-Shift Runner")
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    while True:
        level = run_menu(window, clock)
        if level is None:
            break
        if play_level(window, clock, level) == "quit":
            break

    pygame.quit()


if __name__ == "__main__":
    main()
