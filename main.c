#include <stdio.h>
#include <stdlib.h>
#include "engine.h"
#include "buttons.h"

#define PY_VER "3.12.10"
#define GAMES_DIR "Project_Games"

#ifdef _WIN32
#define PY_URL "https://www.python.org/ftp/python/" PY_VER "/python-" PY_VER "-embed-amd64.zip"
#define PY_EXE "python\\python.exe"
#define PTH_FILE "python\\python312._pth"
#define GET_PIP "python\\get-pip.py"
#else
#define PY_URL "https://cmcc.mirrors.ustc.edu.cn/github-release/astral-sh/python-build-standalone/20250409/cpython-3.12.10+20250409-x86_64-unknown-linux-gnu-install_only.tar.gz"
#define PY_EXE "python/bin/python3"
#define VENV_PY "venv/bin/python3"
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
    int rc = system(cmd);
    if (rc != 0) fprintf(stderr, "Command failed (%d): %s\n", rc, cmd);
    return rc;
}

/* Returns the executable path RELATIVE to Project_Games */
static int python_exe(char *buf, size_t n) {
#ifdef _WIN32
    return snprintf(buf, n, "python\\python.exe") < (int)n ? 0 : -1;
#else
    return snprintf(buf, n, "venv/bin/python3") < (int)n ? 0 : -1;
#endif
}

static int python(const char *arg) {
    char exe[512];
    char cmd[2048];
    if (python_exe(exe, sizeof exe) != 0) return -1;

#ifdef _WIN32
    /* Change dir, run python natively, then change back.
       (The `cd /d` fixes the drive letter if it's on D:, and `cd ..` keeps the shell clean) */
    snprintf(cmd, sizeof cmd, "cd /d \"%s\" && \"%s\" %s && cd ..", GAMES_DIR, exe, arg);
#else
    snprintf(cmd, sizeof cmd, "cd \"%s\" && \"%s\" %s; cd ..", GAMES_DIR, exe, arg);
#endif
    return run(cmd);
}

static int setup_python(void) {
    char cmd[1024];
    char path[512];

    snprintf(path, sizeof path, "%s/%s", GAMES_DIR, PY_EXE);
    if (!file_exists(path)) {
        printf("Setting up Python environment in %s/...\n", GAMES_DIR);
#ifdef _WIN32
        run("if not exist " GAMES_DIR "\\python mkdir " GAMES_DIR "\\python");
        snprintf(cmd, sizeof cmd, "curl -fL -o " GAMES_DIR "\\python.zip " PY_URL);
        if (run(cmd) != 0) return 1;

        snprintf(cmd, sizeof cmd,
            "powershell -NoProfile -Command \""
            "Expand-Archive -Path '%s\\python.zip' -DestinationPath '%s\\python' -Force;"
            "$d=Get-ChildItem '%s\\python' -Directory|Select -First 1;"
            "if($d){Move-Item ($d.FullName+'\\*') '%s\\python' -Force;"
            "Remove-Item $d.FullName -Recurse -Force}\"",
            GAMES_DIR, GAMES_DIR, GAMES_DIR, GAMES_DIR);
        if (run(cmd) != 0) return 1;

        snprintf(path, sizeof path, "%s\\%s", GAMES_DIR, PY_EXE);
        if (!file_exists(path)) {
            fprintf(stderr, "Extraction failed: %s missing\n", path);
            return 1;
        }
        snprintf(cmd, sizeof cmd, "del " GAMES_DIR "\\python.zip");
        run(cmd);
#else
        run("mkdir -p " GAMES_DIR "/python");
        snprintf(cmd, sizeof cmd, "curl -fL -o " GAMES_DIR "/python.tar.gz " PY_URL);
        if (run(cmd) != 0) return 1;
        snprintf(cmd, sizeof cmd,
                 "tar -xzf " GAMES_DIR "/python.tar.gz -C " GAMES_DIR "/python --strip-components=1");
        if (run(cmd) != 0) return 1;
        snprintf(cmd, sizeof cmd, "rm " GAMES_DIR "/python.tar.gz");
        run(cmd);
#endif
    }

#ifdef _WIN32
    snprintf(cmd, sizeof cmd,
             "powershell -NoProfile -Command \""
             "(Get-Content '%s\\%s') -replace '#import site','import site' "
             "| Set-Content '%s\\%s'\"",
             GAMES_DIR, PTH_FILE, GAMES_DIR, PTH_FILE);
    run(cmd);

    snprintf(path, sizeof path, "%s\\python\\Scripts\\pip.exe", GAMES_DIR);
    if (!file_exists(path)) {
        snprintf(cmd, sizeof cmd, "curl -fL -o " GAMES_DIR "\\" GET_PIP " https://bootstrap.pypa.io/get-pip.py");
        if (run(cmd) != 0) return 1;
        snprintf(cmd, sizeof cmd,
                 "pushd \"" GAMES_DIR "\\python\" && python.exe get-pip.py && popd");
        if (run(cmd) != 0) return 1;
    }
#else
    snprintf(path, sizeof path, "%s/%s", GAMES_DIR, VENV_PY);
    if (!file_exists(path)) {
        snprintf(cmd, sizeof cmd, "\"%s/%s\" -m venv \"%s/venv\"", GAMES_DIR, PY_EXE, GAMES_DIR);
        if (run(cmd) != 0) return 1;
    }
#endif

    if (python("-m pip install --upgrade pygame-ce") != 0) return 1;
    if (python("--version") != 0) return 1;
    if (python("-c \"import pygame\"") != 0) return 1;

    printf("Ready.\n");
    return 0;
}

static int setup_thread(void *ud) {
    (void)ud;
    setup_python();
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
static void on_start_click(void *ud) {
    (void)ud;
    if (!SDL_AtomicCAS(&setup_running, 0, 1)) return;

    SDL_Thread *t = SDL_CreateThread(setup_thread, "python_setup", NULL);
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

int main(int argc, char *argv[]) {

    struct EngineOptions options = {0};
    options.title  = "C engine test";
    options.width  = 480;
    options.height = 272;

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

    BM_add(&buttons, (SDL_Rect) { 40, 40, 180, 48 }, "Play Tetris", on_tetris_click, &engine);
    BM_add(&buttons, (SDL_Rect) { 40, 100, 180, 48 }, "Setup Python", on_start_click, &engine);
    BM_add(&buttons, (SDL_Rect) { 40, 160, 180, 48 }, "Quit", on_quit_click, &engine);

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