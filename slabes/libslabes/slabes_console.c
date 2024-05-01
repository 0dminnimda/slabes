#include "console_display.c"

#include "slabes.c"

int main() {
    Game *game = get_game();

    srand(time(NULL));

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
