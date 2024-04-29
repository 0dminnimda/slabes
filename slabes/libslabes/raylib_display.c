#include "slabes.h"
#include "raylib.h"
#include <math.h>

typedef struct {
    float elapsed_time;
} State;

State state;

const int screenWidth = 800;
const int screenHeight = 450;

const double s = 20;  // Side length of the hexagon
const int num_rows = 8;  // Number of rows
const int num_cols = 12;  // Number of columns
const int offsetX = 50;  // Horizontal offset to center the grid
const int offsetY = 50;  // Vertical offset to center the grid

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

    char *msg[16] = {0};

    for (ssize_t yi = 0; yi < game->field.height - 1; yi++) {
        for (ssize_t xi = 0; xi < game->field.width - 1; xi++) {
            double y = yi * y_delta + offsetX;
            double x = xi * x_delta + (yi % 2) * (x_delta / 2) + offsetY;

            sprintf(msg, "%d,%d", (int)yi, (int)xi);
            Vector2 center = {x, y};
            DrawPoly(center, 6, s * 0.95, 30.0f, DARKBLUE);
            DrawText(msg, x - x_delta/4, y - y_delta/4, 10, DARKGRAY);
        }
    }
}

bool setup_display() {
    SetTraceLogLevel(LOG_ERROR);

    InitWindow(screenWidth, screenHeight, "slabes");
    SetTargetFPS(60);

    return true;
}

void update_display(Game *game) {
    state.elapsed_time += GetFrameTime();

    if (!WindowShouldClose()) {
        BeginDrawing();

        ClearBackground(BLACK);

        draw_hexagon_grid(game, s);

        EndDrawing();
    }
    
}

void cleanup_display() {
    while (!WindowShouldClose()) {
        state.elapsed_time += GetFrameTime();

        BeginDrawing();

        // ClearBackground(BLACK);

        // draw_hexagon_grid(game, s);

        EndDrawing();
    }
    CloseWindow();
}
