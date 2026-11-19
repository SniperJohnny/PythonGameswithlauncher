#include "graphics.h"

#include <stddef.h>
#define SDL_MAIN_HANDLED
#include <SDL.h>
int GRAPHICS_init(Graphics *graphics) {
    if (!graphics->windowTitle) graphics->windowTitle = "No Name";
    if (!graphics->width)  graphics->width  = 800;
    if (!graphics->height) graphics->height = 600;

    graphics->window = SDL_CreateWindow(
        graphics->windowTitle,
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        graphics->width, graphics->height,
        SDL_WINDOW_SHOWN
    );
    if (graphics->window == NULL) {
        SDL_Log("Unable to create window: %s", SDL_GetError());
        return 1;
    }

    // NEW: create the renderer
    graphics->renderer = SDL_CreateRenderer(
        graphics->window, -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC
    );
    if (graphics->renderer == NULL) {
        SDL_Log("Unable to create renderer: %s", SDL_GetError());
        SDL_DestroyWindow(graphics->window);
        graphics->window = NULL;
        return 1;
    }

    return 0;
}

void GRAPHICS_free(Graphics *graphics) {
    if (graphics->renderer) {
        SDL_DestroyRenderer(graphics->renderer);
        graphics->renderer = NULL;
    }
    if (graphics->window) {
        SDL_DestroyWindow(graphics->window);
        graphics->window = NULL;
    }
}