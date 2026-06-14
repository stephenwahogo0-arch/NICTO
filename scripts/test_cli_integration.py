"""Test CLI integration with enhanced game engine."""

import sys
import os
sys.path.insert(0, 'packages/nikto-core/src')
sys.path.insert(0, 'packages/nicto-game/src')

import asyncio
from nikto.brain.core import NiktoBrain

async def test_brain_integration():
    print("=== Testing Brain Integration ===")
    
    # Test 1: Create brain and check game engine status
    brain = NiktoBrain()
    status = brain.get_game_status()
    print(f"✓ Brain initialized with game engine status: {status.get('games_built', 0)} games built")
    
    # Test 2: Build a game from prompt
    result = await brain.build_game_from_prompt("FPS shooter with enemies")
    print(f"✓ Game built: {result['name']} ({result['genre']})")
    print(f"  - World size: {result['world_size']}")
    print(f"  - Lines of code: {result['lines_of_code']}")
    print(f"  - Test score: {result.get('test_score', 'N/A')}")
    
    # Test 3: List games
    games = await brain.list_generated_games()
    print(f"✓ Listed {len(games)} games")
    
    # Test 4: Get specific game
    if games:
        game = await brain.get_game_by_name(games[0]['name'])
        print(f"✓ Retrieved game: {game['name']}")
    
    # Test 5: Create game with parameters
    result2 = await brain.create_game("TestGame", "fps", 32, 32, 5)
    print(f"✓ Created game with parameters: {result2['name']}")
    
    # Test 6: Delete game
    if games:
        deleted = await brain.delete_game(games[0]['name'])
        print(f"✓ Deleted game: {deleted}")
    
    print("\n=== All Brain Integration Tests Passed ===")
    return True

async def main():
    try:
        await test_brain_integration()
        return 0
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
