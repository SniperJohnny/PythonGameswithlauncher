# Textures needed

Everything except the patrolling enemy now uses existing art. The enemy falls back to a
placeholder rectangle until this file exists:

## `assets-time-shift-runner/assets/Enemies/Patroller/`
- `Idle.png` - a 32x32 side view of a small hooded creature in dark red with two glowing
  eyes, facing right; the game flips it to face left.

## Sound
Sound effects are generated in code (`audio.py`), so no files are needed. If you would
rather use real audio, add `.wav` files for jump, land, hit, rewind, checkpoint, clear and
click and tell me where they are.
