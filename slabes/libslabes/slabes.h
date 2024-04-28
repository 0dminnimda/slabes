#pragma once

#ifndef SLABES_H
#define SLABES_H

#include <stdbool.h>
#include <stdlib.h>
#include "shared_load.h"

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

#if defined _WIN32 && !defined __GNUC__
# ifdef LIBFOO_BUILD
#  ifdef DLL_EXPORT
#   define LIBFOO_SCOPE            __declspec (dllexport)
#   define LIBFOO_SCOPE_VAR extern __declspec (dllexport)
#  endif
# elif defined _MSC_VER
#  define LIBFOO_SCOPE
#  define LIBFOO_SCOPE_VAR  extern __declspec (dllimport)
# elif defined DLL_EXPORT
#  define LIBFOO_SCOPE             __declspec (dllimport)
#  define LIBFOO_SCOPE_VAR  extern __declspec (dllimport)
# endif
#endif
#ifndef LIBFOO_SCOPE
# define LIBFOO_SCOPE
# define LIBFOO_SCOPE_VAR extern
#endif

// char *direction_to_string(Direction direction);

// Direction left_rotated_direction(Direction direction);

// Direction right_rotated_direction(Direction direction);

#define FIELD_AT(field, x, y) (field)->cells[(y) * (field)->width + (x)]

// extern __declspec (dllexport) __attribute__((weak)) __attribute__ ((visibility ("default")))  

// extern __declspec (dllexport) __declspec(dllimport) __attribute__((weak)) __attribute__ ((visibility ("default"))) 
Cell field_check_at(Field *field, ssize_t x, ssize_t y, Cell default_value);

// extern __declspec (dllexport) __attribute__((weak)) Game *get_game();

#endif // SLABES_H
