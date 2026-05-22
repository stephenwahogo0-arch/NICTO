"""Generate NIKTO game engine screenshot SVGs."""
import os

os.makedirs("screenshots", exist_ok=True)

screenshots = {
    "platformer": "Side-scrolling platformer with coins, enemies, platforms, parallax",
    "rpg": "Top-down RPG with tile world, combat, inventory, leveling system",
    "fps": "Raycasting FPS with textured walls, enemies, health bar, ammo",
    "racing": "Pseudo-3D road racer with curves, speed bar, lap counting",
    "puzzle": "Match-3 puzzle game with combos, chain reactions, level progression",
    "strategy": "Tower defense with enemy waves, upgradable towers, path system",
    "fighting": "2D fighter with combos, blocking, special moves, health bars",
    "simulation": "Life sim with characters, needs, jobs, buildings, happiness",
    "shooter": "Space shooter with enemy waves, power-ups, boss fights, stars",
    "stealth": "Stealth game with guards, vision cones, shadows, objectives",
    "physics": "Rigid body dynamics, soft body cloth, joints, destruction",
    "vfx": "Particle system: fire, smoke, explosion, spark, magic, rain",
    "animation": "Skeleton rigging, IK solving, walk cycles, animation blending",
    "ai_behavior": "Behavior trees, state machines, utility AI, A* pathfinding",
    "audio": "3D audio engine, Doppler effect, DSP reverb, synth tones",
}

for name, desc in screenshots.items():
    svg = (
        '<svg width="640" height="480" xmlns="http://www.w3.org/2000/svg">\n'
        '<rect width="640" height="480" fill="#111118"/>\n'
        '<text x="320" y="50" text-anchor="middle" fill="#00aaff" font-size="24" font-family="monospace" font-weight="bold">NIKTO</text>\n'
        '<text x="320" y="80" text-anchor="middle" fill="#ffffff" font-size="14" font-family="monospace">Game Engine Screenshot</text>\n'
        '<rect x="40" y="100" width="560" height="300" rx="12" fill="#1a1a28" stroke="#00aaff" stroke-width="1"/>\n'
        '<text x="320" y="160" text-anchor="middle" fill="#00ffcc" font-size="18" font-family="monospace" font-weight="bold">'
        + name + '</text>\n'
        '<text x="320" y="260" text-anchor="middle" fill="#aaaaaa" font-size="13" font-family="monospace">'
        + desc + '</text>\n'
        '<text x="320" y="430" text-anchor="middle" fill="#555" font-size="11" font-family="monospace">'
        'NIKTO Game Engine  |  pygame-ce  |  ECS Architecture</text>\n'
        '</svg>'
    )
    fp = "screenshots/game_" + name + ".svg"
    with open(fp, "w") as f:
        f.write(svg)
    print("Created:", fp)

print("\nGenerated", len(screenshots), "screenshots")
