"""Small procedural sound effects, so the game needs no audio files."""
import array
import math

import pygame

RATE = 44100
SOUNDS = {}
_ready = False


def _tone(start_freq, end_freq, duration, volume=0.3):
    frames = int(RATE * duration)
    buffer = array.array("h")
    phase = 0.0
    for i in range(frames):
        progress = i / frames
        frequency = start_freq + (end_freq - start_freq) * progress
        phase += 2 * math.pi * frequency / RATE
        sample = math.sin(phase) * (1 - progress) * volume
        buffer.append(int(sample * 32767))
    return pygame.mixer.Sound(buffer=buffer.tobytes())


def init():
    global _ready
    try:
        pygame.mixer.init(RATE, -16, 1, 512)
        SOUNDS.update({
            "jump": _tone(420, 760, 0.12),
            "land": _tone(220, 140, 0.08),
            "bounce": _tone(160, 540, 0.20),
            "rewind": _tone(380, 620, 0.30, 0.22),
            "hit": _tone(200, 70, 0.28, 0.4),
            "checkpoint": _tone(620, 940, 0.18),
            "switch": _tone(300, 820, 0.22),
            "clear": _tone(520, 1040, 0.55),
            "click": _tone(700, 520, 0.05, 0.25),
        })
        _ready = True
    except pygame.error:
        _ready = False


def play(name):
    if _ready:
        sound = SOUNDS.get(name)
        if sound is not None:
            sound.play()
