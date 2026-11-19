cmake_minimum_required(VERSION 4.4)
project(gamelauncher C)

set(CMAKE_C_STANDARD 11)

add_executable(gamelauncher main.c
        statemanager.c
        graphics.c
        engine.c
        buttons.c
        button_render.c

)
add_custom_command(TARGET gamelauncher POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/Project_Games
        $<TARGET_FILE_DIR:gamelauncher>/Project_Games
)
# --- SDL2 core (ships its own cmake config) ---
find_package(SDL2 REQUIRED)

# --- SDL2_image (ships its own cmake config) ---
find_package(SDL2_image REQUIRED)

# --- SDL2_ttf (ships its own cmake config) ---
find_package(SDL2_ttf REQUIRED)

# --- SDL2_gfx (NO cmake config — use pkg-config) ---
#find_package(PkgConfig REQUIRED)
#pkg_check_modules(SDL2_gfx REQUIRED SDL2_gfx)

target_link_libraries(gamelauncher PRIVATE
        SDL2::SDL2
        SDL2_image::SDL2_image
        SDL2_ttf::SDL2_ttf
        ${SDL2_gfx_LIBRARIES}
)

target_include_directories(gamelauncher PRIVATE
        ${SDL2_gfx_INCLUDE_DIRS}
)