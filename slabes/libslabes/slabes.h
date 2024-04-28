#pragma once

#ifndef SLABES_H
#define SLABES_H

#include <stdbool.h>
#include <stdlib.h>

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

char *direction_to_string(Direction direction);

Direction left_rotated_direction(Direction direction);

Direction right_rotated_direction(Direction direction);

#define FIELD_AT(field, x, y) (field)->cells[(y) * (field)->width + (x)]

Cell field_check_at(Field *field, ssize_t x, ssize_t y, Cell default_value);

#endif // SLABES_H
