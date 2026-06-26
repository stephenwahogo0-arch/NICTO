#!/usr/bin/env python3
"""Test NICTO Master Self-Improvement Pipeline (targeted)."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["NIKTO_ENABLE_EXPERIMENTAL"] = "1"


async def test():
    from nicto_neural import MasterPipeline, Domain

    print("=" * 60, flush=True)
    print("  MASTER PIPELINE TEST - 2 Domains", flush=True)
    print("=" * 60, flush=True)

    pipeline = MasterPipeline()

    try:
        # Phase 1: just 2 domains, 1 query each
        print("\n--- Phase 1: Web Knowledge Acquisition ---", flush=True)
        await pipeline.ensure_trainer()
        await pipeline.ensure_api()

        domains = [Domain.CODING, Domain.AI_ML]
        total = {"sources": 0, "facts": 0, "memories": 0, "lessons": 0, "truths": 0}

        for domain in domains:
            queries = ["Python programming best practices"]
            for query in queries:
                print(f"  Learning: {query}", flush=True)
                from nicto_neural.intira_browser import IntiraTrainer
                trainer = pipeline._trainer
                result = await trainer.search_and_learn(
                    topic=query, count=2, engine="duckduckgo",
                    mode="full", extract_content=False,
                )
                total["sources"] += result.sources_used
                total["facts"] += result.facts_added
                total["memories"] += result.memories_stored
                total["lessons"] += result.lessons_learned
                total["truths"] += result.truths_registered
                print(f"    -> {result.sources_used} sources, "
                      f"{result.facts_added} facts, "
                      f"{result.memories_stored} mems", flush=True)

        pipeline._result.total_sources = total["sources"]
        pipeline._result.total_facts = total["facts"]
        pipeline._result.total_memories = total["memories"]
        pipeline._result.total_lessons = total["lessons"]
        pipeline._result.total_truths = total["truths"]
        pipeline._result.phases_completed.append("web_knowledge_acquisition")

        # Phase 3: Configure 550B
        print("\n--- Phase 3: 550B Configuration ---", flush=True)
        from nicto_neural.neural.super_config import ULTRA_CONFIG
        config = ULTRA_CONFIG
        params_dict = config.estimate_params()
        total_params = params_dict.get("total", 0)
        total_b = params_dict.get("total_billions", 0)
        pipeline._result.model_params = total_params
        print(f"  ULTRA: d_model={config.d_model}, n_layers={config.n_layers}, "
              f"n_experts={config.n_experts}", flush=True)
        print(f"  Total params: {total_params:,} ({total_b:.1f}B)", flush=True)
        print(f"  Active per token: ~{total_b / config.n_experts * config.n_active_experts:.1f}B", flush=True)
        pipeline._result.phases_completed.append("configure_550b_model")

        # Phase 5: Self-evaluation
        print("\n--- Phase 5: Self-Evaluation ---", flush=True)
        brain = pipeline._brain
        if brain:
            if brain.knowledge:
                print(f"  KnowledgeCore: {len(brain.knowledge.facts)} facts", flush=True)
            if brain.memory:
                print(f"  LongTermMemory: {len(brain.memory.fragments)} fragments", flush=True)
            if brain.learner:
                print(f"  Learner: {len(brain.learner.lesson_store)} lessons", flush=True)
                for topic_key in list(brain.learner.skill_progress.keys())[-4:]:
                    info = brain.learner.skill_progress[topic_key]
                    print(f"    {topic_key[:35]:35s} "
                          f"score={info.get('score', 0):.2f}", flush=True)
        pipeline._result.phases_completed.append("self_evaluation")

        # Summary
        print("\n" + "=" * 60, flush=True)
        print("  RESULTS", flush=True)
        print("=" * 60, flush=True)
        print(f"  Duration:              {pipeline._result.duration_seconds:.1f}s", flush=True)
        print(f"  Sources:               {pipeline._result.total_sources}", flush=True)
        print(f"  Facts:                 {pipeline._result.total_facts}", flush=True)
        print(f"  Memories:              {pipeline._result.total_memories}", flush=True)
        print(f"  Lessons:               {pipeline._result.total_lessons}", flush=True)
        print(f"  Truths:                {pipeline._result.total_truths}", flush=True)
        print(f"  Model Params:          {pipeline._result.model_params:,}", flush=True)
        print(f"  Phases:                {pipeline._result.phases_completed}", flush=True)
        print()

    finally:
        await pipeline.close()
        print("Done.", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
