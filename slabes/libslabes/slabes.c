#include "slabes.h"

#include <ltdl.h>
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

Direction left_rotated_direction(Direction direction) {
    switch (direction) {
        case UpLeft: return Up;
        case Up: return UpRight;
        case UpRight: return DownRight;
        case DownRight: return Down;
        case Down: return DownLeft;
        case DownLeft: return UpLeft;
        default: return direction;
    }
}

Direction right_rotated_direction(Direction direction) {
    switch (direction) {
        case DownLeft: return Down;
        case Down: return DownRight;
        case DownRight: return UpRight;
        case UpRight: return Up;
        case Up: return UpLeft;
        case UpLeft: return DownLeft;
        default: return direction;
    }
}

Direction reverse_direction(Direction direction) {
    switch (direction) {
        case DownLeft: return UpRight;
        case Down: return Up;
        case DownRight: return UpLeft;
        case UpRight: return DownLeft;
        case Up: return Down;
        case UpLeft: return DownRight;
        default: return direction;
    }
}

Walls field_checked_get_walls(Field *field, ssize_t x, ssize_t y) {
    if (x >= field->width || x < 0) {
        return 0xFF;
    }
    if (y >= field->height || y < 0) {
        return 0xFF;
    }
    return WALLS_AT(field, x, y);

}

bool field_move_position_in_direction(Field *field, Position *pos, Direction direction);

void field_checked_update_walls(Field *field, ssize_t x, ssize_t y, Walls value, bool add) {
    if (x >= field->width || x < 0) {
        return;
    }
    if (y >= field->height || y < 0) {
        return;
    }

    for (size_t i = 1; i <= DirectionMax; i <<= 1) {
        if (!(value & i)) continue;

        Position pos = {x, y};
        if (field_move_position_in_direction(field, &pos, i)) {
            if (add) {
                WALLS_AT(field, pos.x, pos.y) |= reverse_direction(i);
            } else {
                WALLS_AT(field, pos.x, pos.y) &= ~reverse_direction(i);
            }
        }
    }

    if (add) {
        WALLS_AT(field, x, y) |= value;
    } else {
        WALLS_AT(field, x, y) &= ~value;
    }
}

Walls game_walls_with_map_end(Game *game, Walls walls, ssize_t x, ssize_t y) {
    if (y % 2 == 0) {
        if (x == 0) {
            walls |= UpLeft | DownLeft;
        }
    }
    if (y % 2 == game->field.height % 2) {
        if (x == (game->field.width - 1)) {
            walls |= UpRight | DownRight;
        }
    }
    if (y == 0) {
        walls |= DownDirection;
    }
    if (y == 1) {
        walls |= Down;
    }
    if (y == (game->field.height - 2)) {
        walls |= Up;
    }
    if (y == (game->field.height - 1)) {
        walls |= UpDirection;
    }
    return walls;
}

Cell field_checked_get_cell(Field *field, ssize_t x, ssize_t y, Cell default_value) {
    if (x >= field->width || x < 0) {
        return default_value;
    }
    if (y >= field->height || y < 0) {
        return default_value;
    }
    return FIELD_AT(field, x, y);
}

void field_checked_set_cell(Field *field, ssize_t x, ssize_t y, Cell value) {
    if (x >= field->width || x < 0) {
        return;
    }
    if (y >= field->height || y < 0) {
        return;
    }
    FIELD_AT(field, x, y) = value;
}

void field_construct(Field *field, size_t width, size_t height) {
    field->width = width;
    field->height = height;
    field->cells = (Cell *)SLABES_MALLOC(sizeof(Cell) * width * height);
    field->walls = (Walls *)SLABES_MALLOC(sizeof(Walls) * width * height);
}

// the goal is to make it so look most like a square
// here I'm trying to make diagonals have eqaul number of cells
void field_construct_square(Field *field, size_t side) {
    field_construct(field, side, side*2 + 1);
}

void field_destruct(Field *field) {
    SLABES_FREE(field->cells);
    SLABES_FREE(field->walls);
}

void field_fill_cells(Field *field, Cell value) {
    memset(field->cells, value, sizeof(Cell) * field->width * field->height);
}

void field_fill_walls(Field *field, Walls value) {
    memset(field->walls, value, sizeof(Walls) * field->width * field->height);
}

void game_reset(Game *game) {
    game->player_position.x = 0;
    game->player_position.y = 0;
    game->player_direction = Up;
    field_fill_cells(&game->field, Empty);
    field_fill_walls(&game->field, 0);
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

bool field_move_position_in_direction(Field *field, Position *pos, Direction direction) {
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
    if (new_pos.y >= field->height || new_pos.x >= field->width) {
        return false;
    }

    *pos = new_pos;
    return true;
}

bool cell_is_obstacle(Cell cell) {
    switch (cell) {
        case Wall: return true;
        default: return false;
    }
}

bool game_make_player_take_one_step(Game *game) {
    Position pos = game->player_position;
    if (!field_move_position_in_direction(&game->field, &pos, game->player_direction)) {
        // printf("cannot move in this direction (%s)\n", direction_to_string(game->player_direction));
        return false;
    }
    if (cell_is_obstacle(FIELD_AT(&game->field, pos.x, pos.y))) {
        return false;
    }
    if (field_checked_get_walls(&game->field, game->player_position.x, game->player_position.y) & game->player_direction) {
        return false;
    }
    game_set_player_position(game, pos);
    return true;
}

typedef void (*void_game_function_t)(Game *game);
typedef bool (*bool_game_function_t)(Game *game);

static lt_dlhandle library_handle = NULL;

bool_game_function_t setup_display_function = NULL;
void_game_function_t update_display_function = NULL;
void_game_function_t cleanup_display_function = NULL;

bool load_library(char *libname) {
    if (lt_dlinit()) {
        printf("Failed to initialize libltdl\n");
        printf("Continuing without displaying game state\n");
        return true;
    }

    library_handle = lt_dlopen(libname);
    if (!library_handle) {
        printf("Failed to load %s: %s\n", libname, lt_dlerror());
        printf("Continuing without displaying game state\n");
        return true;
    }

    setup_display_function = (bool_game_function_t)lt_dlsym(library_handle, "setup_display");
    if (!setup_display_function) {
        fprintf(stderr, "Failed to find setup_display function: %s\n", lt_dlerror());
        return false;
    }

    update_display_function = (void_game_function_t)lt_dlsym(library_handle, "update_display");
    if (!update_display_function) {
        fprintf(stderr, "Failed to find update_display function: %s\n", lt_dlerror());
        return false;
    }

    cleanup_display_function = (void_game_function_t)lt_dlsym(library_handle, "cleanup_display");
    if (!cleanup_display_function) {
        fprintf(stderr, "Failed to find cleanup_display function: %s\n", lt_dlerror());
        return false;
    }

    return true;
}

bool setup_game(char *libname, size_t field_side) {
    Game *game = get_game();

    field_construct_square(&game->field, field_side);
    game_reset(game);
    game_set_player_position(game, (Position){0, 0});

    if (libname && !load_library(libname)) {
        return false;
    }

    if (setup_display_function) {
        if (!setup_display_function(game)) {
            return false;
        }
    }

    return true;
}

void update_game_display() {
    if (update_display_function) {
        update_display_function(get_game());
    }
}

void cleanup_game() {
    Game *game = get_game();

    if (cleanup_display_function) {
        cleanup_display_function(game);
    }

    lt_dlclose(library_handle);
    lt_dlexit();

    field_destruct(&game->field);
}
