#include "raylib_display.c"

#include "slabes.c"

int main(void) {
    Game *game = get_game();

    field_construct_square(&game->field, 10);

    game_reset(game);

    game_set_player_position(game, (Position){0, 0});

    FIELD_AT(&game->field, 1, 0) = Wall;
    FIELD_AT(&game->field, 1, 1) = Wall;
    FIELD_AT(&game->field, 2, 1) = Wall;
    FIELD_AT(&game->field, 2, 2) = Wall;
    FIELD_AT(&game->field, 3, 0) = Wall;

    setup_display(game);

    while (!WindowShouldClose())
    {
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

            ClearBackground(BLACK);
            draw_hexagon_grid(game, hex_side);

        EndDrawing();
    }

    CloseWindow();

    field_destruct(&game->field);

    return 0;
}
