# Time-Shift Runner: Handoff and Feature Plan

## 1. Current Critical Bug (Fix First)
**Symptom:** The player jumps infinitely into the sky and falls through the floor. Debug print statements inside `Player.loop()` do not fire.
**Diagnosis:** The main game loop (`Time-shift-runner.py`) is skipping the call to `player.loop(FPS)`. This happens because the `is_rewinding` flag is stuck on `True` or the main loop's `if/else` logic for the time mechanic is structurally bypassing the physics update. Because `player.loop()` is skipped, gravity is never applied, and the player retains their upward velocity forever. 
**Required Fix:** Refactor the main game loop so `player.loop(FPS)` is *always* called. Inside `Player.loop()`, check `if self.is_rewinding: return` to pause physics, rather than skipping the function call entirely. Ensure `player.is_rewinding` resets to `False` when the rewind key is released.

## 2. Vision & Feature Plan
The goal is to evolve the prototype into a polished 2D platformer heavily inspired by *Hollow Knight* and *Ori and the Will of the Wisps*, focusing on snappy movement, time-manipulation mechanics (rewind/slow-mo), and atmospheric level design.

### A. Core Systems & Structure
*   **Main Menu:** Start game, Level Selector, Quit.
*   **Level System & Progress Saving:** A system to track which levels are unlocked/completed. Needs a simple save file (e.g., JSON) and a way to delete progress.
*   **5 Levels:** 
    *   **Level 1:** Tutorial (teaches movement, jump, and rewind).
    *   **Levels 2-5:** Increasing difficulty, introducing mechanics and enemies.
*   **Easy Level Creator:** A simple, human-readable format (like 2D grids or JSON coordinate lists) so the developer can easily design and tweak levels without writing code.

### B. Gameplay & Mechanics
*   **Tutorial Level:** Contextual prompts (e.g., "Press SPACE to jump" floating in the world) that appear exactly when the player needs them.
*   **Time Mechanics Polish:** Visual and audio feedback for rewinding (e.g., screen tint, particles, sound effects).
*   **New Enemies/Traps:** (Developer will create textures, agent needs to implement logic). E.g., patrolling enemies, spikes, moving platforms.
*   **Game Feel:** Add particle effects (dust on landing, trails on rewind), camera improvements, and screen shake on hit.

### C. Developer Helper Methods
*   Create utility functions to make development easier (e.g., `draw_text()`, `load_json_level()`, `spawn_particles()`).

## 3. Rules for the Coding Agent
**Read carefully before writing any code:**
1. **Respect Existing Structure:** The project root is `Tagderoffenentürproject`. The game code lives inside `time-shift-runner-code/` (alongside `settings.py`, `player.py`, `objects.py`, `level.py`, and `Time-shift-runner.py`). Assets live in `assets-time-shift-runner/assets/`. Do not change this folder structure.
2. **Do Not Touch Other Projects:** There are unrelated files (`Pong.py`, `spaceinvaders.py`) in the root folder. **Do not read, modify, or touch these files under any circumstances.**
3. **Minimal Code:** Write as little code as possible. Do not over-engineer. Keep it simple and readable.
4. **Comments:** Only write necessary comments. Do not write paragraphs explaining obvious code.
5. **Ask Before Acting:** If you have an idea for a feature not explicitly requested here, **stop and ask the user first.**
6. **Ask if Missing Info:** If you need a specific variable, asset name, or logic rule, **ask the user.**
7. **Asset Creation (`assets.md`):** Since the user will create textures, create an `assets.md` file inside `time-shift-runner-code/`. List the name of every new texture needed (enemies, traps, background elements) and provide a clear, descriptive sentence on how it should look so the user can create it.

---

## 4. The Prompt to Give Your Agent

Copy and paste the text below directly into your coding agent:

```text
Please read the attached `handoff.md` file carefully. 

Your first priority is to fix the infinite jumping/falling bug by refactoring the main game loop as described in Section 1. Ensure `player.loop()` is always called, and physics are paused internally via `is_rewinding`.

After the bug is fixed, proceed to implement the feature plan in Section 2. Start by creating the Level System, Main Menu, and the Level Creator data structure. 

STRICT RULES:
- Maintain the existing folder structure exactly as described in Section 3. 
- DO NOT touch `Pong.py` or `spaceinvaders.py`.
- Write the absolute minimum amount of code required.
- Do not over-engineer. Keep everything simple.
- Only write necessary comments.
- If you need textures, create the `assets.md` file as requested.
- If you have an idea for a feature not in the plan, ASK ME first. Do not just build it.
- If you are missing information, ASK ME.

Please start with the bug fix and the main menu/level system, and then wait for my review before proceeding to the tutorial level.
