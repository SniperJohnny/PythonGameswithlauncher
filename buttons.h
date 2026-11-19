#pragma once
#include <SDL_ttf.h>
#include <SDL2/SDL.h>

typedef void (*ButtonCallback)(void *userdata);

typedef struct Button {
    SDL_Rect        rect;
    const char     *text;
    ButtonCallback  onClick;
    void           *userdata;
    int             hovered;
    int             pressed;
    int             visible;

    // --- ADD THESE THREE LINES ---
    SDL_Texture    *text_tex;
    int             tex_w;
    int             tex_h;
    // -----------------------------
} Button;

#define MAX_BUTTONS 32

typedef struct ButtonManager {
    Button buttons[MAX_BUTTONS];
    int    count;
} ButtonManager;

void  BM_init(ButtonManager *bm);
int   BM_add(ButtonManager *bm, SDL_Rect rect, const char *text,
             ButtonCallback cb, void *userdata);   // returns index, -1 on full
void  BM_update(ButtonManager *bm, int mx, int my, int clicked, int released);
// Change this line:
// void BM_render(ButtonManager *bm, SDL_Renderer *renderer);

// To this:
void BM_render(ButtonManager *bm, SDL_Renderer *renderer, TTF_Font *font);