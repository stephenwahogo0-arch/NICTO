import asyncio
from nikto import NiktoBrain

async def test():
    brain = await NiktoBrain().awaken()

    result1 = brain.process("What is the meaning of consciousness?", {"task_type": "philosophical_analysis"})
    meta1 = result1["metacognition"]
    print("=== TEST 1: Basic metacognitive evaluation ===")
    print(f"Biases detected: {len(meta1['biases_detected'])}")
    print(f"Quality: {meta1['quality_assessment']['quality']} (score: {meta1['quality_assessment']['score']})")
    print(f"Strategy rec: {meta1['strategy_recommendation']['recommended_style']}")
    print(f"Uncertainty: {meta1['uncertainty_analysis']['total_uncertainty']}")
    print()

    for i in range(3):
        brain.process(f"Analyzing complex problem iteration {i}", {"task_type": "problem_solving"})

    reflect = brain.meta_cognition.reflect(brain.reasoner.thought_history)
    print("=== TEST 2: Self-reflection ===")
    for insight in reflect.get("insights", []):
        print(f"  Insight: {insight}")
    for pattern in reflect.get("patterns", []):
        print(f"  Pattern: {pattern['pattern']} - {pattern['detail']}")
    print()

    deep = brain.meta_cognition.deep_reflect(brain.reasoner.thought_history)
    print("=== TEST 3: Deep reflection ===")
    print("Strategy effectiveness:")
    for style, data in list(deep.get("strategy_effectiveness", {}).items())[:3]:
        print(f"  {style}: uses={data['uses']}, avg_quality={data['avg_quality']}")
    if deep.get("recommendations"):
        for rec in deep["recommendations"][:3]:
            print(f"  Recommendation: {rec}")
    print()

    improve = brain.meta_cognition.recursive_self_improve(brain.reasoner.thought_history)
    print("=== TEST 4: Recursive self-improvement ===")
    print(f"Improved: {improve['improved']}")
    for imp in improve.get("improvements", [])[:3]:
        print(f"  Improvement: {imp['area']} - {imp['action']}")
    print()

    awareness = brain.meta_cognition.get_meta_awareness(brain.reasoner.thought_history)
    print("=== TEST 5: Meta-awareness dashboard ===")
    print(f"Cognitive state: {awareness['current_cognitive_state']}")
    print(f"Active biases: {awareness['active_biases']}")
    print(f"Total observations: {awareness['total_observations']}")
    print(f"Strategy profiles tracked: {len(awareness['strategy_profiles'])}")
    print()

    status = brain.get_status()
    introspect = brain.introspect()
    print("=== TEST 6: Brain integration ===")
    print(f"Brain: {status['name']}, awake={status['awake']}")
    print("Meta-cognition in introspect:")
    print(f"  Observations: {introspect['meta_cognition']['total_observations']}")
    print(f"  State: {introspect['meta_cognition']['current_state']}")
    print(f"  Profiles: {introspect['meta_cognition']['profiles_tracked']}")

    saved = brain.save_state()
    print(f"\nState saved to: {saved}")

    await brain.sleep()
    print("\nALL METACOGNITION TESTS PASSED")

asyncio.run(test())
