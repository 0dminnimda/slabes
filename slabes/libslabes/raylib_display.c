#include "slabes.h"
#include "raylib.h"
#include <math.h>

typedef struct {
    float elapsed_time;
} State;

State state;

const int screen_width = 800;
const int screen_height = 450;

const double hex_side = 20;
const int offset_x= 50;
const int offset_y = 50;

const Color empty_color = DARKBLUE;
const Color wall_color = GRAY;
const Color player_color = WHITE;

Color cell_color(Cell cell) {
    switch (cell) {
        case Player: return player_color;
        case Wall: return wall_color;
        default: return empty_color;
    }
}


void draw_hexagon_grid(Game *game, double s) {
    double x_delta = 3 * s;  // distance between hexagons in the same row
    double y_delta = sqrt(3) / 2 * s;  // distance between rows
    double total_y = (game->field.height - 1) * y_delta;

    for (ssize_t yi = 0; yi < game->field.height; yi++) {
        for (ssize_t xi = 0; xi < game->field.width; xi++) {
            double y = total_y - (yi * y_delta);
            double x = xi * x_delta + (yi % 2) * (x_delta / 2);
            Vector2 center = {x + offset_x, y + offset_y};

            DrawPoly(center, 6, s, 30.0f, cell_color(FIELD_AT(&game->field, xi, yi)));
            DrawPolyLines(center, 6, s, 30.0f, WHITE);
        }
    }
}

bool setup_display() {
    SetTraceLogLevel(LOG_ERROR);

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
