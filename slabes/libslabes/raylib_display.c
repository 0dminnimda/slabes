#include "slabes.h"
#include "raylib.h"
#include <math.h>

typedef struct {
} State;

State state;

const int screenWidth = 800;
const int screenHeight = 450;

const double s = 30;  // Side length of the hexagon
const int num_rows = 8;  // Number of rows
const int num_cols = 12;  // Number of columns
const int offsetX = 50;  // Horizontal offset to center the grid
const int offsetY = 50;  // Vertical offset to center the grid


void draw_hexagon_grid(double s, int num_rows, int num_cols, int offsetX, int offsetY) {
    double height = 1.5 * s;  // Vertical distance between rows
    double width = sqrt(3) * s;  // Horizontal distance between hexagon centers in a row

    for (int row = 0; row < num_rows; row++) {
        for (int col = 0; col < num_cols; col++) {
            double x = col * width + (row % 2) * (width / 2) + offsetX;
            double y = row * height + offsetY;
            
            Vector2 center = {x, y};
            DrawPoly(center, 6, s, 0.0f, DARKBLUE);  // Draw a hexagon
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
    if (!WindowShouldClose()) {
        BeginDrawing();

        draw_hexagon_grid(s, num_rows, num_cols, offsetX, offsetY);

        EndDrawing();
    }
    
}

void cleanup_display() {
    CloseWindow();
}
