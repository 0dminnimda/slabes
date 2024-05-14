// GENERATED FROM /*file*/

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>

#include "libslabes/slabes.c"

// #define SLABES_DEBUG_OP

#ifdef _WIN32
#include <windows.h>
#elif __unix__
#include <unistd.h>
#endif

#ifndef NO_DELAY_ON_ROBOT_OP
void sleep_ms(int milliseconds) {
#ifdef _WIN32
    Sleep(milliseconds);
#elif __unix__
    usleep(milliseconds * 1000); // usleep takes sleep time in microseconds
#endif
}

#define ROBOT_OP_DELAY sleep_ms(200)
#else
#define ROBOT_OP_DELAY
#endif

typedef bool unsigned_bool;
typedef unsigned char unsigned_char;
typedef unsigned short unsigned_short;

typedef uint8_t unsigned_int8_t;
typedef uint16_t unsigned_int16_t;

#if __has_include(<stdckdint.h>)
# include <stdckdint.h>
#elif defined(__GNUC__)  /*gcc and clagn have this*/
#  define ckd_add(R, A, B) __builtin_add_overflow ((A), (B), (R))
#  define ckd_sub(R, A, B) __builtin_sub_overflow ((A), (B), (R))
#  define ckd_mul(R, A, B) __builtin_mul_overflow ((A), (B), (R))
#else
#  define ckd_add(R, A, B) (
    (((B) > 0 && (A) > INT_MAX - (B)) || ((B) < 0 && (A) < INT_MIN - (B))) ?
    true : ((*(R) = (A) + (B)), false)
)
#  define ckd_sub(R, A, B) (
    (((B) < 0 && (A) > INT_MAX + (B)) || ((B) > 0 && (A) < INT_MIN + (B))) ?
    true : ((*(R) = (A) + (B)), false)
)
// #define ckd_mul(R, A, B) __builtin_mul_overflow ((A), (B), (R))
// // There may be a need to check for -1 for two's complement machines.
// // If one number is -1 and another is INT_MIN, multiplying them we get abs(INT_MIN) which is 1 higher than INT_MAX
// if (a == -1 && x == INT_MIN) // `a * x` can overflow
// if (x == -1 && a == INT_MIN) // `a * x` (or `a / x`) can overflow
// // general case
// if (x != 0 && a > INT_MAX / x) // `a * x` would overflow
// if (x != 0 && a < INT_MIN / x) // `a * x` would underflow
#endif


/*int-types*/
/*int-ops*/
/*int-conv*/

slabes_type_unsigned_tiny slabes_func___robot_command_go() {
    ROBOT_OP_DELAY;
    if (game_make_player_take_one_step(get_game())) {
        update_game_display();
        return 1;
    }
    return 0;
}

slabes_type_unsigned_tiny slabes_func___robot_command_rl() {
    ROBOT_OP_DELAY;
    get_game()->player_direction = left_rotated_direction(get_game()->player_direction);
    update_game_display();
    return 1;
}

slabes_type_unsigned_tiny slabes_func___robot_command_rr() {
    ROBOT_OP_DELAY;
    get_game()->player_direction = right_rotated_direction(get_game()->player_direction);
    update_game_display();
    return 1;
}

slabes_type_unsigned_tiny slabes_assert(slabes_type_unsigned_tiny value, const char *msg) {
    if (!value) {
        printf("Assertion failed: %s\n", msg);
        exit(1);
    }
    return value;
}


/*decl*/

/*main*/

int main(int argc, char *argv[]) {
    char *libname = NULL;
    if (argc >= 2) {
        libname = argv[1];
    }
    setup_game(libname, 10);

    printf("Starting...\n");

    update_game_display();
    ROBOT_OP_DELAY;
    program_main();
    update_game_display();

    printf("Finishing...\n");

    cleanup_game();
    return 0;
}
