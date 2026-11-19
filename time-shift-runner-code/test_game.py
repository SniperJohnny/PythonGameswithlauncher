import os
import sys
import pygame

# Ensure we can find the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from settings import WIDTH, HEIGHT, ASSET_BASE
from player import Player
from objects import Block, Fire


def test_rewind():
    print("\n--- Testing Rewind Mechanic ---")
    player = Player(100, 100, 50, 50)

    # Simulate 60 frames of falling/moving
    for i in range(60):
        player.y_vel = 5  # Force falling
        player.loop(60)

    start_x = player.rect.x
    start_y = player.rect.y

    if len(player.history) == 0:
        print("❌ FAIL: History buffer is empty after looping.")
        return

    # Now rewind for 10 frames
    for _ in range(10):
        player.rewind()

    end_x = player.rect.x
    end_y = player.rect.y

    if end_y < start_y:  # Remember, y decreases as you go up
        print(f"✅ PASS: Rewind moved player backwards. (From Y:{start_y} to Y:{end_y})")
    else:
        print(f"❌ FAIL: Rewind did not move player backwards. (From Y:{start_y} to Y:{end_y})")
def test_assets():
    print("\n--- Testing Assets ---")
    if not os.path.exists(ASSET_BASE):
        print(f"❌ FAIL: Asset base path does not exist: {ASSET_BASE}")
        return False

    bg_path = os.path.join(ASSET_BASE, "Background", "Blue.png")
    terrain_path = os.path.join(ASSET_BASE, "Terrain", "Terrain.png")

    if os.path.exists(bg_path) and os.path.exists(terrain_path):
        print("✅ PASS: Core image files found (Background, Terrain).")
        return True
    else:
        print("❌ FAIL: Missing Background/Blue.png or Terrain/Terrain.png.")
        return False


def test_player_loading():
    print("\n--- Testing Player Sprites ---")
    player = Player(100, 100, 50, 50)

    if not Player.SPRITES:
        print("❌ FAIL: No sprites loaded. Check folder names: MainCharacters/MaskDude.")
        return False

    expected_animations = ["idle_right", "idle_left", "run_right", "run_left", "jump_right", "fall_right"]
    missing = [anim for anim in expected_animations if anim not in Player.SPRITES]

    if missing:
        print(f"❌ FAIL: Missing expected sprite animations: {missing}")
        return False

    print(f"✅ PASS: Loaded {len(Player.SPRITES)} sprite animations successfully.")
    return True


def test_collisions():
    print("\n--- Testing Collisions & Physics ---")

    block_size = 96
    floor_block = Block(0, 500, block_size)
    objects = [floor_block]

    player = Player(20, 0, 50, 50)

    # Simulate falling
    for _ in range(150):
        player.loop(60)
        for obj in objects:
            if pygame.sprite.collide_mask(player, obj):
                if player.y_vel > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()

    # 1. Check gravity resting state (allow tiny gravity pressure)
    if player.y_vel < 1.0 and player.jump_count == 0:
        print("✅ PASS: Player gravity stopped and landed correctly.")
    else:
        print(f"❌ FAIL: Player did not stop falling. Current Y-Vel: {player.y_vel}")

    # 2. Check alignment
    if abs(player.rect.bottom - floor_block.rect.top) <= 2:
        print("✅ PASS: Player's feet are perfectly aligned with the block's surface.")
    else:
        print(f"❌ FAIL: Player Y alignment off. Player Bottom: {player.rect.bottom}, Block Top: {floor_block.rect.top}")

    # 3. Test Fire collision logic
    fire = Fire(20, 500, 16, 32)
    player.rect.x = 20
    player.rect.y = 480
    player.update()

    if pygame.sprite.collide_mask(player, fire):
        print("✅ PASS: Pixel-perfect mask collision detected between Player and Fire.")
    else:
        print("❌ FAIL: Mask collision failed. The player is not overlapping the fire.")


def main():
    print("========================================")
    print("   TIME-SHIFT RUNNER: AUTOMATED TESTS   ")
    print("========================================")

    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))

    assets_ok = test_assets()
    player_ok = test_player_loading()

    if assets_ok and player_ok:
        test_collisions()
        test_rewind()
    else:
        print("\n⚠️ Skipping physics tests because assets failed to load.")

    print("\n========================================")
    print("             TESTS FINISHED             ")
    print("========================================")
    pygame.quit()


if __name__ == "__main__":
    main()