import random

import pygame


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = random.uniform(-2, 2)
        self.vel_y = random.uniform(-3, -0.5)
        self.life = random.randint(18, 36)
        self.size = random.randint(2, 5)

    def loop(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.15
        self.life -= 1

    def draw(self, window, offset_x, offset_y):
        if self.life > 0:
            pygame.draw.rect(window, self.color, (self.x - offset_x, self.y - offset_y, self.size, self.size))


def spawn_particles(particles, x, y, count, color):
    for _ in range(count):
        particles.append(Particle(x, y, color))


def update_particles(particles):
    for particle in particles:
        particle.loop()
    particles[:] = [particle for particle in particles if particle.life > 0]


def draw_particles(window, particles, offset_x, offset_y=0):
    for particle in particles:
        particle.draw(window, offset_x, offset_y)
