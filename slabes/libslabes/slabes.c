// #include "shared_load.h"

// EXPORTED int add(int a, int b)
// {
//   return a + b;
// }

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>


#ifndef SLABES_MALLOC
void *slabes_malloc_(size_t size) {
    void *p = malloc(size);
    if (p == NULL) {
        printf("Out of memory.\n");
        exit(EXIT_FAILURE);
    }
    return p;
}
#define SLABES_MALLOC slabes_malloc_
#endif // SLABES_MALLOC

#ifndef SLABES_FREE
#define SLABES_FREE free
#endif // SLABES_FREE


/*
 _   _   _  
/0\_/1\_/2\_
\_/3\_/4\_/5\
/6\_/7\_/8\_/
\_/ \_/ \_/ 

*/

typedef enum : char {
    Wall = '#',
    Player = 'o',
    Empty = ' ',
} Cell;

typedef struct {
    size_t width, height;
    Cell *cells;
} Field;

typedef enum {
    UpLeft,
    Up,
    UpRight,
    DownRight,
    Down,
    DownLeft,
} Direction;

typedef struct {
    size_t x, y;
} Position;

typedef struct {
    Position player_position;
    Direction player_direction;
    Field field;
} Game;


char *direction_to_string(Direction direction) {
    switch (direction) {
        case UpLeft: return "UpLeft";
        case Up: return "Up";
        case UpRight: return "UpRight";
        case DownRight: return "DownRight";
        case Down: return "Down";
        case DownLeft: return "DownLeft";
        default: return "Unknown";
    }
}

#define FIELD_AT(field, x, y) (field)->cells[(y) * (field)->width + (x)]

Cell field_check_at(Field *field, ssize_t x, ssize_t y, Cell default_value) {
    if (x >= field->width || x < 0) {
        return default_value;
    }
    if (y >= field->height || y < 0) {
        return default_value;
    }
    return FIELD_AT(field, x, y);
}


void field_construct(Field *field, size_t width, size_t height) {
    field->width = width;
    field->height = height;
    field->cells = (Cell *)SLABES_MALLOC(sizeof(Cell) * width * height);
}

// the goal is to make it so look most like a square
// here I'm trying to make diagonals have eqaul number of cells
void field_construct_square(Field *field, size_t side) {
    field_construct(field, side, side*2 + 1);
}

void field_destruct(Field *field) {
    SLABES_FREE(field->cells);
}

void field_fill(Field *field, Cell value) {
    memset(field->cells, value, sizeof(Cell) * field->width * field->height);
}

void game_reset(Game *game) {
    game->player_position.x = 0;
    game->player_position.y = 0;
    game->player_direction = Up;
    field_fill(&game->field, Empty);
}

void game_set_player_position(Game *game, Position pos) {
    if (pos.x < 0 || pos.x >= game->field.width) { return; }
    if (pos.y < 0 || pos.y >= game->field.height) { return; }

    FIELD_AT(&game->field, game->player_position.x, game->player_position.y) = Empty;
    game->player_position = pos;
    FIELD_AT(&game->field, pos.x, pos.y) = Player;
}

/*
    __    __
 __/up\__/..\
/ul\__/ur\__/
\__/it\__/..\
/dl\__/dr\__/
\__/dn\__/..\
   \__/  \__/

.. up
ul ur
.. it
dl dr
.. dn

- or -

up ..
ul ur
it ..
dl dr
dn ..

depending whether we are at the inbetween row or on the base row

*/

bool game_move_position_in_direction(Game *game, Position *pos, Direction direction) {
    Position new_pos = *pos;

    if (new_pos.y % 2 == 0) {
        if (direction == UpLeft || direction == DownLeft) {
            new_pos.x -= 1;
        }
    } else {
        if (direction == UpRight || direction == DownRight) {
            new_pos.x += 1;
        }
    }

    if (direction == Up) {
        new_pos.y += 2;
    } else if (direction == Down) {
        new_pos.y -= 2;
    } else if (direction == UpLeft || direction == UpRight) {
        new_pos.y += 1;
    } else if (direction == DownLeft || direction == DownRight) {
        new_pos.y -= 1;
    }

    // unsigned underflow is a defined behavior,
    // so no problems relying on it here for check if 0 - <sometihng> happened
    if (new_pos.y >= game->field.height || new_pos.x >= game->field.width) {
        return false;
    }

    *pos = new_pos;
    return true;
}

bool game_make_player_take_one_step(Game *game) {
    Position pos = game->player_position;
    if (!game_move_position_in_direction(game, &pos, game->player_direction)) {
        printf("cannot move in this direction (%s)\n", direction_to_string(game->player_direction));
        return false;
    }
    game_set_player_position(game, pos);
    return true;
}

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

static Game game;

int main() {
    field_construct_square(&game.field, 10);

    game_reset(&game);

    game_set_player_position(&game, (Position){0, 0});

    FIELD_AT(&game.field, 1, 0) = Wall;
    FIELD_AT(&game.field, 1, 1) = Wall;
    FIELD_AT(&game.field, 2, 1) = Wall;
    FIELD_AT(&game.field, 2, 2) = Wall;
    FIELD_AT(&game.field, 3, 0) = Wall;

    game_print_small(&game, true);

    while (1) {
        printf("> ");
        fflush(stdout);
        char c = getchar();
        if (c == 'x') { break; }
        bool move = true;
        switch (c) {
            case 'w': game.player_direction = Up; break;
            case 's': game.player_direction = Down; break;
            case 'e': game.player_direction = UpRight; break;
            case 'd': game.player_direction = DownRight; break;
            case 'q': game.player_direction = UpLeft; break;
            case 'a': game.player_direction = DownLeft; break;
            default: move = false; break;
        }

        if (move) {
            if (!game_make_player_take_one_step(&game)) continue;
            game_print_small(&game, true);
        }
    }

    field_destruct(&game.field);

    return 0;
}
