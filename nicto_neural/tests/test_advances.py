import os
import sys
import tempfile
import asyncio
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestMultiPathCoT(unittest.TestCase):
    def test_spec_dataclasses(self):
        from nicto_neural.reasoning.multi_path_cot import ReasoningPath, MultiPathResult
        rp = ReasoningPath(strategy="deductive", steps=["a"], conclusion="c", confidence=0.85)
        self.assertEqual(rp.strategy, "deductive")
        self.assertEqual(rp.confidence, 0.85)
        mpr = MultiPathResult(best_path=rp, all_paths=[rp], selection_reason="best", consistency_score=0.85, domain="test")
        self.assertEqual(mpr.best_path.strategy, "deductive")

    def test_think_returns_multipathresult(self):
        from nicto_neural.reasoning.multi_path_cot import MultiPathCoT, MultiPathResult
        cot = MultiPathCoT()
        result = asyncio.run(cot.think("What is 2+2?", "mathematics"))
        self.assertIsInstance(result, MultiPathResult)
        self.assertEqual(len(result.all_paths), 3)
        self.assertIn(result.best_path.strategy, ["deductive", "inductive", "abductive"])

    def test_get_stats(self):
        from nicto_neural.reasoning.multi_path_cot import MultiPathCoT
        cot = MultiPathCoT()
        asyncio.run(cot.think("test", "general"))
        stats = cot.get_stats()
        self.assertEqual(stats["total_thinks"], 1)
        self.assertIn("strategy_wins", stats)


class TestCrossSessionMemory(unittest.TestCase):
    def test_store_and_recall(self):
        from nicto_neural.memory.cross_session import CrossSessionMemory
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            mem = CrossSessionMemory(db_path=db_path)
            mem.store_fact("f1", "Python is a language", "programming", 0.95, 1)
            results = mem.recall_facts(domain="programming", limit=10)
            self.assertTrue(len(results) >= 1)
            self.assertEqual(results[0]["fact"], "Python is a language")
            mem._db.close()
        finally:
            os.unlink(db_path)

    def test_recall_facts_accepts_query(self):
        from nicto_neural.memory.cross_session import CrossSessionMemory
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            mem = CrossSessionMemory(db_path=db_path)
            mem.store_fact("f2", "Nmap for port scanning", "cybersecurity", 0.9, 1)
            results = mem.recall_facts(query="nmap", limit=5)
            self.assertIsInstance(results, list)
            mem._db.close()
        finally:
            os.unlink(db_path)


class TestRealtimeImprovement(unittest.TestCase):
    def test_improve_returns_improvementresult(self):
        from nicto_neural.learning.realtime_improvement import RealtimeImprovementEngine, ImprovementResult
        engine = RealtimeImprovementEngine()
        result = asyncio.run(engine.improve())
        self.assertIsInstance(result, ImprovementResult)
        self.assertGreaterEqual(result.interaction_count, 1)

    def test_improve_with_args(self):
        from nicto_neural.learning.realtime_improvement import RealtimeImprovementEngine
        engine = RealtimeImprovementEngine()
        result = asyncio.run(engine.improve(question="How do I scan ports?", response="Use nmap -sS", confidence=0.8, domain="cybersecurity", truth_verified=True, claims_blocked=1))
        self.assertGreater(result.interaction_count, 0)


class TestCalibrationEngine(unittest.TestCase):
    def test_calibrate(self):
        from nicto_neural.reasoning.calibration_engine import CalibrationEngine
        ce = CalibrationEngine()
        calibrated = ce.calibrate(0.85, "cybersecurity", {"some": "result"})
        self.assertGreaterEqual(calibrated, 0.05)
        self.assertLessEqual(calibrated, 0.99)

    def test_adjust(self):
        from nicto_neural.reasoning.calibration_engine import CalibrationEngine
        ce = CalibrationEngine()
        delta = ce.adjust(0.8, 0.9, "programming")
        self.assertIsInstance(delta, float)

    def test_get_calibration_report(self):
        from nicto_neural.reasoning.calibration_engine import CalibrationEngine
        ce = CalibrationEngine()
        for i in range(10):
            ce.adjust(0.7 + i * 0.02, 0.75, "general")
        report = ce.get_calibration_report()
        self.assertIn("general", report)


class TestRewardModel(unittest.TestCase):
    def test_compute_returns_float(self):
        from nicto_neural.learning.reward_model import RewardModel
        rm = RewardModel()
        r = rm.compute(output="OK", expected="OK")
        self.assertIsInstance(r, float)
        self.assertGreaterEqual(r, 0.0)

    def test_explain_reward_returns_string(self):
        from nicto_neural.learning.reward_model import RewardModel
        rm = RewardModel()
        explanation = rm.explain_reward(output="A", expected="A")
        self.assertIsInstance(explanation, str)
        self.assertIn("Total reward", explanation)

    def test_get_history_stats(self):
        from nicto_neural.learning.reward_model import RewardModel
        rm = RewardModel()
        rm.compute(output="x", expected="x")
        rm.compute(output="y", expected="z")
        stats = rm.get_history_stats()
        self.assertGreaterEqual(stats["total_episodes"], 2)

    def test_ten_components_present(self):
        from nicto_neural.learning.reward_model import RewardModel
        rm = RewardModel()
        self.assertEqual(len(rm.WEIGHTS), 10)

    def test_get_component_breakdown(self):
        from nicto_neural.learning.reward_model import RewardModel
        rm = RewardModel()
        breakdown = rm.get_component_breakdown(output="test", expected="test")
        self.assertIn("total_reward", breakdown)
        self.assertIn("components", breakdown)


class TestDomainProfiler(unittest.TestCase):
    def test_get_profile_no_domain(self):
        from nicto_neural.neural.domain_profiler import DomainProfiler
        dp = DomainProfiler()
        profile = dp.get_profile()
        self.assertIn("domains", profile)
        self.assertIn("strongest", profile)

    def test_get_profile_with_domain(self):
        from nicto_neural.neural.domain_profiler import DomainProfiler
        dp = DomainProfiler()
        profile = dp.get_profile("cybersecurity")
        self.assertIn("elo", profile)

    def test_record(self):
        from nicto_neural.neural.domain_profiler import DomainProfiler
        dp = DomainProfiler()
        dp.record("cybersecurity", 0.9, 150.0)
        profile = dp.get_profile("cybersecurity")
        self.assertGreaterEqual(profile["samples"], 1)


class TestContextCompressor(unittest.TestCase):
    def test_compress_with_text(self):
        from nicto_neural.memory.context_compressor import ContextCompressor
        cc = ContextCompressor()
        result = cc.compress("A" * 2000)
        self.assertIsInstance(result, dict)
        self.assertIn("compressed", result)

    def test_get_stats(self):
        from nicto_neural.memory.context_compressor import ContextCompressor
        cc = ContextCompressor()
        stats = cc.get_stats()
        self.assertIn("current_tokens", stats)
        self.assertEqual(stats["max_tokens"], 1_000_000)


class TestPatternDiscovery(unittest.TestCase):
    def test_discover_returns_list(self):
        from nicto_neural.reasoning.pattern_discovery import PatternDiscoveryEngine
        pde = PatternDiscoveryEngine()
        patterns = pde.discover()
        self.assertIsInstance(patterns, list)

    def test_get_insights(self):
        from nicto_neural.reasoning.pattern_discovery import PatternDiscoveryEngine
        pde = PatternDiscoveryEngine()
        insights = pde.get_insights()
        self.assertIsInstance(insights, list)


class TestMetaLearner(unittest.TestCase):
    def test_observe_and_adapt(self):
        from nicto_neural.learning.meta_learner import MetaLearner
        ml = MetaLearner()
        result = ml.observe_and_adapt(task={"type": "test"}, result={"history": [{"loss": 1.0}, {"loss": 0.5}]})
        self.assertTrue(result["adapted"])

    def test_get_meta_stats(self):
        from nicto_neural.learning.meta_learner import MetaLearner
        ml = MetaLearner()
        stats = ml.get_meta_stats()
        self.assertIn("strategies_tried", stats)


class TestHallucinationEliminator(unittest.TestCase):
    def test_check_response_clean(self):
        from nicto_neural.reasoning.hallucination_eliminator import HallucinationEliminator
        he = HallucinationEliminator()
        result = he.check_response("The sky is blue.")
        self.assertTrue(result.is_clean)
        self.assertEqual(len(result.issues), 0)

    def test_check_response_detects_myth(self):
        from nicto_neural.reasoning.hallucination_eliminator import HallucinationEliminator
        he = HallucinationEliminator()
        result = he.check_response("Humans only use 10% of their brain.")
        self.assertFalse(result.is_clean)
        self.assertGreater(len(result.issues), 0)

    def test_get_stats(self):
        from nicto_neural.reasoning.hallucination_eliminator import HallucinationEliminator
        he = HallucinationEliminator()
        he.check_response("test")
        stats = he.get_stats()
        self.assertGreaterEqual(stats["total_checks"], 1)


class TestSuperBenchmark(unittest.TestCase):
    def test_record_and_compare(self):
        from nicto_neural.metrics.super_benchmark import SuperBenchmark
        sb = SuperBenchmark()
        sb.record_nicto_score("mmlu", 85.0)
        report = sb.generate_comparison_report()
        self.assertIn("benchmarks", report)
        self.assertIn("summary", report)
        self.assertIn("nicto_leads_in", report)

    def test_print_leaderboard(self):
        from nicto_neural.metrics.super_benchmark import SuperBenchmark
        sb = SuperBenchmark()
        sb.record_nicto_score("gsm8k", 90.0)
        board = sb.print_leaderboard()
        self.assertIn("NICTO", board)
        self.assertIn("DeepSeek", board)


class TestNeuralCoreProcess(unittest.TestCase):
    def test_process_returns_dict(self):
        from nicto_neural.neural_core import NeuralCore
        core = NeuralCore()
        result = core.process({"query": "What is 2+2?", "domain": "mathematics"})
        self.assertIsInstance(result, dict)
        self.assertIn("cot_strategy", result)

    def test_competitive_status(self):
        from nicto_neural.neural_core import NeuralCore
        core = NeuralCore()
        status = core.get_competitive_status()
        self.assertIn("benchmark_report", status)
        self.assertIn("domain_profile", status)


if __name__ == "__main__":
    unittest.main()
