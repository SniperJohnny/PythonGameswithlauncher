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

# --- SDL2_ttf (ships its own cmake config) ---
find_package(SDL2_ttf CONFIG REQUIRED)

target_link_libraries(gamelauncher PRIVATE
        SDL2::SDL2
        $<IF:$<TARGET_EXISTS:SDL2_ttf::SDL2_ttf>,SDL2_ttf::SDL2_ttf,SDL2_ttf::SDL2_ttf-static>
        ${SDL2_gfx_LIBRARIES}
)
target_include_directories(gamelauncher PRIVATE
        ${SDL2_gfx_INCLUDE_DIRS}
)
target_include_directories(gamelauncher PRIVATE
        $<$<PLATFORM_ID:Linux>:/home/SniperJohnny/.vcpkg-clion/vcpkg/installed/x64-linux/include/SDL2>
)
target_include_directories(gamelauncher PRIVATE
        /home/SniperJohnny/.vcpkg-clion/vcpkg/installed/x64-linux/include/SDL2
)