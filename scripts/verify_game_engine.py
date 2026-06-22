"""End-to-end verification of the NICTO Omega Game Engine."""

import sys, os, asyncio, traceback

sys.path.insert(0, 'packages/nicto-game/src')
sys.path.insert(0, 'packages/nikto-core/src')

passed = 0
failed = 0

async def test(name, fn):
    global passed, failed
    try:
        await fn()
        print(f'  [PASS] {name}')
        passed += 1
    except Exception as e:
        print(f'  [FAIL] {name}: {e}')
        traceback.print_exc()
        failed += 1

async def main():
    global passed, failed

    from nicto_game import (
        GameDirector, GameConfig, GameGenre, GamePlatform,
        WorldConfig, GraphicsConfig, GameplayConfig,
        StoryConfig, AudioConfig, OptimizationConfig,
        TileType, Biome,
        WorldGenerator, BiomeGenerator,
        CharacterGenerator, StoryEngine, CodeEngine,
        AudioEngine, TestingEngine, OptimizationEngine,
        ExportEngine,
        AgentCoordinator, PlannerAgent, ArchitectAgent, QAAgent,
    )
    from nicto_game.core.types import GameMap

    print('=== NICTO OMEGA GAME ENGINE — VERIFICATION ===')
    print()

    # 1. Config creation
    async def test_config():
        cfg = GameConfig(name="TestGame", genre=GameGenre.FPS,
                        world=WorldConfig(width=16, height=16, enemies=5))
        assert cfg.name == "TestGame"
        assert cfg.genre == GameGenre.FPS
        assert cfg.world.width == 16
        assert cfg.world.enemies == 5
    await test("Config creation", test_config)

    # 2. World generation - all 4 genres
    async def test_world_fps():
        wg = WorldGenerator()
        cfg = GameConfig(name="FPS_Test", genre=GameGenre.FPS,
                        world=WorldConfig(width=16, height=16, enemies=5))
        gm = await wg.generate(cfg)
        assert isinstance(gm, GameMap)
        assert gm.width == 16
        assert gm.height == 16
        assert len(gm.tiles) == 16
        assert "player" in gm.spawn_points
    await test("World gen - FPS", test_world_fps)

    async def test_world_maze():
        wg = WorldGenerator()
        cfg = GameConfig(name="Maze", genre=GameGenre.MAZE,
                        world=WorldConfig(width=16, height=16))
        gm = await wg.generate(cfg)
        assert gm.width == 16
    await test("World gen - Maze", test_world_maze)

    async def test_world_dungeon():
        wg = WorldGenerator()
        cfg = GameConfig(name="Dungeon", genre=GameGenre.DUNGEON,
                        world=WorldConfig(width=24, height=24))
        gm = await wg.generate(cfg)
        assert gm.width == 24
    await test("World gen - Dungeon", test_world_dungeon)

    async def test_world_open():
        wg = WorldGenerator()
        cfg = GameConfig(name="OpenWorld", genre=GameGenre.OPEN_WORLD,
                        world=WorldConfig(width=32, height=32, rivers=True, biomes=True))
        gm = await wg.generate(cfg)
        assert gm.width == 32
    await test("World gen - Open World", test_world_open)

    async def test_world_survival():
        wg = WorldGenerator()
        cfg = GameConfig(name="Survival", genre=GameGenre.SURVIVAL,
                        world=WorldConfig(width=32, height=32, enemies=10, npcs=3))
        gm = await wg.generate(cfg)
        assert len(gm.spawn_points) >= 4
    await test("World gen - Survival", test_world_survival)

    # 3. Biome generation
    async def test_biomes():
        import random
        bg = BiomeGenerator(random.Random(42))
        hm = bg.generate_heightmap(16, 16)
        assert len(hm) == 16
        assert len(hm[0]) == 16
        bm = bg.classify_biomes(hm, bg.generate_moisture_map(16, 16))
        assert len(bm) == 16
        assert isinstance(bm[0][0], Biome)
    await test("Biome generation", test_biomes)

    # 4. Character generation
    async def test_characters():
        cg = CharacterGenerator()
        cfg = GameConfig(name="Test", genre=GameGenre.RPG,
                        world=WorldConfig(npcs=4, seed=42))
        chars = await cg.generate(cfg, num_npcs=4)
        assert len(chars) == 4
        for c in chars:
            assert c.name
            assert c.role
            assert c.faction
            assert c.behavior
    await test("Character generation", test_characters)

    # 5. Story engine
    async def test_story():
        se = StoryEngine()
        cfg = GameConfig(name="TestRPG", genre=GameGenre.RPG,
                        story=StoryConfig(generate_quests=True, generate_lore=True, num_quests=3))
        story = await se.generate(cfg)
        assert "lore" in story
        assert "quests" in story
        assert len(story["lore"]) >= 2
        assert len(story["quests"]) >= 1
    await test("Story generation", test_story)

    # 6. Code generation
    async def test_code():
        ce = CodeEngine()
        cfg = GameConfig(name="CodeTest", genre=GameGenre.FPS,
                        world=WorldConfig(width=8, height=8))
        wg = WorldGenerator()
        gm = await wg.generate(cfg)
        code = await ce.generate(cfg, gm)
        assert len(code) > 500
        assert "class Game" in code
        assert "pygame" in code
        assert "def run" in code or "def render" in code
        compile(code, 'test_game.py', 'exec')
    await test("Code generation", test_code)

    # 7. Audio generation
    async def test_audio():
        import tempfile
        ae = AudioEngine()
        cfg = GameConfig(name="AudioTest", genre=GameGenre.RPG,
                        assets=type('obj', (object,), {'generate_audio': True, 'texture_size': 256})(),
                        audio=AudioConfig(generate_music=True, generate_sfx=True))
        with tempfile.TemporaryDirectory() as tmp:
            assets = await ae.generate(cfg, tmp)
            assert len(assets) >= 3
            for name, path in assets.items():
                assert os.path.exists(path)
                assert os.path.getsize(path) > 100
    await test("Audio generation", test_audio)

    # 8. Testing engine
    async def test_testing():
        te = TestingEngine()
        cfg = GameConfig(name="Test", genre=GameGenre.FPS)
        sample_code = '''
import pygame
class Game:
    def run(self):
        while True:
            pass
if __name__ == "__main__":
    Game().run()
'''
        result = await te.validate_game(sample_code, cfg)
        assert "syntax_valid" in result
        assert "score" in result
    await test("Testing engine", test_testing)

    # 9. Optimization
    async def test_optimization():
        oe = OptimizationEngine()
        cfg = GameConfig(name="Test", genre=GameGenre.FPS)
        result = await oe.analyze("import pygame\nclass Game:\n    def run(self): pass", cfg)
        assert "quality" in result
        assert "estimated_fps" in result
    await test("Optimization engine", test_optimization)

    # 10. Agents
    async def test_agents():
        coordinator = AgentCoordinator()
        coordinator.register(PlannerAgent())
        coordinator.register(ArchitectAgent())
        coordinator.register(QAAgent())
        assert coordinator.get("planner") is not None
        assert coordinator.get("architect") is not None
        assert coordinator.get("qa") is not None
    await test("Agent system", test_agents)

    # 11. Export
    async def test_export():
        ee = ExportEngine()
        platforms = ee.get_available_platforms()
        assert "windows" in platforms
        assert "linux" in platforms
        assert "android" in platforms
        assert "web" in platforms
    await test("Export system", test_export)

    # 12. Full pipeline
    async def test_pipeline():
        gd = GameDirector()
        cfg = GameConfig(name="PipeTest", genre=GameGenre.FPS,
                        world=WorldConfig(width=12, height=12, enemies=3, npcs=1),
                        story=StoryConfig(generate_quests=True, num_quests=2))
        result = await gd.build_game(cfg)
        assert "name" in result
        assert "world_size" in result
        assert "lines_of_code" in result
        assert result["lines_of_code"] > 100
    await test("Full pipeline build", test_pipeline)

    # 13. Build from prompt
    async def test_prompt():
        gd = GameDirector()
        result = await gd.build_from_prompt("FPS shooter with many enemies")
        assert "name" in result
        assert "world_size" in result
        assert "lines_of_code" in result
    await test("Build from prompt", test_prompt)

    # 14. Status reporting
    async def test_status():
        gd = GameDirector()
        status = gd.get_status()
        assert "games_built" in status
        assert "agents_registered" in status
        assert len(status["agents_registered"]) == 3
    await test("Status reporting", test_status)

    print()
    print(f'{passed}/{passed + failed} tests passed')
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
