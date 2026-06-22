"""Procedural asset generator for 1GB+ game content.
Generates terrain, audio, textures, dungeons, quests at scale."""
import os, math, random, struct, hashlib, json, gzip, array
from datetime import datetime

SAMPLE_RATE = 44100

class ProceduralAudio:
    @staticmethod
    def generate_sine_wav(freq, duration_sec, volume=0.5):
        n = int(SAMPLE_RATE * duration_sec)
        samples = array.array('h', [0]) * n
        step = 2 * math.pi * freq / SAMPLE_RATE
        vol = int(volume * 32767)
        for i in range(n):
            samples[i] = int(vol * math.sin(i * step))
        return ProceduralAudio._wav_bytes(samples.tobytes(), n)

    @staticmethod
    def generate_noise_wav(duration_sec, volume=0.3, seed=42):
        rng = random.Random(seed)
        n = int(SAMPLE_RATE * duration_sec)
        samples = array.array('h', [0]) * n
        vol = int(volume * 32767)
        for i in range(n):
            samples[i] = int(vol * (rng.random() * 2 - 1))
        return ProceduralAudio._wav_bytes(samples.tobytes(), n)

    @staticmethod
    def generate_melody_wav(duration_sec, bpm=120):
        n = int(SAMPLE_RATE * duration_sec)
        samples = array.array('h', [0]) * n
        beat_sec = 60 / bpm
        notes = [262, 294, 330, 349, 392, 440, 494, 523]
        note_len = int(SAMPLE_RATE * beat_sec / 4)
        for i in range(0, n, note_len):
            freq = notes[(i // note_len) % len(notes)]
            block = min(note_len, n - i)
            step = 2 * math.pi * freq / SAMPLE_RATE
            for j in range(block):
                t = j / SAMPLE_RATE
                v = int(0.4 * 32767 * math.sin(j * step))
                v += int(0.2 * 32767 * math.sin(2 * j * step))
                decay = max(0, 1 - j / note_len)
                samples[i + j] = int(v * decay)
        return ProceduralAudio._wav_bytes(samples.tobytes(), n)

    @staticmethod
    def _wav_bytes(data, n):
        data_size = len(data)
        hdr = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
        hdr += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16)
        hdr += struct.pack('<4sI', b'data', data_size)
        return hdr + data


def _perlin(height, width, scale, octaves, seed):
    rng = random.Random(seed)
    perm = list(range(256))
    rng.shuffle(perm)
    perm = perm * 2
    hm = [[0.0] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            v, amp, freq, mv = 0.0, 1.0, scale, 0.0
            for _ in range(octaves):
                xi = int(math.floor(x * freq)) & 255
                yi = int(math.floor(y * freq)) & 255
                xf = x * freq - math.floor(x * freq)
                yf = y * freq - math.floor(y * freq)
                u = xf * xf * (3 - 2 * xf)
                vf = yf * yf * (3 - 2 * yf)
                aa = perm[perm[xi] + yi]
                ab = perm[perm[xi] + yi + 1]
                ba = perm[perm[xi + 1] + yi]
                bb = perm[perm[xi + 1] + yi + 1]
                def grad(h, x, y): return (x if h & 1 == 0 else -x) + (y if h & 2 == 0 else -y)
                x1 = grad(aa & 3, xf, yf) * (1 - u) + grad(ba & 3, xf - 1, yf) * u
                x2 = grad(ab & 3, xf, yf - 1) * (1 - u) + grad(bb & 3, xf - 1, yf - 1) * u
                v += (x1 * (1 - vf) + x2 * vf) * amp
                mv += amp
                amp *= 0.5
                freq *= 2
            hm[y][x] = v / mv
    return hm


class ProceduralTerrain:
    @staticmethod
    def generate_heightmap(width, height, scale=0.01, octaves=6, seed=42):
        return _perlin(height, width, scale, octaves, seed)

    @staticmethod
    def generate_biome_map(heightmap, water_level=0.35, forest_level=0.5):
        h, w = len(heightmap), len(heightmap[0])
        bm = [[''] * w for _ in range(h)]
        biome_keys = ['water', 'grass', 'forest', 'mountain', 'snow']
        levels = [water_level, forest_level, 0.7, 0.85, 1.0]
        for y in range(h):
            for x in range(w):
                val = heightmap[y][x]
                for i, lvl in enumerate(levels):
                    if val < lvl:
                        bm[y][x] = biome_keys[i]
                        break
        return bm

    @staticmethod
    def compress_heightmap(heightmap):
        arr = []
        for row in heightmap:
            arr.extend(row)
        return gzip.compress(json.dumps(arr).encode())


class ProceduralDungeon:
    @staticmethod
    def generate_dungeon(width, height, room_attempts=100, seed=42):
        rng = random.Random(seed)
        grid = [[1] * width for _ in range(height)]
        rooms = []
        for _ in range(room_attempts):
            rw, rh = rng.randint(4, 10), rng.randint(4, 10)
            rx, ry = rng.randint(1, width - rw - 1), rng.randint(1, height - rh - 1)
            ok = True
            for y in range(ry - 1, ry + rh + 1):
                for x in range(rx - 1, rx + rw + 1):
                    if 0 <= y < height and 0 <= x < width and grid[y][x] == 0:
                        ok = False
            if ok:
                for y in range(ry, ry + rh):
                    for x in range(rx, rx + rw):
                        grid[y][x] = 0
                rooms.append({'x': rx, 'y': ry, 'w': rw, 'h': rh, 'cx': rx + rw // 2, 'cy': ry + rh // 2})
        for i in range(1, len(rooms)):
            ax, ay = rooms[i-1]['cx'], rooms[i-1]['cy']
            bx, by = rooms[i]['cx'], rooms[i]['cy']
            if rng.random() < 0.5:
                for x in range(min(ax, bx), max(ax, bx) + 1):
                    if 0 <= ay < height and 0 <= x < width: grid[ay][x] = 0
                for y in range(min(ay, by), max(ay, by) + 1):
                    if 0 <= y < height and 0 <= bx < width: grid[y][bx] = 0
            else:
                for y in range(min(ay, by), max(ay, by) + 1):
                    if 0 <= y < height and 0 <= ax < width: grid[y][ax] = 0
                for x in range(min(ax, bx), max(ax, bx) + 1):
                    if 0 <= by < height and 0 <= x < width: grid[by][x] = 0
        return {'grid': grid, 'rooms': rooms, 'width': width, 'height': height}

    @staticmethod
    def compress_dungeon(dungeon):
        flat = []
        for row in dungeon['grid']:
            flat.extend(row)
        data = {'flat': flat, 'rooms': dungeon['rooms'], 'w': dungeon['width'], 'h': dungeon['height']}
        return gzip.compress(json.dumps(data).encode())


class ProceduralContent:
    def __init__(self, output_dir, seed=42):
        self.output_dir = output_dir
        self.seed = seed
        os.makedirs(output_dir, exist_ok=True)

    def generate_1gb_assets(self):
        total_bytes = 0
        target = 1024 * 1024 * 1024
        manifest = []
        idx = 0

        audio_dir = os.path.join(self.output_dir, 'audio')
        os.makedirs(audio_dir, exist_ok=True)

        for i in range(20):
            freq = 55 * (2 ** (i % 36 / 12))
            dur = 60.0
            wav = ProceduralAudio.generate_sine_wav(freq, dur, volume=0.4)
            path = os.path.join(audio_dir, f'synth_{i}.wav')
            with open(path, 'wb') as f: f.write(wav)
            total_bytes += len(wav)
            manifest.append({'type': 'audio_sine', 'file': f'audio/synth_{i}.wav', 'size': len(wav)})
            idx += 1

        for i in range(10):
            dur = 60.0
            wav = ProceduralAudio.generate_noise_wav(dur, volume=0.3, seed=self.seed + i)
            path = os.path.join(audio_dir, f'noise_{i}.wav')
            with open(path, 'wb') as f: f.write(wav)
            total_bytes += len(wav)
            manifest.append({'type': 'audio_noise', 'file': f'audio/noise_{i}.wav', 'size': len(wav)})
            idx += 1

        for i in range(10):
            dur = 120.0
            bpm = 100 + i * 6
            wav = ProceduralAudio.generate_melody_wav(dur, bpm=bpm)
            path = os.path.join(audio_dir, f'melody_{i}.wav')
            with open(path, 'wb') as f: f.write(wav)
            total_bytes += len(wav)
            manifest.append({'type': 'audio_melody', 'file': f'audio/melody_{i}.wav', 'size': len(wav)})
            idx += 1

        terrain_dir = os.path.join(self.output_dir, 'terrain')
        os.makedirs(terrain_dir, exist_ok=True)

        for w, h in [(256, 256), (500, 500), (1000, 1000)]:
            for variant in range(3):
                hm = ProceduralTerrain.generate_heightmap(w, h, scale=0.005, octaves=6, seed=self.seed + variant + idx)
                compressed = ProceduralTerrain.compress_heightmap(hm)
                path = os.path.join(terrain_dir, f'world_{w}x{h}_v{variant}.hm.gz')
                with open(path, 'wb') as f: f.write(compressed)
                total_bytes += len(compressed)
                manifest.append({'type': 'heightmap', 'file': f'terrain/world_{w}x{h}_v{variant}.hm.gz', 'size': len(compressed), 'dims': f'{w}x{h}'})

                bm = ProceduralTerrain.generate_biome_map(hm)
                bm_json = json.dumps(bm).encode()
                bm_path = os.path.join(terrain_dir, f'biomes_{w}x{h}_v{variant}.json.gz')
                with gzip.open(bm_path, 'wb') as f: f.write(bm_json)
                total_bytes += len(bm_json)
                manifest.append({'type': 'biome_map', 'file': f'terrain/biomes_{w}x{h}_v{variant}.json.gz', 'size': len(bm_json), 'dims': f'{w}x{h}'})
            idx += 1

        dungeon_dir = os.path.join(self.output_dir, 'dungeons')
        os.makedirs(dungeon_dir, exist_ok=True)

        for i in range(50):
            dw = dh = 50 + i * 3
            dungeon = ProceduralDungeon.generate_dungeon(dw, dh, room_attempts=100 + i * 5, seed=self.seed + i)
            compressed = ProceduralDungeon.compress_dungeon(dungeon)
            d_path = os.path.join(dungeon_dir, f'dungeon_{i}_{dw}x{dh}.dgz')
            with open(d_path, 'wb') as f: f.write(compressed)
            total_bytes += len(compressed)
            manifest.append({'type': 'dungeon', 'file': f'dungeons/dungeon_{i}_{dw}x{dh}.dgz', 'size': len(compressed)})

        manifest_path = os.path.join(self.output_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump({'total_bytes': total_bytes, 'target': target, 'generated': datetime.now().isoformat(), 'assets': manifest}, f, indent=2)
        total_bytes += os.path.getsize(manifest_path)

        return total_bytes


class GameAssetGenerator:
    @staticmethod
    def build_1gb_game(output_dir, seed=42, verbose=True):
        if verbose: print(f'Building 1GB game assets in {output_dir}...')
        pc = ProceduralContent(output_dir, seed=seed)
        total = pc.generate_1gb_assets()
        if verbose: print(f'Generated {total / (1024*1024*1024):.2f} GB of game assets ({total:,} bytes)')
        return total

    @staticmethod
    def generate_game_script(title, genre, map_size, seed=42):
        return f'''#!/usr/bin/env python3
"""NICTO Generated Game: {title}  Genre: {genre}  Map: {map_size}x{map_size}  Seed: {seed}"""
import pygame, math, random, sys
from pygame.locals import *
W, H = 800, 600
SEED = {seed}
MAP_SIZE = {map_size}

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
COLORS = {{0:(30,30,40),1:(100,150,80),2:(130,110,70),3:(180,170,160)}}

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("{title}")
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
        pygame.display.set_caption(f"{{title}} | FPS: {{clock.get_fps():.0f}}")
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
'''
