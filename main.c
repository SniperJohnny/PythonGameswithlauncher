#include <stdio.h>
#include <stdlib.h>
#include "engine.h"
#include "buttons.h"

#define PY_VER "3.12.10"
#define GAMES_DIR "Project_Games"
#define PY_BASE "https://cmcc.mirrors.ustc.edu.cn/github-release/astral-sh/python-build-standalone/20250409/cpython-3.12.10+20250409-"

#ifdef _WIN32
#define PY_URL PY_BASE "x86_64-pc-windows-msvc-install_only.tar.gz"
#define PY_EXE "python\\python.exe"
#define CD "cd /d "
#else
#define PY_URL PY_BASE "x86_64-unknown-linux-gnu-install_only.tar.gz"
#define PY_EXE "python/bin/python3"
#define CD "cd "
#endif

static SDL_atomic_t setup_running;

static int file_exists(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    fclose(f);
    return 1;
}

static int run(const char *cmd) {
    printf("> %s\n", cmd);
    return system(cmd);
}

static int python(const char *args) {
    char cmd[1024];
    snprintf(cmd, sizeof cmd, CD GAMES_DIR " && " PY_EXE " %s", args);
    return run(cmd);
}

static int setup_python(void) {
    if (!file_exists(GAMES_DIR "/" PY_EXE) &&
        run("curl -fL " PY_URL " | tar -xzf - -C " GAMES_DIR) != 0) return 1;
    if (python("-c \"import pygame\"") == 0) return 0;
    return python("-m pip install pygame-ce");
}

static int game_thread(void *ud) {
    if (setup_python() == 0) python((const char *)ud);
    SDL_AtomicSet(&setup_running, 0);
    return 0;
}



static int run_game_thread(void *ud) {
    const char *script_name = (const char *)ud;

    /* Ensure python is installed first! */
    if (setup_python() != 0) {
        printf("Setup failed, cannot launch game.\n");
        SDL_AtomicSet(&setup_running, 0);
        return 0;
    }

    printf("Launching %s...\n", script_name);
    int rc = python(script_name);

    if (rc != 0) fprintf(stderr, "%s exited with code %d\n", script_name, rc);
    else printf("%s finished successfully.\n", script_name);

    SDL_AtomicSet(&setup_running, 0);
    return 0;
}

unsigned int initState1() { printf("state 1 created\n"); return 0; }
unsigned int destroyState1() { printf("state 1 destroyed\n"); return 0; }
unsigned int updateState1(float deltaTime) { return 0; }

static void on_quit_click(void *ud) {
    Engine *e = (Engine *)ud;
    e->quit = 1;
}

static void on_pong_click(void *ud) {
    (void)ud;
    if (!SDL_AtomicCAS(&setup_running, 0, 1)) return;

    SDL_Thread *t = SDL_CreateThread(run_game_thread, "pong_thread", (void*)"Pong.py");
    if (!t) {
        SDL_AtomicSet(&setup_running, 0);
        return;
    }
    SDL_DetachThread(t);
}

static void on_tetris_click(void *ud) {
    (void)ud;
    if (!SDL_AtomicCAS(&setup_running, 0, 1)) return;

    SDL_Thread *t = SDL_CreateThread(run_game_thread, "tetris_thread", (void*)"tetris.py");
    if (!t) {
        SDL_AtomicSet(&setup_running, 0);
        return;
    }
    SDL_DetachThread(t);
}
static void on_spaceinvaders_click(void *ud) {
    (void)ud;
    if (!SDL_AtomicCAS(&setup_running, 0, 1)) return;

    SDL_Thread *t = SDL_CreateThread(run_game_thread, "space_invaders_thread", (void*)"spaceinvaders.py");
    if (!t) {
        SDL_AtomicSet(&setup_running, 0);
        return;
    }
    SDL_DetachThread(t);
}

int main(int argc, char *argv[]) {

    struct EngineOptions options = {0};
    options.title  = "C Game Launcher for python Programms";
    options.width  = 960;
    options.height = 564;

    Engine engine;
    if (ENGINE_init(&engine, &options) != 0) {
        fprintf(stderr, "ENGINE_init failed\n");
        return 1;
    }
    if (TTF_Init() != 0) {
        fprintf(stderr, "TTF_Init failed: %s\n", TTF_GetError());
        return 1;
    }

    State state1;
    state1.init    = initState1;
    state1.update  = updateState1;
    state1.destroy = destroyState1;

    TTF_Font *font = TTF_OpenFont("Project_Games/Font/Program_font.ttf", 20);
    STATEMANAGER_push(&engine.statemanager, &state1);

    ButtonManager buttons;
    BM_init(&buttons);

    BM_add(&buttons, (SDL_Rect) { options.width / 2 - 180, 80, 360, 96 }, "Play Tetris", on_tetris_click, &engine);
    BM_add(&buttons, (SDL_Rect) { options.width / 2 - 180, 200, 360, 96 }, "Play Space Invaders", on_spaceinvaders_click, &engine);
    BM_add(&buttons, (SDL_Rect) { options.width / 2 - 180, 320, 360, 96 }, "Play Pong", on_pong_click, &engine);
    BM_add(&buttons, (SDL_Rect) { options.width / 2 - 180, 440, 360, 96 }, "Quit", on_quit_click, &engine);

    SDL_Event e;
    Uint32 lastTime = SDL_GetTicks();
    SDL_Renderer *renderer = ENGINE_getRenderer(&engine);
    while (!engine.quit) {
        Uint32 now = SDL_GetTicks();
        float dt = (now - lastTime) / 1000.0f;
        lastTime = now;

        int mx, my;
        SDL_GetMouseState(&mx, &my);

        int clicked = 0, released = 0;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) engine.quit = 1;
            if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) clicked = 1;
            if (e.type == SDL_MOUSEBUTTONUP && e.button.button == SDL_BUTTON_LEFT) released = 1;
        }

        STATEMANAGER_update(&engine.statemanager, dt);
        BM_update(&buttons, mx, my, clicked, released);

        SDL_SetRenderDrawColor(renderer, 20, 20, 30, 255);
        SDL_RenderClear(renderer);
        BM_render(&buttons, renderer, font);
        SDL_RenderPresent(renderer);
    }

    ENGINE_free(&engine);
    return 0;
}