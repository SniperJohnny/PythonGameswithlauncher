#include "buttons.h"
#include <SDL_ttf.h>

static void outline(SDL_Renderer *r, SDL_Rect rc, int grow) {
    SDL_Rect g = { rc.x - grow, rc.y - grow, rc.w + 2 * grow, rc.h + 2 * grow };
    SDL_RenderDrawRect(r, &g);
}

void BM_render(ButtonManager *bm, SDL_Renderer *renderer, TTF_Font *font) {
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    Uint32 t = SDL_GetTicks();

    for (int i = 0; i < bm->count; i++) {
        Button *b = &bm->buttons[i];
        if (!b->visible) continue;

        int hot = b->hovered;
        int cr = hot ? 255 : 0, cg = hot ? 60 : 230, cb = hot ? 200 : 255;

        SDL_Rect rc = b->rect;
        if (hot)        rc.x += 8;
        if (b->pressed) { rc.x += 2; rc.y += 2; }

        SDL_Rect shadow = { b->rect.x + 6, b->rect.y + 6, b->rect.w, b->rect.h };
        SDL_SetRenderDrawColor(renderer, cr, cg, cb, 70);
        SDL_RenderFillRect(renderer, &shadow);

        if (b->pressed) SDL_SetRenderDrawColor(renderer, cr, cg, cb, 90);
        else if (hot)   SDL_SetRenderDrawColor(renderer, 40, 15, 50, 255);
        else            SDL_SetRenderDrawColor(renderer, 14, 16, 40, 255);
        SDL_RenderFillRect(renderer, &rc);

        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 40);
        for (int y = rc.y; y < rc.y + rc.h; y += 2)
            SDL_RenderDrawLine(renderer, rc.x, y, rc.x + rc.w - 1, y);

        if (hot) {
            for (int g = 3; g <= 8; g++) {
                SDL_SetRenderDrawColor(renderer, cr, cg, cb, 90 - g * 10);
                outline(renderer, rc, g);
            }
        }
        SDL_SetRenderDrawColor(renderer, cr, cg, cb, 255);
        outline(renderer, rc, 0);
        outline(renderer, rc, -1);

        if (hot && (t / 300) % 2) {
            int cy = rc.y + rc.h / 2;
            for (int k = 0; k < 8; k++)
                SDL_RenderDrawLine(renderer, rc.x + 16 + k, cy - 8 + k, rc.x + 16 + k, cy + 8 - k);
        }

        if (b->text && font) {
            if (!b->text_tex) {
                SDL_Color white = {255, 255, 255, 255};
                SDL_Surface *surf = TTF_RenderUTF8_Blended(font, b->text, white);
                if (surf) {
                    b->text_tex = SDL_CreateTextureFromSurface(renderer, surf);
                    SDL_FreeSurface(surf);
                    if (b->text_tex)
                        SDL_QueryTexture(b->text_tex, NULL, NULL, &b->tex_w, &b->tex_h);
                }
            }
            if (b->text_tex) {
                if (hot) SDL_SetTextureColorMod(b->text_tex, 255, 230, 0);
                else     SDL_SetTextureColorMod(b->text_tex, 255, 255, 255);
                SDL_Rect dst = {
                    rc.x + (rc.w - b->tex_w) / 2,
                    rc.y + (rc.h - b->tex_h) / 2,
                    b->tex_w, b->tex_h
                };
                SDL_RenderCopy(renderer, b->text_tex, NULL, &dst);
            }
        }
    }
}