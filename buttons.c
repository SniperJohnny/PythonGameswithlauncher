#include "buttons.h"
#include <string.h>

void BM_init(ButtonManager *bm) {
    memset(bm, 0, sizeof(*bm));
}

int BM_add(ButtonManager *bm, SDL_Rect rect, const char *text, ButtonCallback cb, void *userdata) {
    if (bm->count >= MAX_BUTTONS) return -1;
    Button *b = &bm->buttons[bm->count];
    b->rect = rect;
    b->text = text;
    b->onClick = cb;
    b->userdata = userdata;
    b->hovered  = 0;
    b->pressed  = 0;
    b->visible  = 1;


    b->text_tex = NULL;
    b->tex_w = 0;
    b->tex_h = 0;

    return bm->count++;
}

static int point_in_rect(int x, int y, const SDL_Rect *r) {
    return x >= r->x && x < r->x + r->w && y >= r->y && y < r->y + r->h;
}

void BM_update(ButtonManager *bm, int mx, int my, int clicked, int released) {
    for (int i = 0; i < bm->count; i++) {
        Button *b = &bm->buttons[i];
        if (!b->visible) continue;

        b->hovered = point_in_rect(mx, my, &b->rect);

        if (clicked && b->hovered) b->pressed = 1;
        if (released) {
            if (b->pressed && b->hovered && b->onClick) {
                b->onClick(b->userdata);
            }
            b->pressed = 0;
        }
    }
}

void BM_destroy(ButtonManager *bm) {
    for (int i = 0; i < bm->count; i++) {
        if (bm->buttons[i].text_tex) {
            SDL_DestroyTexture(bm->buttons[i].text_tex);
            bm->buttons[i].text_tex = NULL;
        }
    }
    bm->count = 0;
}