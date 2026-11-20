#ifndef ENGINE_GRAPHICS_H
#define ENGINE_GRAPHICS_H

#define SDL_MAIN_HANDLED
#include <SDL.h>

typedef struct {
    char *windowTitle;
    int width;
    int height;
    SDL_Window *window;
    SDL_Renderer *renderer;
} Graphics;

int GRAPHICS_init(Graphics *graphics);
void GRAPHICS_free(Graphics *graphics);

#endif