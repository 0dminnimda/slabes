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

typedef enum : uint8_t {
    DirectionCount =      6,
    UpLeft    = 1 << 5,
    Up        = 1 << 4,
    UpRight   = 1 << 3,
    DownRight = 1 << 2,
    Down      = 1 << 1,
    DownLeft  = 1 << 0,
    DirectionMax = UpLeft,
    UpDirection = UpLeft | Up | UpRight, 
    DownDirection = DownLeft | Down | DownRight, 
    AllDirections = UpDirection | DownDirection,
} Direction;

typedef Direction Walls;

typedef struct {
    size_t width, height;
    Cell *cells;
    Walls *walls;
} Field;

typedef struct {
    size_t x, y;
} Position;

typedef struct {
    Position player_position;
    Direction player_direction;
    Field field;
} Game;

#define WALLS_AT(field, x, y) (field)->walls[(y) * (field)->width + (x)]

Walls field_checked_get_walls(Field *field, ssize_t x, ssize_t y);

void field_checked_update_walls(Field *field, ssize_t x, ssize_t y, Walls value, bool add);

#define FIELD_AT(field, x, y) (field)->cells[(y) * (field)->width + (x)]
void field_checked_update_walls_one_direction(Field *field, ssize_t x, ssize_t y, Walls value, bool add);


Cell field_checked_get_cell(Field *field, ssize_t x, ssize_t y, Cell default_value);

void field_checked_set_cell(Field *field, ssize_t x, ssize_t y, Cell value);

char *direction_to_string(Direction direction);

Direction left_rotated_direction(Direction direction);

Direction right_rotated_direction(Direction direction);

Direction reverse_direction(Direction direction);

Walls game_walls_with_map_end(Game *game, Walls walls, ssize_t x, ssize_t y);

#endif // SLABES_H
