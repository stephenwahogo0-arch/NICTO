#!/usr/bin/env python3
"""NICTO Generated Game: test_game  fps"""
import pygame, math, sys
from pygame.locals import *

WIDTH, HEIGHT = 800, 600
FOV = math.pi / 3
HALF_FOV = FOV / 2
HALF_HEIGHT = HEIGHT // 2
PLAYER_SPEED = 0.05
ROT_SPEED = 0.03
MAP_W, MAP_H = 12, 12
COLORS = {"1": [180, 60, 60], "2": [60, 120, 200], "3": [60, 180, 60], "4": [200, 180, 60], "5": [160, 60, 180], "6": [60, 180, 180]}
MAP = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
        [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
        [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]

def cast_ray(x, y, angle, max_dist=16.0):
    sin_a, cos_a = math.sin(angle), math.cos(angle)
    dist = 0.0
    while dist < max_dist:
        dist += 0.02
        mx, my = int(x + cos_a * dist), int(y + sin_a * dist)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            return max_dist, None
        cell = MAP[my][mx]
        if cell > 0:
            # Find exact wall side for texturing
            px, py = x + cos_a * dist, y + sin_a * dist
            wall_x = px - mx if (py - my) < 0.5 else 1.0 - (px - mx)
            return dist, (cell, wall_x)
    return max_dist, None

def draw_frame(screen, px, py, angle):
    screen.fill((20, 20, 30))
    # Floor and ceiling
    screen.fill((10, 10, 20), (0, 0, WIDTH, HALF_HEIGHT))
    screen.fill((30, 30, 40), (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

    for col in range(WIDTH):
        ray_angle = angle - HALF_FOV + (col / WIDTH) * FOV
        dist, hit = cast_ray(px, py, ray_angle)
        if dist > 15.9:
            continue

        # Fix fisheye
        dist *= math.cos(ray_angle - angle)
        wall_h = min(HALF_HEIGHT / (dist + 0.001), HEIGHT)
        top = HALF_HEIGHT - wall_h // 2
        bot = HALF_HEIGHT + wall_h // 2

        # Shade by distance
        shade = max(30, min(255, int(255 - dist * 14)))
        if hit:
            cell_id, wx = hit
            color = COLORS.get(str(cell_id), (shade, shade, shade))
            shaded = tuple(max(0, min(255, int(c * shade / 255))) for c in color)
            pygame.draw.rect(screen, shaded, (col, int(top), 1, int(bot - top)))

    # Minimap
    mm_scale = 4
    ox, oy = WIDTH - MAP_W * mm_scale - 10, 10
    for my, row in enumerate(MAP):
        for mx, cell in enumerate(row):
            if cell > 0:
                ci = COLORS.get(str(cell), (100, 100, 100))
                pygame.draw.rect(screen, ci, (ox + mx * mm_scale, oy + my * mm_scale, mm_scale, mm_scale))
    # Player on minimap
    mx, my = int(px * mm_scale) + ox, int(py * mm_scale) + oy
    pygame.draw.circle(screen, (255, 50, 50), (mx, my), 3)
    # Direction
    dx, dy = math.cos(angle) * 8, math.sin(angle) * 8
    pygame.draw.line(screen, (255, 255, 50), (mx, my), (mx + dx, my + dy), 2)

    # Crosshair
    cx, cy = WIDTH // 2, HEIGHT // 2
    pygame.draw.line(screen, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 2)
    pygame.draw.line(screen, (255, 255, 255), (cx, cy - 10), (cx, cy + 10), 2)

    # Info
    font = pygame.font.Font(None, 24)
    fps_t = font.render(f"FPS: {clock.get_fps():.0f} | WASD move, Arrow turn", True, (180, 255, 180))
    screen.blit(fps_t, (10, HEIGHT - 30))

def main():
    global clock
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NICTO Game: test_game")
    clock = pygame.time.Clock()

    px, py = 3.50, 1.50
    angle = 0.0

    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            angle -= ROT_SPEED
        if keys[K_RIGHT]:
            angle += ROT_SPEED
        if keys[K_UP] or keys[K_w]:
            nx = px + math.cos(angle) * PLAYER_SPEED
            ny = py + math.sin(angle) * PLAYER_SPEED
            if 0 <= int(ny) < MAP_H and 0 <= int(nx) < MAP_W and MAP[int(ny)][int(nx)] == 0:
                px, py = nx, ny
        if keys[K_DOWN] or keys[K_s]:
            nx = px - math.cos(angle) * PLAYER_SPEED
            ny = py - math.sin(angle) * PLAYER_SPEED
            if 0 <= int(ny) < MAP_H and 0 <= int(nx) < MAP_W and MAP[int(ny)][int(nx)] == 0:
                px, py = nx, ny

        draw_frame(screen, px, py, angle)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
