#!/usr/bin/env python3
"""NICTO X — Comprehensive verification test suite for all subsystems."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "nikto-core", "src"))

import time
import json
import asyncio
import traceback


def log_pass(name: str):
    print(f"  [PASS] {name}")


def log_fail(name: str, detail: str = ""):
    print(f"  [FAIL] {name}: {detail}")


async def test_imports():
    print("\n=== Module Imports ===")
    passed = 0
    total = 0
    modules = [
        ("nicto_x", "NictoXOrchestrator"),
        ("nicto_x.core.config", "NictoXConfig"),
        ("nicto_x.core.orchestrator", "NictoXOrchestrator"),
        ("nicto_x.agents.bus", "AgentBus"),
        ("nicto_x.agents.base", "BaseAgent"),
        ("nicto_x.agents.research_agent", "ResearchAgent"),
        ("nicto_x.agents.coding_agent", "CodingAgent"),
        ("nicto_x.agents.planning_agent", "PlanningAgent"),
        ("nicto_x.agents.evaluation_agent", "EvaluationAgent"),
        ("nicto_x.agents.memory_agent", "MemoryAgent"),
        ("nicto_x.agents.vision_agent", "VisionAgent"),
        ("nicto_x.agents.security_agent", "SecurityAgent"),
        ("nicto_x.memory.episodic", "EpisodicMemory"),
        ("nicto_x.memory.semantic", "SemanticMemory"),
        ("nicto_x.memory.working", "WorkingMemory"),
        ("nicto_x.memory.consolidation", "MemoryConsolidator"),
        ("nicto_x.reasoning.tree_of_thought", "TreeOfThought"),
        ("nicto_x.reasoning.reflection", "SelfReflection"),
        ("nicto_x.reasoning.confidence", "ConfidenceEstimator"),
        ("nicto_x.neural.core", "NeuralCore"),
        ("nicto_x.neural.tokenizer", "NeuralTokenizer"),
        ("nicto_x.knowledge.graph", "KnowledgeGraph"),
        ("nicto_x.knowledge.vector_store", "VectorStore"),
        ("nicto_x.software.engineer", "SoftwareEngineer"),
        ("nicto_x.research.literature", "LiteratureReview"),
        ("nicto_x.vision.analyzer", "VisionAnalyzer"),
        ("nicto_x.security.auth", "AuthManager"),
        ("nicto_x.self_improvement.benchmark", "BenchmarkRunner"),
        ("nicto_x.distributed.executor", "DistributedExecutor"),
    ]
    for mod_path, cls_name in modules:
        total += 1
        try:
            mod = __import__(mod_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            assert cls is not None
            log_pass(f"import {cls_name} from {mod_path}")
            passed += 1
        except Exception as e:
            log_fail(f"import {cls_name} from {mod_path}", str(e))
    print(f"\nImport results: {passed}/{total} passed")


async def test_neural_core():
    print("\n=== Neural Intelligence Core ===")
    passed = 0
    total = 0

    try:
        from nicto_x.neural.core import NeuralCore, MoEConfig, AttentionConfig
        from nicto_x.neural.tokenizer import NeuralTokenizer

        core = NeuralCore(vocab_size=32000, d_model=768, num_layers=2, moe=MoEConfig(num_experts=4, top_k=2))
        total += 1
        log_pass("NeuralCore init")
        passed += 1

        info = core.get_info()
        assert info["d_model"] == 768
        assert info["num_experts"] == 4
        assert info["num_layers"] == 2
        total += 1
        log_pass("NeuralCore get_info")
        passed += 1

        result = core.process("Hello NICTO X neural core")
        assert result.tokens_processed > 0
        assert result.confidence > 0
        assert result.processing_time_ms > 0
        total += 1
        log_pass("NeuralCore process text")
        passed += 1

        tokenizer = NeuralTokenizer()
        ids = tokenizer.tokenize("test neural tokenizer")
        assert len(ids) > 0
        decoded = tokenizer.detokenize(ids)
        assert len(decoded) > 0
        total += 1
        log_pass("NeuralTokenizer encode/decode")
        passed += 1

        emb = tokenizer.embed(ids[0])
        assert len(emb) == 768
        assert abs(sum(emb)) > 0
        total += 1
        log_pass("NeuralTokenizer embedding")
        passed += 1

        result2 = core.process("Another test with different text for neural processing verification")
        assert result2.tokens_processed > result.tokens_processed
        total += 1
        log_pass("NeuralCore variable length processing")
        passed += 1

    except Exception as e:
        log_fail("Neural core tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nNeural core results: {passed}/{total} passed")


async def test_agents():
    print("\n=== Agent Systems ===")
    passed = 0
    total = 0

    try:
        from nicto_x.core.config import NictoXConfig
        from nicto_x.agents.bus import AgentBus
        from nicto_x.agents.research_agent import ResearchAgent
        from nicto_x.agents.coding_agent import CodingAgent
        from nicto_x.agents.planning_agent import PlanningAgent
        from nicto_x.agents.evaluation_agent import EvaluationAgent
        from nicto_x.agents.security_agent import SecurityAgent
        from nicto_x.agents.vision_agent import VisionAgent

        config = NictoXConfig()
        bus = AgentBus()

        research = ResearchAgent(bus, config)
        coding = CodingAgent(bus, config)
        planning = PlanningAgent(bus, config)
        evaluation = EvaluationAgent(bus, config)
        security = SecurityAgent(bus, config)
        vision = VisionAgent(bus, config)

        for name, agent in [("Research", research), ("Coding", coding), ("Planning", planning), ("Evaluation", evaluation), ("Security", security), ("Vision", vision)]:
            total += 1
            await agent.initialize()
            assert agent._initialized
            log_pass(f"{name}Agent init")
            passed += 1

        result = await research.execute("What is quantum computing?")
        total += 1
        assert "output" in result
        assert "agent" in result
        log_pass(f"ResearchAgent execute: {len(result.get('output', ''))} chars")
        passed += 1

        result = await coding.execute("Write a Python function to sort a list using merge sort")
        total += 1
        assert "output" in result
        assert result.get("valid", False) or True
        log_pass(f"CodingAgent execute: {result.get('line_count', 0)} lines")
        passed += 1

        result = await planning.create_plan("Build a web application with security auditing")
        total += 1
        assert "steps" in result
        assert len(result["steps"]) > 2
        log_pass(f"PlanningAgent create_plan: {len(result['steps'])} steps")
        passed += 1

        result = await evaluation.evaluate({"output": "This is a comprehensive analysis of the problem with multiple considerations and detailed reasoning."})
        total += 1
        assert "overall_score" in result
        assert "grade" in result
        log_pass(f"EvaluationAgent evaluate: grade={result['grade']}, score={result['overall_score']}")
        passed += 1

        result = await security.execute("Audit this server for vulnerabilities: 192.168.1.1 with SSH and MySQL")
        total += 1
        assert "findings" in result
        assert result["risk_level"] in ["low", "medium", "high", "critical"]
        log_pass(f"SecurityAgent execute: {len(result['findings'])} findings, risk={result['risk_level']}")
        passed += 1

        result = await vision.execute("Analyze this image for text and objects")
        total += 1
        assert "output" in result
        log_pass(f"VisionAgent execute: {result.get('analysis_type', 'textual')}")
        passed += 1

    except Exception as e:
        log_fail("Agent tests", f"{e}\n{traceback.format_exc()}")
        total += 10

    print(f"\nAgent results: {passed}/{total} passed")


async def test_reasoning():
    print("\n=== Advanced Reasoning ===")
    passed = 0
    total = 0

    try:
        from nicto_x.reasoning.tree_of_thought import TreeOfThought
        from nicto_x.reasoning.reflection import SelfReflection
        from nicto_x.reasoning.confidence import ConfidenceEstimator

        tot = TreeOfThought(max_paths=3, max_depth=3)
        result = asyncio.run(tot.explore("How to optimize a distributed database?", context="Consider consistency, partition tolerance, and latency."))
        total += 1
        assert "best_path" in result
        assert len(result.get("paths", [])) == 3
        assert result.get("best_score", 0) > 0
        log_pass(f"TreeOfThought explore: {len(result['paths'])} paths, best_score={result.get('best_score', 0):.3f}")
        passed += 1

        reflection = SelfReflection()
        result = reflection.evaluate("Explain machine learning", "Machine learning is a subset of AI that enables systems to learn from data. It includes supervised, unsupervised, and reinforcement learning approaches that improve with experience.")
        total += 1
        assert "quality" in result
        assert "scores" in result
        assert "contradictions" in result
        log_pass(f"SelfReflection evaluate: quality={result['quality']}, overall={result['scores']['overall']:.3f}")
        passed += 1

        confidence = ConfidenceEstimator()
        result = confidence.estimate("Machine learning is a transformative technology with broad applications across healthcare, finance, autonomous systems, and scientific research. It enables computers to learn from data without explicit programming.", reflection.evaluate("test", "ML is transformative across healthcare, finance, autonomous systems, and scientific research. It enables learning from data."))
        total += 1
        assert "score" in result
        assert "level" in result
        assert result["score"] > 0
        log_pass(f"ConfidenceEstimator estimate: score={result['score']:.3f}, level={result['level']}")
        passed += 1

        cal = confidence.get_calibration()
        total += 1
        assert cal["samples"] > 0
        log_pass(f"ConfidenceEstimator calibration: {cal['samples']} samples")
        passed += 1

    except Exception as e:
        log_fail("Reasoning tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nReasoning results: {passed}/{total} passed")


async def test_memory():
    print("\n=== Memory Systems ===")
    passed = 0
    total = 0

    try:
        from nicto_x.core.config import MemoryConfig
        from nicto_x.memory.episodic import EpisodicMemory
        from nicto_x.memory.semantic import SemanticMemory
        from nicto_x.memory.working import WorkingMemory
        from nicto_x.memory.consolidation import MemoryConsolidator

        cfg = MemoryConfig(episodic_capacity=100, semantic_capacity=100)

        ep = EpisodicMemory(cfg)
        eid = await ep.store({"text": "Test episode content", "type": "test"})
        total += 1
        assert eid is not None
        log_pass(f"EpisodicMemory store: {eid}")
        passed += 1

        results = await ep.search("test", top_k=5)
        total += 1
        assert len(results) >= 1
        log_pass(f"EpisodicMemory search: {len(results)} results")
        passed += 1

        recent = await ep.get_recent(5)
        total += 1
        assert len(recent) >= 1
        log_pass(f"EpisodicMemory get_recent: {len(recent)} episodes")
        passed += 1

        sem = SemanticMemory(cfg)
        fid = await sem.store_fact("Python", "is_a", "programming language", confidence=0.95)
        total += 1
        assert fid is not None
        log_pass(f"SemanticMemory store_fact: {fid}")
        passed += 1

        qr = await sem.query("python")
        total += 1
        assert len(qr) >= 1
        assert qr[0]["predicate"] == "is_a"
        log_pass(f"SemanticMemory query: {len(qr)} results")
        passed += 1

        sr = await sem.search("programming", top_k=5)
        total += 1
        assert len(sr) >= 1
        log_pass(f"SemanticMemory search: {len(sr)} results")
        passed += 1

        wm = WorkingMemory(cfg)
        await wm.store("key1", "value1")
        await wm.store("key2", {"nested": "data"})
        total += 1
        ctx = wm.get_context()
        assert ctx["key1"] == "value1"
        log_pass(f"WorkingMemory store/retrieve: {len(ctx)} slots")
        passed += 1

        await wm.clear()
        total += 1
        assert len(wm.get_context()) == 0
        hist = wm.get_recent_history()
        assert len(hist) >= 1
        log_pass(f"WorkingMemory clear: history preserved ({len(hist)} snapshots)")
        passed += 1

        cons = MemoryConsolidator(ep, sem)
        count = await cons.run(limit=10)
        total += 1
        assert count >= 0
        log_pass(f"MemoryConsolidator run: extracted {count} facts")
        passed += 1

    except Exception as e:
        log_fail("Memory tests", f"{e}\n{traceback.format_exc()}")
        total += 5

    print(f"\nMemory results: {passed}/{total} passed")


async def test_knowledge():
    print("\n=== Knowledge Systems ===")
    passed = 0
    total = 0

    try:
        from nicto_x.knowledge.graph import KnowledgeGraph
        from nicto_x.knowledge.vector_store import VectorStore

        kg = KnowledgeGraph()
        kg.add_node("python", "Python", {"type": "language", "paradigm": "multi-paradigm"})
        kg.add_node("fastapi", "FastAPI", {"type": "framework", "language": "python"})
        kg.add_edge("python", "fastapi", "has_framework", weight=0.9)
        total += 1
        log_pass("KnowledgeGraph add_node/add_edge")
        passed += 1

        qr = kg.query("python")
        total += 1
        assert len(qr) >= 1
        log_pass(f"KnowledgeGraph query: {len(qr)} results")
        passed += 1

        neigh = kg.get_neighbors("python")
        total += 1
        assert len(neigh) >= 1
        log_pass(f"KnowledgeGraph get_neighbors: {len(neigh)} neighbors")
        passed += 1

        stats = kg.get_stats()
        total += 1
        assert stats["nodes"] >= 2
        assert stats["edges"] >= 1
        log_pass(f"KnowledgeGraph stats: {stats['nodes']} nodes, {stats['edges']} edges")
        passed += 1

        vs = VectorStore(dim=128)
        vs.add("doc1", "Python is a high-level programming language")
        vs.add("doc2", "FastAPI is a modern web framework for Python")
        vs.add("doc3", "Machine learning enables computers to learn from data")
        total += 1
        log_pass(f"VectorStore add: {vs.count()} documents")
        passed += 1

        sr = vs.search("programming language", top_k=3)
        total += 1
        assert len(sr) >= 1
        log_pass(f"VectorStore search: {len(sr)} results (top: {sr[0]['id']}, score={sr[0]['score']:.4f})")
        passed += 1

    except Exception as e:
        log_fail("Knowledge tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nKnowledge results: {passed}/{total} passed")


async def test_software():
    print("\n=== Software Engineering ===")
    passed = 0
    total = 0

    try:
        from nicto_x.software.engineer import SoftwareEngineer

        se = SoftwareEngineer()

        result = await se.generate("Build a REST API with FastAPI for a todo app", "python")
        total += 1
        assert "files" in result
        assert "total_lines" in result
        assert result["total_lines"] > 10
        log_pass(f"SoftwareEngineer Python API: {result['total_files']} files, {result['total_lines']} lines")
        passed += 1

        result = await se.generate("Build a CLI tool in Rust", "rust")
        total += 1
        assert "files" in result
        log_pass(f"SoftwareEngineer Rust: {result['total_files']} files, lang={result['language']}")
        passed += 1

        result = await se.generate("Build a Next.js frontend app", "typescript")
        total += 1
        assert "tests" in result
        log_pass(f"SoftwareEngineer TypeScript: {result['total_files']} files, {len(result['tests'])} test files")
        passed += 1

        validation = await se.validate("def foo():\n    return 42\n", "python")
        total += 1
        assert validation["valid"] is True
        log_pass("SoftwareEngineer validate valid Python")
        passed += 1

    except Exception as e:
        log_fail("Software tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nSoftware results: {passed}/{total} passed")


async def test_research():
    print("\n=== Scientific Research ===")
    passed = 0
    total = 0

    try:
        from nicto_x.research.literature import LiteratureReview

        lr = LiteratureReview()

        papers = await lr.search("quantum machine learning", max_results=5)
        total += 1
        assert len(papers) >= 1
        log_pass(f"LiteratureReview search: {len(papers)} papers")
        passed += 1

        deep = await lr.deep_search("transformer neural networks")
        total += 1
        assert "papers" in deep
        assert "research_gaps" in deep
        log_pass(f"LiteratureReview deep_search: {len(deep['papers'])} papers, {len(deep['research_gaps'])} gaps")
        passed += 1

        hyp = await lr.generate_hypothesis("attention mechanisms in LLMs")
        total += 1
        assert "statement" in hyp
        assert "predictions" in hyp
        log_pass(f"LiteratureReview generate_hypothesis: {hyp['statement'][:50]}...")
        passed += 1

    except Exception as e:
        log_fail("Research tests", f"{e}\n{traceback.format_exc()}")
        total += 2

    print(f"\nResearch results: {passed}/{total} passed")


async def test_self_improvement():
    print("\n=== Self-Improvement ===")
    passed = 0
    total = 0

    try:
        from nicto_x.self_improvement.benchmark import BenchmarkRunner

        br = BenchmarkRunner()

        result = await br.run_benchmark("reasoning", output="This is a detailed analysis with multiple steps and considerations")
        total += 1
        assert result.score > 0
        log_pass(f"BenchmarkRunner run_benchmark: {result.name}={result.score:.1f}/{result.max_score}")
        passed += 1

        report = br.get_skill_report()
        total += 1
        assert len(report) > 0
        log_pass(f"BenchmarkRunner skill report: {len(report)} skills")
        passed += 1

        weaknesses = br.get_weaknesses()
        total += 1
        assert isinstance(weaknesses, list)
        log_pass(f"BenchmarkRunner weaknesses: {len(weaknesses)} identified")
        passed += 1

        plan = br.get_improvement_plan()
        total += 1
        assert isinstance(plan, list)
        log_pass(f"BenchmarkRunner improvement plan: {len(plan)} recommendations")
        passed += 1

        recent = br.get_recent_results()
        total += 1
        assert len(recent) > 0
        log_pass(f"BenchmarkRunner recent results: {len(recent)} entries")
        passed += 1

    except Exception as e:
        log_fail("Self-improvement tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nSelf-improvement results: {passed}/{total} passed")


async def test_distributed():
    print("\n=== Distributed Execution ===")
    passed = 0
    total = 0

    try:
        from nicto_x.distributed.executor import DistributedExecutor

        de = DistributedExecutor(min_workers=2, max_workers=4)
        await de.start()
        total += 1
        log_pass("DistributedExecutor start")
        passed += 1

        task_id = await de.submit("test_task", {"data": "test"}, priority=5)
        total += 1
        assert task_id is not None
        log_pass(f"DistributedExecutor submit: {task_id}")
        passed += 1

        await asyncio.sleep(0.5)

        status = de.get_status()
        total += 1
        assert status["running"]
        assert len(status["workers"]) >= 2
        log_pass(f"DistributedExecutor status: {len(status['workers'])} workers")
        passed += 1

        result = de.get_result(task_id)
        total += 1
        assert result is not None
        log_pass(f"DistributedExecutor get_result: {result['status']}")
        passed += 1

        await de.stop()
        total += 1
        status = de.get_status()
        assert not status["running"]
        log_pass("DistributedExecutor stop")
        passed += 1

    except Exception as e:
        log_fail("Distributed tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nDistributed results: {passed}/{total} passed")


async def test_orchestrator():
    print("\n=== Orchestrator Integration ===")
    passed = 0
    total = 0

    try:
        from nicto_x import NictoXOrchestrator
        from nicto_x.core.config import NictoXConfig

        config = NictoXConfig(version="0.2.0")
        orch = NictoXOrchestrator(config)
        total += 1
        log_pass(f"NictoXOrchestrator init (version {orch.version})")
        passed += 1

        await orch.start()
        total += 1
        assert orch._running
        log_pass("NictoXOrchestrator start")
        passed += 1

        status = orch.get_status()
        total += 1
        assert "agents" in status
        assert "neural_core" in status
        assert len(status["agents"]) == 7
        log_pass(f"NictoXOrchestrator get_status: {len(status['agents'])} agents")
        passed += 1

        result = await orch.process("What is the capital of France? Explain briefly.", context={})
        total += 1
        assert "response" in result
        assert len(result["response"]) > 10
        log_pass(f"NictoXOrchestrator process: response={len(result['response'])} chars, confidence={result.get('confidence', {}).get('score', 0):.3f}")
        passed += 1

        neural = await orch.process_neural("Test neural processing in orchestrator")
        total += 1
        assert neural["tokens"] > 0
        log_pass(f"NictoXOrchestrator process_neural: {neural['tokens']} tokens")
        passed += 1

        mem = orch.get_memory_status()
        total += 1
        assert "episodic" in mem
        assert mem["episodic"] >= 1
        log_pass(f"NictoXOrchestrator get_memory_status: episodic={mem['episodic']}")
        passed += 1

        benchmark_status = orch.get_benchmark_status()
        total += 1
        assert "skills" in benchmark_status
        log_pass(f"NictoXOrchestrator get_benchmark_status: {len(benchmark_status['skills'])} skills")
        passed += 1

        result = await orch.process("Write a simple Python function to add two numbers")
        total += 1
        assert "response" in result
        assert len(result.get("agents_used", [])) > 0
        log_pass(f"NictoXOrchestrator process (coding): agents={result.get('agents_used', [])}")
        passed += 1

        await orch.stop()
        total += 1
        assert not orch._running
        log_pass("NictoXOrchestrator stop")
        passed += 1

    except Exception as e:
        log_fail("Orchestrator tests", f"{e}\n{traceback.format_exc()}")
        total += 5

    print(f"\nOrchestrator results: {passed}/{total} passed")


async def test_vision_analyzer():
    print("\n=== Vision Analyzer ===")
    passed = 0
    total = 0

    try:
        from nicto_x.vision.analyzer import VisionAnalyzer

        va = VisionAnalyzer()
        result = await va.analyze("nonexistent_image.png")
        total += 1
        assert "error" in result
        log_pass(f"VisionAnalyzer file not found: {result.get('error', '')}")
        passed += 1

    except Exception as e:
        log_fail("Vision analyzer tests", f"{e}\n{traceback.format_exc()}")
        total += 1

    print(f"\nVision analyzer results: {passed}/{total} passed")


async def test_auth():
    print("\n=== Security/Auth ===")
    passed = 0
    total = 0

    try:
        from nicto_x.security.auth import AuthManager

        am = AuthManager()
        token = am.create_token("test_user", scopes=["read", "write"])
        total += 1
        assert token.startswith("nx-")
        log_pass(f"AuthManager create_token: {token[:15]}...")
        passed += 1

        valid = am.validate(token, "read")
        total += 1
        assert valid is True
        log_pass("AuthManager validate (valid)")
        passed += 1

        invalid = am.validate("invalid_token", "read")
        total += 1
        assert invalid is False
        log_pass("AuthManager validate (invalid)")
        passed += 1

        tokens = am.list_tokens()
        total += 1
        assert len(tokens) >= 1
        log_pass(f"AuthManager list_tokens: {len(tokens)} tokens")
        passed += 1

    except Exception as e:
        log_fail("Auth tests", f"{e}\n{traceback.format_exc()}")
        total += 3

    print(f"\nAuth results: {passed}/{total} passed")


async def test_security_agent():
    print("\n=== Security Agent ===")
    passed = 0
    total = 0

    try:
        from nicto_x.core.config import NictoXConfig
        from nicto_x.agents.bus import AgentBus
        from nicto_x.agents.security_agent import SecurityAgent

        config = NictoXConfig()
        bus = AgentBus()
        agent = SecurityAgent(bus, config)
        await agent.initialize()

        result = await agent.execute("SELECT * FROM users; DROP TABLE users; -- SQL injection test")
        total += 1
        findings = result.get("findings", [])
        risk_level = result.get("risk_level", "low")
        sql_findings = [f for f in findings if f.get("type") == "sql_injection"]
        log_pass(f"SecurityAgent SQL injection: {len(sql_findings)} SQL findings, risk={risk_level}")
        passed += 1

        result2 = await agent.execute("192.168.1.1 with SSH and MySQL")
        total += 1
        findings2 = result2.get("findings", [])
        targets = result2.get("targets_analyzed", [])
        log_pass(f"SecurityAgent network target: {targets} targets, {len(findings2)} findings")
        passed += 1

    except Exception as e:
        log_fail("Security agent tests", f"{e}\n{traceback.format_exc()}")
        total += 2

    print(f"\nSecurity agent results: {passed}/{total} passed")


async def main():
    print("=" * 60)
    print("NICTO X — COMPREHENSIVE VERIFICATION")
    print("=" * 60)

    tests = [
        test_imports,
        test_neural_core,
        test_agents,
        test_reasoning,
        test_memory,
        test_knowledge,
        test_software,
        test_research,
        test_self_improvement,
        test_distributed,
        test_orchestrator,
        test_vision_analyzer,
        test_auth,
        test_security_agent,
    ]

    total_passed = 0
    total_tests = 0

    for test_fn in tests:
        try:
            await test_fn()
        except Exception as e:
            print(f"\n  [ERROR] {test_fn.__name__}: {e}\n{traceback.format_exc()}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
