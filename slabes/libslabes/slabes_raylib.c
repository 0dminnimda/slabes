#include "raylib_display.c"

#include "slabes.c"

int main(void) {
    Game *game = get_game();

    field_construct_square(&game->field, 10);

    game_reset(game);

    game_set_player_position(game, (Position){0, 0});

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

    setup_display(game);

    while (!WindowShouldClose())
    {
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
