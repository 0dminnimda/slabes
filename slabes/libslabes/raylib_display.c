#include "slabes.h"
#include "raylib.h"
#include "raymath.h"
#include <math.h>
#include <stdio.h>

#if RAYLIB_VERSION_MAJOR >= 5
const double hex_start_ange = 0.0;
#else
const double hex_start_ange = 30.0;
#endif

const Color empty_color = DARKBLUE;
const Color wall_color = GRAY;
const Color cell_wall_color = GRAY;
const Color player_color = WHITE;
const Color player_direction_color = GREEN;

int screen_width = 800;
int screen_height = 450;
double hex_side = 20;

Color cell_color(Cell cell) {
    switch (cell) {
        case Player: return player_color;
        case Wall: return wall_color;
        default: return empty_color;
    }
}

double direction_to_angle(Direction direction) {
    switch (direction) {
        case UpLeft: return 5.0*PI / 6.0;
        case Up: return PI / 2.0;
        case UpRight: return PI / 6.0;
        case DownRight: return -PI / 6.0;
        case Down: return -PI / 2.0;
        case DownLeft: return -5.0*PI / 6.0;
        default: return direction;
    }
}

Vector2 direction_to_vector2(Direction direction, double radius) {
    double angle = direction_to_angle(direction);
    return (Vector2){radius * cos(angle), -radius * sin(angle)};
}

void draw_player_direction(Game *game, double hex_side, Vector2 center) {
    const double arrow_ratio = 0.4;
    Vector2 direction = direction_to_vector2(game->player_direction, sqrt(3) / 2 * hex_side);
    Vector2 shifted_center = Vector2Add(center, (Vector2){direction.x * 0.1, direction.y * 0.1});
    direction = (Vector2){direction.x * 0.8, direction.y * 0.8};
    Vector2 perp1 = { direction.y * arrow_ratio, -direction.x * arrow_ratio};
    Vector2 perp2 = {-direction.y * arrow_ratio,  direction.x * arrow_ratio};
    DrawTriangle(
        Vector2Add(shifted_center, perp1),
        Vector2Add(shifted_center, perp2),
        Vector2Add(shifted_center, direction),
        player_direction_color
    );
}

static Vector2 hexagon_points[6];

void calculate_hexagon_points() {
    double angles[6] = {-2.0*PI / 3.0, -PI / 3.0, 0, PI / 3.0, 2.0*PI / 3.0, PI};
    for (size_t i = 0; i < 6; i++) {
        hexagon_points[i] = (Vector2){
            hex_side * cos(angles[i]),
            -hex_side * sin(angles[i])
        };
    }
}

void draw_cell_walls(Walls walls, double hex_side, Vector2 center) {
    Vector2 prev = Vector2Add(center, hexagon_points[5]);
    for (size_t i = 0; i < 6; i++) {
        Vector2 cur = Vector2Add(center, hexagon_points[i]);
        if (walls & (1 << i)) {
            DrawLineEx(prev, cur, hex_side / 10.0, cell_wall_color);
        }
        prev = cur;
    }
}

void draw_hexagon_grid(Game *game, double hex_side) {
    double x_delta = 3 * hex_side;  // distance between hexagons in the same row
    double y_delta = sqrt(3) / 2 * hex_side;  // distance between rows
    double total_y = (game->field.height - 1) * y_delta;
    double offset_x = 2*hex_side;
    double offset_y = 2*hex_side;

    for (ssize_t yi = 0; yi < game->field.height; yi++) {
        for (ssize_t xi = 0; xi < game->field.width; xi++) {
            double y = total_y - (yi * y_delta);
            double x = xi * x_delta + (yi % 2) * (x_delta / 2);
            Vector2 center = {x + offset_x, y + offset_y};

            Cell cell = FIELD_AT(&game->field, xi, yi);
            if (cell == Player) {
                DrawPoly(center, 6, hex_side, hex_start_ange, player_color);
                draw_player_direction(game, hex_side, center);
            }
            Walls walls = field_walls_check_at(&game->field, xi, yi);
            walls = game_walls_with_map_end(game, walls, xi, yi);
            draw_cell_walls(walls, hex_side, center);
        }
    }
}

void recalculate_sizes(Game *game) {
    screen_width = GetScreenWidth();
    screen_height = GetScreenHeight();

    double hex_height = (double)game->field.height / 2.0;
    hex_height = (double)screen_height / hex_height;
    double hex_width = (double)game->field.width / 2.0 * 3.0 + 1.25;
    hex_width = (double)screen_width / hex_width;

    hex_side = fmin(hex_height, hex_width) / 2.0;

    calculate_hexagon_points();
}

bool setup_display(Game *game) {
    SetTraceLogLevel(LOG_ERROR);

    SetConfigFlags(FLAG_WINDOW_RESIZABLE | FLAG_VSYNC_HINT);
    InitWindow(screen_width, screen_height, "slabes");
    SetTargetFPS(60);

    recalculate_sizes(game);

    return true;
}

void update_display(Game *game) {
    if (!WindowShouldClose()) {
        if (IsWindowResized()) {
            recalculate_sizes(game);
        }
        
        BeginDrawing();

        ClearBackground(BLACK);

        draw_hexagon_grid(game, hex_side);

        EndDrawing();
    }
    
}

void cleanup_display(Game *game) {
    while (!WindowShouldClose()) {
        BeginDrawing();

        // ClearBackground(BLACK);

        // draw_hexagon_grid(game, hex_side);

        EndDrawing();
    }
    CloseWindow();
}
