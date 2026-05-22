import sys
import asyncio
import time

sys.path.insert(0, 'packages\nikto-core\src')

async def test_basic():
    print('Testing basic NIKTO functionality...')
    
    # Test 1: Agent creation and import
    from nikto.agent.base import Agent, AgentConfig
    from nikto.config.settings import NiktoConfig
    print('[OK] Agent imports work')
    
    # Test 2: Brain engine
    from nikto.brain.engine import BrainEngine
    brain = BrainEngine()
    result = brain.think('What is 2+2?', {})
    print('[OK] Brain works: {}'.format(type(result)))
    
    # Test 3: Surpass engine (real benchmarking)
    from nikto.surpass.engine import SurpassEngine
    surpass = SurpassEngine()
    surpass.benchmark_category('reasoning', 0.85)
    scores = surpass.get_scores()
    print('[OK] Surpass works: {}'.format(scores))
    
    # Test 4: Knowledge engine
    from nikto.knowledge.engine import KnowledgeEngine
    knowledge = KnowledgeEngine()
    knowledge.add_fact('test', 'This is a real fact')
    facts = knowledge.query('test')  # Fixed: use query() instead of get_facts()
    print('[OK] Knowledge works: {} facts'.format(len(facts)))
    
    # Test 5: Reasoning engine
    from nikto.reasoning.engine import ReasoningEngine
    reasoning = ReasoningEngine()
    result = reasoning.reason('What is AI?', 'deductive', 2)
    print('[OK] Reasoning works: {} steps'.format(len(result["steps"])))
    
    # Test 6: Vector engine (real search)
    from nikto.vector_engine import VectorEngine
    vec = VectorEngine(dim=16)
    vec.add_document('doc1', [0.1]*16, {'text': 'hello world'})
    results = vec.search([0.1]*16, 1)
    print('[OK] Vector engine works: {} results'.format(len(results)))
    
    # Test 7: Fast response system
    from nikto.fast_response import FastResponseSystem
    fast = FastResponseSystem()
    # No initialize needed - just use it
    response = await fast.respond('test query', lambda q: 'Response to {}'.format(q))
    print('[OK] Fast response works: {}...'.format(response[:50]))
    
    print('')
    print('All basic tests passed! NIKTO core is operational.')

if __name__ == '__main__':
    asyncio.run(test_basic())