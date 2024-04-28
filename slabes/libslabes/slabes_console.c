#include "slabes.c"

/*
 _   _   _  
/#\_/ \_/ \_
\#/ \_/#\_/ \
/ \_/#\#/o\_/
\_/ \#/ \_/ 

 _   _   _  
/#\_/ \_/o\_
\#/ \_/#\_/ \
  \_/ \#/ \_/

 __    __    __  
/##\__/  \__/  \__
\##/  \__/##\ _/  \
/  \__/##\##/oo\__/
\__/  \##/  \__/ 

*/


char player_upper_char(Game *game) {
    if (game->player_direction == Up) {
        return '^';
    } else if (game->player_direction == UpRight) {
        return '>';
    } else if (game->player_direction == UpLeft) {
        return '<';
    }
    return ' ';
}

char player_lower_char(Game *game) {
    if (game->player_direction == Down) {
        return 'v';
    } else if (game->player_direction == DownRight) {
        return '>';
    } else if (game->player_direction == DownLeft) {
        return '<';
    }
    return '_';
}


void game_print_small_upper_row(Game *game, ssize_t y, bool wide) {
    char c0 = y? '/' : ' ';
    for (ssize_t x = 0; x < game->field.width; x++) {
        char c1 = field_check_at(&game->field, x, y - 1, ' ');
        if (c1 == Player) { c1 = player_upper_char(game); }
        char c2 = field_check_at(&game->field, x, y, ' ');
        if (c2 == Empty) { c2 = '_'; }
        if (c2 == Player) { c2 = player_lower_char(game); }
        if (wide) {
            printf("%c%c%c\\%c%c", c0, c1, c1, c2, c2);
        } else {
            printf("%c%c\\%c", c0, c1, c2);
        }
        c0 = '/';
    }
    if (y != (game->field.height)) { printf("/"); }
    printf("\n");
}

void game_print_small_lower_row(Game *game, ssize_t y, bool wide) {
    char c0 = (y < game->field.height)? '\\' : ' ';
    for (ssize_t x = 0; x < game->field.width; x++) {
        char c1 = field_check_at(&game->field, x, y , ' ');
        if (c1 == Empty) { c1 = '_'; }
        if (c1 == Player) { c1 = player_lower_char(game); }
        char c2 = field_check_at(&game->field, x, y - 1, ' ');
        if (c2 == Player) { c2 = player_upper_char(game); }
        if (wide) {
            printf("%c%c%c/%c%c", c0, c1, c1, c2, c2);
        } else {
            printf("%c%c/%c", c0, c1, c2);
        }
        c0 = '\\';
    }
    if (y) { printf("\\"); }
    printf("\n");
}

void game_print_small(Game *game, bool wide) {
    if (game->field.height == 0 || game->field.width == 0) {
        printf("<empty game field>\n");
        return;
    }

    char *first = wide? " __   " : " _  ";
    if (game->field.height % 2 == 0) {
        first = wide? "   __ " : "  _ ";
        printf(" ");
    }

    for (ssize_t x = 0; x < game->field.width; x++) { printf("%s", first); }
    printf("\n");

    ssize_t y = game->field.height;
    if (game->field.height % 2 == 0) {
        for (;;) {
            game_print_small_lower_row(game, y, wide);
            if (--y < 0) break;
            game_print_small_upper_row(game, y, wide);
            if (--y < 0) break;
        }
    } else {
        for (;;) {
            game_print_small_upper_row(game, y, wide);
            if (--y < 0) break;
            game_print_small_lower_row(game, y, wide);
            if (--y < 0) break;
        }
    }
}

/*
  _   _   _   _    
 / \_/ \_/#\_/ \
|   |   |###|   |
 \_/ \_/ \#/#\_/ \
  |   |   |###|   |
 /#\_/ \_/ \#/ \_/
|###|   | O |   |
 \#/ \_/ \_/ \_/

  __    __    __    __    
 /  \__/  \__/##\__/  \
|    ||    ||####||    ||
 \__/  \__/  \##/##\__/  \
  ||    ||    ||####||    |
 /##\__/  \__/  \##/  \__/
|####||    || () ||    ||
 \##/  \__/  \__/  \__/

  ___     ___     ___     ___    
 /   \ _ /   \ _ /###\___/   \
|     |_|     |_|#####|_|     |__
 \___/   \___/   \###/###\___/   \
  |_|     |_|     |_|#####|_|     |
 /###\___/   \___/   \###/   \___/
|#####|_|     |_|  @  |_|     |
 \###/   \___/   \___/   \___/

*/

#ifndef SLABES_CONSOLE_NO_MAIN

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

#endif // SLABES_CONSOLE_NO_MAIN
