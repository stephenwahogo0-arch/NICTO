#!/usr/bin/env python3
"""NICTO Generated Game: NICTO_Survival  Genre: survival  Map: 200x200  Seed: 42"""
import pygame, math, random, sys
from pygame.locals import *
W, H = 800, 600
SEED = 42
MAP_SIZE = 200

def generate_world():
    rng = random.Random(SEED)
    perm = list(range(512)); rng.shuffle(perm)
    def noise(x, y):
        xi, yi = int(math.floor(x)) & 255, int(math.floor(y)) & 255
        xf, yf = x - math.floor(x), y - math.floor(y)
        u = xf*xf*xf*(xf*(xf*6-15)+10)
        v = yf*yf*yf*(yf*(yf*6-15)+10)
        def grad(h, x, y): return (x if h&1==0 else -x) + (y if h&2==0 else -y)
        aa = perm[perm[xi]+yi]; ab = perm[perm[xi]+yi+1]
        ba = perm[perm[xi+1]+yi]; bb = perm[perm[xi+1]+yi+1]
        x1 = grad(aa, xf, yf)*(1-u) + grad(ba, xf-1, yf)*u
        x2 = grad(ab, xf, yf-1)*(1-u) + grad(bb, xf-1, yf-1)*u
        return x1*(1-v) + x2*v
    return [[0 if noise(x*0.01, y*0.01)*0.5+0.5 < 0.3 else
             (1 if noise(x*0.01, y*0.01)*0.5+0.5 < 0.5 else
             (2 if noise(x*0.01, y*0.01)*0.5+0.5 < 0.7 else 3))
             for x in range(MAP_SIZE)] for y in range(MAP_SIZE)]

WORLD = generate_world()
COLORS = {0:(30,30,40),1:(100,150,80),2:(130,110,70),3:(180,170,160)}

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("NICTO_Survival")
    clock = pygame.time.Clock()
    px, py, pa = MAP_SIZE//2, MAP_SIZE//2, 0.0
    running = True
    while running:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE): running = False
        keys = pygame.key.get_pressed()
        pa += (keys[K_RIGHT]-keys[K_LEFT]) * 0.03
        dx = (keys[K_UP] or keys[K_w]) - (keys[K_DOWN] or keys[K_s])
        nx = px + math.cos(pa) * 0.05 * dx
        ny = py + math.sin(pa) * 0.05 * dx
        if 0 <= int(ny) < MAP_SIZE and 0 <= int(nx) < MAP_SIZE and WORLD[int(ny)][int(nx)] == 0:
            px, py = nx, ny
        screen.fill((10,10,20))
        mm = min(W, H) // 3
        scale = mm / MAP_SIZE
        ox, oy = W - mm - 10, 10
        for my in range(MAP_SIZE):
            for mx in range(MAP_SIZE):
                c = WORLD[my][mx]
                if c: pygame.draw.rect(screen, COLORS[c], (ox+mx*scale, oy+my*scale, scale+1, scale+1))
        pygame.draw.circle(screen, (255,50,50), (int(ox+px*scale), int(oy+py*scale)), 4)
        pygame.display.set_caption(f"{title} | FPS: {clock.get_fps():.0f}")
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
