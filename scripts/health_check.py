import sys, os, json
sys.path.insert(0, 'packages/nikto-core/src')
sys.path.insert(0, 'packages/nicto-x/src')
sys.path.insert(0, 'packages/nicto-game/src')

results = {}

# Light imports first
try:
    from nicto_game.core.director import GameDirector
    results['game_director'] = 'OK'
except Exception as e:
    results['game_director'] = 'FAIL: %s' % e

try:
    from nicto_x.agents.coding_agent import CodingAgent
    from nicto_x.agents.research_agent import ResearchAgent
    from nicto_x.agents.planning_agent import PlanningAgent
    results['nicto_x_agents'] = 'OK'
except Exception as e:
    results['nicto_x_agents'] = 'FAIL: %s' % e

try:
    from nicto_x import NictoXOrchestrator
    results['nicto_x_orchestrator'] = 'OK'
except Exception as e:
    results['nicto_x_orchestrator'] = 'FAIL: %s' % e

try:
    from nikto.brain import NiktoBrain
    results['nikto_brain'] = 'OK'
except Exception as e:
    results['nikto_brain'] = 'FAIL: %s' % e

try:
    from nikto.plugins import PluginEngine
    results['plugin_engine'] = 'OK'
except Exception as e:
    results['plugin_engine'] = 'FAIL: %s' % e

try:
    from nicto_neural import NeuralCore
    results['neural_core'] = 'OK'
except Exception as e:
    results['neural_core'] = 'FAIL: %s' % e

try:
    from nicto_neural import NictoMaster, NictoGameBuilder
    results['real_ai_modules'] = 'OK'
except Exception as e:
    results['real_ai_modules'] = 'FAIL: %s' % e

try:
    from nikto.autopilot import AutopilotEngine
    results['autopilot'] = 'OK'
except Exception as e:
    results['autopilot'] = 'FAIL: %s' % e

try:
    from nikto.orchestrator import OrchestratorEngine
    results['orchestrator'] = 'OK'
except Exception as e:
    results['orchestrator'] = 'FAIL: %s' % e

try:
    from nikto.security.scanner import SecurityScanner
    results['security_scanner'] = 'OK'
except Exception as e:
    results['security_scanner'] = 'FAIL: %s' % e

try:
    from nikto.dream.steerer import NiktoDreamSteerer
    results['dream_steerer'] = 'OK'
except Exception as e:
    results['dream_steerer'] = 'FAIL: %s' % e

try:
    from nikto.swarm.engine import NiktoSwarmEngine
    results['swarm_engine'] = 'OK'
except Exception as e:
    results['swarm_engine'] = 'FAIL: %s' % e

try:
    from nikto.metrics.performance_graph import NiktoPerformanceGraph
    results['performance_graph'] = 'OK'
except Exception as e:
    results['performance_graph'] = 'FAIL: %s' % e

td_path = 'nicto_neural/training_data/nicto_chatml.jsonl'
if os.path.exists(td_path):
    count = sum(1 for _ in open(td_path))
    results['training_data'] = 'OK (%d conversations)' % count
else:
    results['training_data'] = 'FAIL: not found'

print('=== NIKTO SYSTEM HEALTH CHECK ===')
for name, status in sorted(results.items()):
    icon = 'OK' if str(status).startswith('OK') else 'FAIL'
    print('  [%s] %s: %s' % (icon, name, status))
ok_count = sum(1 for s in results.values() if str(s).startswith('OK'))
print()
print('%d/%d modules healthy' % (ok_count, len(results)))
