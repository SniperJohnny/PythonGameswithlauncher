#include "buttons.h"
#include <SDL2/SDL_ttf.h>

void BM_render(ButtonManager *bm, SDL_Renderer *renderer, TTF_Font *font) {
    for (int i = 0; i < bm->count; i++) {
        Button *b = &bm->buttons[i];
        if (!b->visible) continue;

        // 1. Draw Background
        if (b->pressed)      SDL_SetRenderDrawColor(renderer, 120, 60, 60, 255);
        else if (b->hovered) SDL_SetRenderDrawColor(renderer, 200, 100, 100, 255);
        else                 SDL_SetRenderDrawColor(renderer, 160, 80,  80,  255);
        SDL_RenderFillRect(renderer, &b->rect);

        // 2. Draw Border
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderDrawRect(renderer, &b->rect);

        // 3. Draw Text
        if (b->text && font) {
            if (!b->text_tex) {
                SDL_Color white = {255, 255, 255, 255};
                SDL_Surface *surf = TTF_RenderUTF8_Blended(font, b->text, white);
                if (surf) {
                    b->text_tex = SDL_CreateTextureFromSurface(renderer, surf);
                    SDL_FreeSurface(surf);
                    if (b->text_tex) {
                        SDL_QueryTexture(b->text_tex, NULL, NULL, &b->tex_w, &b->tex_h);
                    }
                }
            }

            if (b->text_tex) {
                SDL_Rect dst = {
                    b->rect.x + (b->rect.w - b->tex_w) / 2,
                    b->rect.y + (b->rect.h - b->tex_h) / 2,
                    b->tex_w, b->tex_h
                };
                SDL_RenderCopy(renderer, b->text_tex, NULL, &dst);
            }
        }
    }
}