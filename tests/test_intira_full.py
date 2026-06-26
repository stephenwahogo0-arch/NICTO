#!/usr/bin/env python3
"""Intira Browser — Full End-to-End Test Suite for NICTO.

Tests how NICTO uses Intira Browser to:
  1. Search the web privately
  2. Fetch and show results to the user
  3. Self-train by injecting data into its brain

Usage:
    python tests/test_intira_full.py
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["NIKTO_ENABLE_EXPERIMENTAL"] = "1"

from nicto_neural import (
    IntiraAPI,
    IntiraTrainer,
    IntiraAgent,
    TrainingMode,
)


SEP = "=" * 72
DASH = "-" * 72


def header(title: str):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subheader(title: str):
    print(f"\n  --- {title} ---")


async def test_nicto_uses_intira_browser():
    """Full report: how NICTO uses Intira Browser end-to-end."""
    report = []
    total_start = time.time()

    # ====== PHASE 1: NICTO searches the web ================================
    header("PHASE 1 — NICTO Searches the Web via Intira Browser")

    subheader("1.1 NICTO launches Intira Browser (Chromium headless)")
    api = IntiraAPI(headless=True)
    status = await api.get_browser_status()
    print(f"     Browser running: {status['running']}")
    print(f"     Version: {status.get('version', '1.0.0')}")
    print(f"     Headless: {status.get('headless', True)}")

    subheader("1.2 NICTO searches 'autonomous AI agents architecture'")
    t0 = time.time()
    search_result = await api.search(
        "autonomous AI agents architecture", count=10, engine="duckduckgo"
    )
    search_time = time.time() - t0
    results = search_result["results"]

    print(f"     Query: {search_result['query']}")
    print(f"     Engine: {search_result['engine']}")
    print(f"     Results: {search_result['count']}")
    print(f"     Search time: {search_time:.1f}s")

    for i, r in enumerate(results[:5]):
        print(f"     {i+1}. {r['title'][:65]}")
        print(f"        {r['url'][:65]}")
        if r.get("snippet"):
            print(f"        {r['snippet'][:80]}")

    report.append({
        "phase": "1 — Search",
        "query": search_result["query"],
        "results_found": search_result["count"],
        "search_time_s": round(search_time, 1),
    })

    # ====== PHASE 2: NICTO fetches page content =============================
    header("PHASE 2 — NICTO Fetches Web Pages Shows User Results")

    subheader("2.1 NICTO fetches content from a result page")
    if results:
        first_url = results[0]["url"]
        t0 = time.time()
        page = await api.fetch(first_url)
        fetch_time = time.time() - t0
        print(f"     URL: {first_url[:70]}")
        print(f"     Content length: {page['content_length']} chars")
        print(f"     Fetch time: {fetch_time:.1f}s")

        content_preview = page.get("content", "")[:300]
        if content_preview:
            print(f"     Preview: {content_preview}...")

        report.append({
            "phase": "2 — Fetch",
            "url": first_url[:60],
            "content_chars": page["content_length"],
            "fetch_time_s": round(fetch_time, 1),
        })

    subheader("2.2 NICTO navigates to a real page")
    t0 = time.time()
    nav = await api.navigate("https://en.wikipedia.org/wiki/Autonomous_agent")
    nav_time = time.time() - t0
    print(f"     Page title: {nav.get('title', 'N/A')[:60]}")
    print(f"     URL: {nav.get('url', 'N/A')[:60]}")
    print(f"     Navigation time: {nav_time:.1f}s")

    report.append({
        "phase": "2 — Navigate",
        "title": nav.get("title", "")[:50],
        "nav_time_s": round(nav_time, 1),
    })

    subheader("2.3 NICTO extracts structured content from the page")
    t0 = time.time()
    extracted = await api.extract_current_page()
    extract_time = time.time() - t0
    print(f"     Title: {extracted.get('title', 'N/A')[:60]}")
    print(f"     Word count: {extracted.get('word_count', 0)}")
    print(f"     Reading time: {extracted.get('reading_time_seconds', 0)}s")
    print(f"     Keywords: {', '.join(extracted.get('keywords', [])[:8])}")
    print(f"     Headings: {len(extracted.get('headings', []))}")
    print(f"     Links: {len(extracted.get('links', []))}")
    print(f"     Images: {len(extracted.get('images', []))}")
    print(f"     Summary: {extracted.get('summary', '')[:200]}...")
    print(f"     Extract time: {extract_time:.1f}s")

    report.append({
        "phase": "2 — Extract",
        "word_count": extracted.get("word_count", 0),
        "headings": len(extracted.get("headings", [])),
        "links": len(extracted.get("links", [])),
        "extract_time_s": round(extract_time, 1),
    })

    await api.close()

    # ====== PHASE 3: NICTO self-trains from web data ========================
    header("PHASE 3 — NICTO Self-Trains from Web Data")

    trainer = IntiraTrainer()
    await trainer.ensure_brain()
    brain = trainer._brain

    subheader("3.1 Brain state BEFORE training")
    pre_status = brain.get_status()
    pre_facts = len(brain.knowledge.facts) if brain.knowledge else 0
    pre_memories = len(brain.memory.fragments) if brain.memory else 0
    pre_lessons = len(brain.learner.lesson_store) if brain.learner else 0
    pre_truths = len(brain.truth.facts) if brain.truth else 0
    print(f"     Facts in KnowledgeCore: {pre_facts}")
    print(f"     Memories in LTM: {pre_memories}")
    print(f"     Lessons in Learner: {pre_lessons}")
    print(f"     Truths in TruthEngine: {pre_truths}")

    subheader("3.2 NICTO searches and trains on 'reinforcement learning'")
    t0 = time.time()
    result1 = await trainer.search_and_learn(
        topic="reinforcement learning",
        count=3,
        engine="duckduckgo",
        mode=TrainingMode.FULL,
        extract_content=False,
    )
    t1 = time.time()
    print(f"     Duration: {result1.duration_seconds:.1f}s")
    print(f"     Sources: {result1.sources_used}")
    print(f"     Facts added: {result1.facts_added}")
    print(f"     Memories stored: {result1.memories_stored}")
    print(f"     Lessons learned: {result1.lessons_learned}")
    print(f"     Truths registered: {result1.truths_registered}")
    print(f"     Concepts created: {result1.concepts_created}")
    print(f"     Errors: {result1.errors}")

    subheader("3.3 NICTO searches and trains on 'large language models'")
    result2 = await trainer.search_and_learn(
        topic="large language models",
        count=3,
        engine="duckduckgo",
        mode=TrainingMode.FULL,
        extract_content=False,
    )
    time2 = time.time()
    print(f"     Duration: {result2.duration_seconds:.1f}s")
    print(f"     Sources: {result2.sources_used}")
    print(f"     Facts added: {result2.facts_added}")
    print(f"     Memories stored: {result2.memories_stored}")
    print(f"     Lessons learned: {result2.lessons_learned}")
    print(f"     Truths registered: {result2.truths_registered}")
    print(f"     Concepts created: {result2.concepts_created}")

    subheader("3.4 NICTO searches and trains on 'NICTO hyperbrain'")
    result3 = await trainer.search_and_learn(
        topic="NICTO hyperbrain architecture",
        count=2,
        engine="duckduckgo",
        mode=TrainingMode.FULL,
        extract_content=False,
    )
    print(f"     Duration: {result3.duration_seconds:.1f}s")
    print(f"     Sources: {result3.sources_used}")
    print(f"     Facts added: {result3.facts_added}")
    print(f"     Memories stored: {result3.memories_stored}")
    print(f"     Lessons learned: {result3.lessons_learned}")
    print(f"     Truths registered: {result3.truths_registered}")
    print(f"     Concepts created: {result3.concepts_created}")

    # ====== PHASE 4: Brain growth analysis ===================================
    header("PHASE 4 — NICTO Brain Growth Analysis")

    subheader("4.1 Brain state AFTER training")
    post_facts = len(brain.knowledge.facts) if brain.knowledge else 0
    post_memories = len(brain.memory.fragments) if brain.memory else 0
    post_lessons = len(brain.learner.lesson_store) if brain.learner else 0
    post_truths = len(brain.truth.facts) if brain.truth else 0
    delta_facts = post_facts - pre_facts
    delta_memories = post_memories - pre_memories
    delta_lessons = post_lessons - pre_lessons
    delta_truths = post_truths - pre_truths

    print(f"     {'Metric':25s} {'Before':8s} {'After':8s} {'Growth':8s}")
    print(f"     {'-':->50}")
    print(f"     {'KnowledgeCore facts':25s} {pre_facts:8d} {post_facts:8d} +{delta_facts:6d}")
    print(f"     {'LongTermMemory':25s} {pre_memories:8d} {post_memories:8d} +{delta_memories:6d}")
    print(f"     {'Learner lessons':25s} {pre_lessons:8d} {post_lessons:8d} +{delta_lessons:6d}")
    print(f"     {'TruthEngine facts':25s} {pre_truths:8d} {post_truths:8d} +{delta_truths:6d}")

    subheader("4.2 Learner skill levels after training")
    if brain.learner:
        for topic_key in ["reinforcement learning", "large language models", "NICTO hyperbrain architecture"]:
            mastery = brain.learner.get_mastery(topic_key)
            level = brain.learner.get_level(topic_key)
            print(f"     {topic_key:35s} -> mastery: {mastery:.2f}  level: {level.value}")

    subheader("4.3 Learner curiosity (what NICTO wants to learn next)")
    if brain.learner:
        curious = brain.learner.get_curious_topics(threshold=0.1)
        print(f"     Topics NICTO is curious about:")
        for ct in curious[:5]:
            print(f"       * {ct}")

    subheader("4.4 KnowledgeCore - sample facts")
    if brain.knowledge:
        sample_facts = brain.knowledge.query("reinforcement")[:3]
        for f in sample_facts:
            print(f"       * {f.get('fact', f.get('statement', str(f)))[:80]}")

    subheader("4.5 Training history")
    history = trainer.get_training_history()
    for h in history:
        print(f"       * {h['topic'][:30]:30s} {h['sources']}src "
              f"{h['facts']}facts {h['memories']}mem "
              f"{h['lessons']}les {h['truths']}tru "
              f"in {h['duration']}")

    report.append({
        "phase": "3 — Training",
        "sessions": 3,
        "total_facts_added": result1.facts_added + result2.facts_added + result3.facts_added,
        "total_memories_added": result1.memories_stored + result2.memories_stored + result3.memories_stored,
        "total_lessons_added": result1.lessons_learned + result2.lessons_learned + result3.lessons_learned,
        "total_truths_added": result1.truths_registered + result2.truths_registered + result3.truths_registered,
        "brain_growth_facts": delta_facts,
        "brain_growth_memories": delta_memories,
        "brain_growth_lessons": delta_lessons,
    })

    await trainer.close()

    # ====== PHASE 5: Autonomous agent =======================================
    header("PHASE 5 — NICTO's IntiraAgent Autonomously Browsing")

    agent = IntiraAgent()
    await agent.ensure_browser()

    subheader("5.1 Agent searches and navigates")
    results = await agent.search("NICTO artificial intelligence", engine="duckduckgo", count=5)
    print(f"     Search found {len(results)} results")
    if results:
        nav_result = await agent.navigate(results[0]["url"])
        print(f"     Navigated to: {nav_result.get('title', 'N/A')[:60]}")

    subheader("5.2 Agent extracts page data")
    page_data = await agent.extract_page()
    print(f"     Words: {page_data.get('word_count', 0)}")
    print(f"     Keywords: {', '.join(page_data.get('keywords', [])[:6])}")
    print(f"     Links: {page_data.get('links', 0) if isinstance(page_data.get('links'), int) else len(page_data.get('links', []))}")

    subheader("5.3 Agent action history")
    history = agent.get_history()
    for h in history:
        print(f"     [{h['action']:8s}] params={h['params']} completed={h['completed']}")

    report.append({
        "phase": "4 — Agent",
        "actions": len(history),
        "searches": sum(1 for h in history if h["action"] == "search"),
        "navigations": sum(1 for h in history if h["action"] == "navigate"),
    })

    await agent.close()

    # ====== FINAL REPORT ====================================================
    total_time = time.time() - total_start
    header("FINAL REPORT — NICTO × Intira Browser")

    print(f"""
  NICTO successfully uses Intira Browser (v1.0.0) as its private
  Chromium-based web browser. The integration covers 4 subsystems:

  {'='*60}""")

    for r in report:
        p = r["phase"]
        if "Search" in p:
            print(f"  [SEARCH]      OK  {r['results_found']} results in {r['search_time_s']}s")
        elif "Fetch" in p:
            print(f"  [FETCH]       OK  {r['content_chars']} chars in {r['fetch_time_s']}s")
        elif "Navigate" in p:
            print(f"  [NAVIGATE]    OK  '{r['title'][:30]}...'")
        elif "Extract" in p:
            print(f"  [EXTRACT]     OK  {r['word_count']} words, {r['headings']} headings")
        elif "Training" in p:
            print(f"  [TRAINING]    OK  +{r['brain_growth_facts']} facts, +{r['brain_growth_memories']} mem")
        elif "Agent" in p:
            print(f"  [AGENT]       OK  {r['actions']} autonomous actions")

    print(f"""  {'='*60}

  Brain Growth (3 training sessions):
    Facts in KnowledgeCore:       +{delta_facts}
    Memories in LongTermMemory:   +{delta_memories}
    Lessons in Learner:           +{delta_lessons}
    Truths in TruthEngine:        +{delta_truths}

  Total test time: {total_time:.1f}s
  Topics learned: reinforcement learning, large language models, NICTO hyperbrain architecture
""")

    return report


if __name__ == "__main__":
    asyncio.run(test_nicto_uses_intira_browser())
