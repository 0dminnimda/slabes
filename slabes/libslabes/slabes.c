// #include "shared_load.h"

// EXPORTED int add(int a, int b)
// {
//   return a + b;
// }

#include "slabes.h"

#include <stdio.h>
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


Game *get_game() {
    static Game game;
    return &game;
}

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
