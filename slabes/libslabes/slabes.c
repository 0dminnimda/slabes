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
    Up,
    RightUp,
    RightDown,
    Down,
    LeftDown,
    LeftUp,
} Direction;

typedef struct {
    size_t player_x, player_y;
    Direction player_direction;
    Field field;
} Game;


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
    game->player_x = 0;
    game->player_y = 0;
    game->player_direction = Up;
    field_fill(&game->field, Empty);
}

void game_set_player_position(Game *game, ssize_t x, ssize_t y) {
    if (x < 0 || x >= game->field.width) { return; }
    if (y < 0 || y >= game->field.height) { return; }

    FIELD_AT(&game->field, game->player_x, game->player_y) = Empty;
    game->player_x = x;
    game->player_y = y;
    FIELD_AT(&game->field, x, y) = Player;
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
    } else if (game->player_direction == RightUp) {
        return '>';
    } else if (game->player_direction == LeftUp) {
        return '<';
    }
    return ' ';
}

char player_lower_char(Game *game) {
    if (game->player_direction == Down) {
        return 'v';
    } else if (game->player_direction == RightDown) {
        return '>';
    } else if (game->player_direction == LeftDown) {
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
    for (ssize_t x = 0; x < game->field.width; x++) {
        char c1 = field_check_at(&game->field, x, y , ' ');
        if (c1 == Empty) { c1 = '_'; }
        if (c1 == Player) { c1 = player_lower_char(game); }
        char c2 = field_check_at(&game->field, x, y - 1, ' ');
        if (c2 == Player) { c2 = player_upper_char(game); }
        if (wide) {
            printf("\\%c%c/%c%c", c1, c1, c2, c2);
        } else {
            printf("\\%c/%c", c1, c2);
        }
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
    for (ssize_t x = 0; x < game->field.width; x++) { printf("%s", first); }
    printf("\n");

    ssize_t y = game->field.height;
    for (;;) {
        game_print_small_upper_row(game, y, wide);
        if (--y < 0) break;
        game_print_small_lower_row(game, y, wide);
        if (--y < 0) break;
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
    field_construct_square(&game.field, 6);

    game_reset(&game);

    game_set_player_position(&game, 0, 0);

    FIELD_AT(&game.field, 1, 0) = Wall;
    FIELD_AT(&game.field, 1, 1) = Wall;
    FIELD_AT(&game.field, 2, 1) = Wall;
    FIELD_AT(&game.field, 3, 0) = Wall;

    for (ssize_t i = 0; i < 6; i++) {
        game.player_direction = (Direction)(i);
        game_print_small(&game, true);
    }

    for (ssize_t i = 0; i < 3; i++) {
        game_set_player_position(&game, game.player_x + 1, game.player_y);
        game_print_small(&game, true);
    }

    field_destruct(&game.field);

    return 0;
}
