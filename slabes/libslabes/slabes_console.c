#include "console_display.c"

#include "slabes.c"

int main() {
    Game *game = get_game();

    field_construct_square(&game->field, 10);

    game_reset(game);

    game_set_player_position(game, (Position){0, 0});

    FIELD_AT(&game->field, 1, 0) = Wall;
    FIELD_AT(&game->field, 1, 1) = Wall;
    FIELD_AT(&game->field, 2, 1) = Wall;
    FIELD_AT(&game->field, 2, 2) = Wall;
    FIELD_AT(&game->field, 3, 0) = Wall;

    game_print_small(game, true);

    while (1) {
        printf("> ");
        fflush(stdout);
        char c = getchar();
        if (c == 'x') { break; }
        bool move = true;
        switch (c) {
            case 'w': game->player_direction = Up; break;
            case 's': game->player_direction = Down; break;
            case 'e': game->player_direction = UpRight; break;
            case 'd': game->player_direction = DownRight; break;
            case 'q': game->player_direction = UpLeft; break;
            case 'a': game->player_direction = DownLeft; break;
            default: move = false; break;
        }

        if (move) {
            if (!game_make_player_take_one_step(game)) continue;
            game_print_small(game, true);
        }
    }

    field_destruct(&game->field);

    return 0;
}
