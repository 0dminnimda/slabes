#pragma once

#ifndef SLABES_H
#define SLABES_H

#include <stdbool.h>
#include <stdlib.h>
#include <stdint.h>

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

typedef uint8_t Walls;

typedef struct {
    size_t width, height;
    Cell *cells;
    Walls *walls;
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

#define GET_WALL_DOWN_RIGHT(walls) ((walls) & (1 << 2))
#define GET_WALL_DOWN(walls) ((walls) & (1 << 1))
#define GET_WALL_DOWN_LEFT(walls) ((walls) & (1 << 0))

#define ON_WALL_DOWN_RIGHT(walls, value) ((walls) & ((value) << 2))
#define ON_WALL_DOWN(walls, value) ((walls) & ((value) << 1))
#define ON_WALL_DOWN_LEFT(walls, value) ((walls) & ((value) << 0))

#define OFF_WALL_DOWN_RIGHT(walls, value) ((walls) & (~((value) << 2)))
#define OFF_WALL_DOWN(walls, value) ((walls) & (~((value) << 1)))
#define OFF_WALL_DOWN_LEFT(walls, value) ((walls) & (~((value) << 0)))

#define SET_WALL_DOWN_RIGHT(walls, value) ((value)? ON_WALL_DOWN_RIGHT(walls, value) : OFF_WALL_DOWN_RIGHT(walls, value))
#define SET_WALL_DOWN(walls, value) ((value)? ON_WALL_DOWN(walls, value) : OFF_WALL_DOWN(walls, value))
#define SET_WALL_DOWN_LEFT(walls, value) ((value)? ON_WALL_DOWN_LEFT(walls, value) : OFF_WALL_DOWN_LEFT(walls, value))

#define WALLS_AT(field, x, y) (field)->walls[(y) * (field)->width + (x)]

Walls field_walls_check_at(Field *field, ssize_t x, ssize_t y);

#define FIELD_AT(field, x, y) (field)->cells[(y) * (field)->width + (x)]

Cell field_check_at(Field *field, ssize_t x, ssize_t y, Cell default_value);

char *direction_to_string(Direction direction);

Direction left_rotated_direction(Direction direction);

Direction right_rotated_direction(Direction direction);

Walls game_walls_with_map_end(Game *game, Walls walls, ssize_t x, ssize_t y);

#endif // SLABES_H
