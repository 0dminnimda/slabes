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

void field_print_small_upper_row(Field *field, ssize_t y, bool wide) {
    char c0 = (y == field->height)? ' ' : '/';
    for (ssize_t x = 0; x < field->width; x++) {
        char c1 = field_check_at(field, x, y, ' ');
        char c2 = field_check_at(field, x, y - 1, ' ');
        if (c2 == Empty) { c2 = '_'; }
        if (wide) {
            printf("%c%c%c\\%c%c", c0, c1, c1, c2, c2);
        } else {
            printf("%c%c\\%c", c0, c1, c2);
        }
        c0 = '/';
    }
    if (y) { printf("/"); }
    printf("\n");
}

void field_print_small_lower_row(Field *field, ssize_t y, bool wide) {
    for (ssize_t x = 0; x < field->width; x++) {
        char c1 = field_check_at(field, x, y - 1 , ' ');
        if (c1 == Empty) { c1 = '_'; }
        if (c1 == Player) { c1 = '_'; }
        char c2 = field_check_at(field, x, y, ' ');
        if (wide) {
            printf("\\%c%c/%c%c", c1, c1, c2, c2);
        } else {
            printf("\\%c/%c", c1, c2);
        }
    }
    if (y != field->height) { printf("\\"); }
    printf("\n");
}

void field_print_small(Field *field, bool wide) {
    if (field->height == 0) {
        printf("<empty field>\n");
        return;
    }

    char *first = wide? " __   " : " _  ";
    for (ssize_t x = 0; x < field->width; x++) { printf("%s", first); }
    printf("\n");

    ssize_t y = 0;
    for (;;) {
        field_print_small_upper_row(field, y, wide);
        if (++y > field->height) break;
        field_print_small_lower_row(field, y, wide);
        if (++y > field->height) break;
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


int main() {
    Field field;
    field_construct_square(&field, 6);

    field_fill(&field, Empty);

    FIELD_AT(&field, 0, 0) = Player;
    FIELD_AT(&field, 1, 0) = Wall;
    FIELD_AT(&field, 1, 1) = Wall;
    FIELD_AT(&field, 2, 1) = Wall;
    FIELD_AT(&field, 3, 0) = Wall;

    field_print_small(&field, true);

    field_destruct(&field);

    return 0;
}
