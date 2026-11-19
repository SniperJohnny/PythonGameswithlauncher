import pygame

import audio

_FONTS = {}


def font(size):
    if size not in _FONTS:
        if not pygame.font.get_init():
            pygame.font.init()
        _FONTS[size] = pygame.font.SysFont(None, size)
    return _FONTS[size]


def draw_text(window, text, x, y, size=28, color=(235, 240, 255), center=True):
    image = font(size).render(text, True, color)
    rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
    window.blit(image, rect)
    return rect


class Button:
    """Rounded button with hover, press and disabled styles."""

    def __init__(self, x, y, width, height, text, size=28, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.size = size
        self.enabled = enabled
        self.hover = False
        self.pressed = False

    def handle(self, event):
        """Returns True when this button is clicked."""
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            clicked = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            if clicked:
                audio.play("click")
            return clicked
        return False

    def draw(self, window):
        if not self.enabled:
            fill, border, label = (30, 32, 42), (62, 66, 80), (95, 100, 115)
        elif self.pressed:
            fill, border, label = (24, 45, 95), (230, 240, 255), (255, 255, 255)
        elif self.hover:
            fill, border, label = (62, 104, 195), (190, 220, 255), (255, 255, 255)
        else:
            fill, border, label = (38, 46, 70), (92, 112, 155), (210, 220, 240)
        pygame.draw.rect(window, fill, self.rect, border_radius=12)
        pygame.draw.rect(window, border, self.rect, 2, border_radius=12)
        draw_text(window, self.text, self.rect.centerx, self.rect.centery, self.size, label)
