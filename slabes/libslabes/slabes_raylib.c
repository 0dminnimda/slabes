#include "raylib_display.c"

#include "slabes.c"


#ifdef _WIN32
#define Rectangle WinRectangle
#define CloseWindow WinCloseWindow
#define ShowCursor WinShowCursor
#include <windows.h>
#undef Rectangle
#undef CloseWindow
#undef ShowCursor
#elif __unix__
#include <unistd.h>
#endif

void sleep_ms(int milliseconds) {
#ifdef _WIN32
    Sleep(milliseconds);
#elif __unix__
    usleep(milliseconds * 1000); // usleep takes sleep time in microseconds
#endif
}

void game_generate_a_maze_animated(Game *game) {
    field_fill_walls(&game->field, 0xFF);
    // game_set_player_position(game, (Position){0, 0});

    bool *visited = (bool *)SLABES_MALLOC(sizeof(bool) * game->field.width * game->field.height);
    memset(visited, 0, sizeof(bool) * game->field.width * game->field.height);

    Position *stack_base = (Position *)SLABES_MALLOC(sizeof(Position) * game->field.width * game->field.height);
    Position *stack_head = stack_base;

    Position current_pos = game->player_position;
    visited[INDEX_OF(&game->field, current_pos.x, current_pos.y)] = true;
    *stack_head++ = current_pos;

    ssize_t max_distance = 0;
    Position fartherst_pos = current_pos;

    while (stack_head - stack_base) {
        sleep_ms(50);
        BeginDrawing();
            ClearBackground(background_color);
            draw_hexagon_grid(game, hex_side);
        EndDrawing();

        if (stack_head - stack_base > max_distance) {
            max_distance = stack_head - stack_base;
            fartherst_pos = *(stack_head - 1);
        }

        current_pos = *--stack_head;

        size_t direction_shift = rand();
        for (size_t i = 0; i < DirectionCount; ++i) {
            Direction dir = 1 << ((direction_shift + i) % DirectionCount);

            Position neighbour_pos = current_pos;
            if (!field_move_position_in_direction(&game->field, &neighbour_pos, dir)) { continue; }
            if (visited[INDEX_OF(&game->field, neighbour_pos.x, neighbour_pos.y)]) { continue; }

            // remove the wall between current and neighbour
            WALLS_AT(&game->field, current_pos.x, current_pos.y) &= ~dir;
            WALLS_AT(&game->field, neighbour_pos.x, neighbour_pos.y) &= ~reverse_direction(dir);

            visited[INDEX_OF(&game->field, neighbour_pos.x, neighbour_pos.y)] = true;
            field_checked_set_cell(&game->field, neighbour_pos.x, neighbour_pos.y, Wall);
            
            *stack_head++ = current_pos;
            *stack_head++ = neighbour_pos;
            break;
        }
    }

    field_checked_set_cell(&game->field, fartherst_pos.x, fartherst_pos.y, Finish);

    SLABES_FREE(stack_base);
    SLABES_FREE(visited);
}

int main(void) {
    Game *game = get_game();

    srand(time(NULL));

    field_construct_square(&game->field, 10);

    game_reset(game);

    game_set_player_position(game, (Position){0, 0});

#if 0
    field_checked_update_walls(&game->field, 0, 0, UpRight | DownRight, true);
    field_checked_update_walls(&game->field, 0, 2, UpRight | DownRight, true);
    field_checked_update_walls(&game->field, 0, 4, UpRight | DownRight, true);
    field_checked_update_walls(&game->field, 0, 6, UpRight | DownRight, true);
    field_checked_update_walls(&game->field, 0, 8, UpRight | DownRight, true);
    field_checked_update_walls(&game->field, 0, 10, UpRight | DownRight, true);
    field_checked_update_walls(&game->field, 0, 12, DownRight, true);
    field_checked_update_walls(&game->field, 0, 13, Down, true);
    field_checked_update_walls(&game->field, 0, 14, Down | DownRight, true);

    field_checked_update_walls(&game->field, 5, 5, UpLeft | DownLeft, true);
#endif

    setup_display(game);

    // while (!WindowShouldClose()) {
    //     if (IsWindowResized()) {
    //         recalculate_sizes(game);
    //     }

    //     BeginDrawing();
    //         ClearBackground(background_color);
    //     EndDrawing();
    // }

    game_generate_a_maze_animated(game);
    // game_generate_a_maze(game);

    while (!WindowShouldClose()) {
        if (IsWindowResized()) {
            recalculate_sizes(game);
        }

        bool move = true;
        if      (IsKeyDown(KEY_W)) game->player_direction = Up;
        else if (IsKeyDown(KEY_S)) game->player_direction = Down;
        else if (IsKeyDown(KEY_E)) game->player_direction = UpRight;
        else if (IsKeyDown(KEY_D)) game->player_direction = DownRight;
        else if (IsKeyDown(KEY_Q)) game->player_direction = UpLeft;
        else if (IsKeyDown(KEY_A)) game->player_direction = DownLeft;
        else move = false;

        if (move) {
            game_make_player_take_one_step(game);
        }

        BeginDrawing();

            ClearBackground(background_color);
            draw_hexagon_grid(game, hex_side);

        EndDrawing();
    }

    CloseWindow();

    field_destruct(&game->field);

    return 0;
}
