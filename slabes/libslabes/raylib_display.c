#include "slabes.h"
#include "raylib.h"
#include "raymath.h"
#include <math.h>

typedef struct {
    float elapsed_time;
} State;

State state;

#if RAYLIB_VERSION_MAJOR >= 5
const double hex_start_ange = 0.0;
#else
const double hex_start_ange = 30.0;
#endif

const int screen_width = 800;
const int screen_height = 450;

const double hex_side = 20;
const int offset_x= 50;
const int offset_y = 50;

const Color empty_color = DARKBLUE;
const Color wall_color = GRAY;
const Color player_color = WHITE;
const Color player_direction_color = GREEN;

Color cell_color(Cell cell) {
    switch (cell) {
        case Player: return player_color;
        case Wall: return wall_color;
        default: return empty_color;
    }
}

double direction_to_angle(Direction direction) {
    switch (direction) {
        case UpLeft: return 3.0*PI / 4.0;
        case Up: return PI / 2.0;
        case UpRight: return PI / 4.0;
        case DownRight: return -PI / 4.0;
        case Down: return -PI / 2.0;
        case DownLeft: return -3.0*PI / 4.0;
        default: return direction;
    }
}

void draw_player_direction(Game *game, double hex_side, Vector2 center) {
    double angle = direction_to_angle(game->player_direction);
    double len = sqrt(3) / 2 * hex_side;
    Vector2 hand = {len * sin(angle), len * cos(angle)};
    // Vector2 pt1 = Vector2Add(center, hand);
    // Vector2 pt2 = Vector2Subtract(center, hand);
    DrawLineEx(center, Vector2Add(center, hand), 10, player_direction_color);
}

void draw_hexagon_grid(Game *game, double hex_side) {
    double x_delta = 3 * hex_side;  // distance between hexagons in the same row
    double y_delta = sqrt(3) / 2 * hex_side;  // distance between rows
    double total_y = (game->field.height - 1) * y_delta;

    for (ssize_t yi = 0; yi < game->field.height; yi++) {
        for (ssize_t xi = 0; xi < game->field.width; xi++) {
            double y = total_y - (yi * y_delta);
            double x = xi * x_delta + (yi % 2) * (x_delta / 2);
            Vector2 center = {x + offset_x, y + offset_y};

            Cell cell = FIELD_AT(&game->field, xi, yi);
            DrawPoly(center, 6, hex_side, hex_start_ange, cell_color(cell));
            if (cell == Player) {
                draw_player_direction(game, hex_side, center);
            }
            DrawPolyLines(center, 6, hex_side, hex_start_ange, WHITE);
        }
    }
}

bool setup_display() {
    SetTraceLogLevel(LOG_ERROR);

    SetConfigFlags(FLAG_WINDOW_RESIZABLE | FLAG_VSYNC_HINT);
    InitWindow(screen_width, screen_height, "slabes");
    SetTargetFPS(60);

    return true;
}

void update_display(Game *game) {
    state.elapsed_time += GetFrameTime();

    if (!WindowShouldClose()) {
        BeginDrawing();

        ClearBackground(BLACK);

        draw_hexagon_grid(game, hex_side);

        EndDrawing();
    }
    
}

void cleanup_display() {
    while (!WindowShouldClose()) {
        state.elapsed_time += GetFrameTime();

        BeginDrawing();

        // ClearBackground(BLACK);

        // draw_hexagon_grid(game, hex_side);

        EndDrawing();
    }
    CloseWindow();
}
