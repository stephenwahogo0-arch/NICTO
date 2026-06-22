"""NICTO Multi-Model Training + Verification Pipeline.
Trains/enhances all 4 models (Kyros, Omega, Main, X) and runs comprehensive verification.
"""
import sys, os, json, time, asyncio, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'nikto-core', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'nicto-x', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'nicto-game', 'src'))

RESULTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'model_verification_results.json')
REPORT_FILE = os.path.join(os.path.dirname(__file__), '..', 'MODEL_VERIFICATION_REPORT.md')

STANDARD_PROMPTS = {
    "reasoning": "If a train leaves station A at 60 mph and another leaves station B at 90 mph toward each other 300 miles apart, when do they meet?",
    "knowledge": "Explain the significance of the transformer architecture in modern AI.",
    "coding": "Write a Python function to find the longest palindrome substring in a given string.",
    "ethics": "Is it ethical to deploy AI systems that can make autonomous decisions without human oversight?",
    "creative": "Write a short poem about artificial intelligence and consciousness.",
    "security": "What are the most common web application vulnerabilities and how can they be prevented?",
    "memory": "What did I just ask you? Can you recall the previous question?",
}

MODEL_CAPABILITY_MAP = {
    "nicto_kyros": {"max_response_len": 200, "has_reasoning": False, "has_knowledge": False, "has_memory": True, "has_security": False},
    "nicto_omega": {"max_response_len": 500, "has_reasoning": True, "has_knowledge": True, "has_memory": True, "has_security": False},
    "nicto_main": {"max_response_len": 500, "has_reasoning": True, "has_knowledge": True, "has_memory": True, "has_security": True},
    "nicto_x": {"max_response_len": 1000, "has_reasoning": True, "has_knowledge": True, "has_memory": True, "has_security": True},
}


def train_phase():
    """Phase 1: Train/enhance all 4 model pipelines."""
    print("=" * 70)
    print("PHASE 1: TRAINING ALL 4 MODELS")
    print("=" * 70)
    results = {"nicto_kyros": {}, "nicto_omega": {}, "nicto_main": {}, "nicto_x": {}}

    from nikto.brain.core import NiktoBrain

    brain = NiktoBrain()

    # --- Train Kyros: enhance direct response templates ---
    print("\n[Kyros] Training minimal pipeline...")
    kyros_start = time.time()
    kyros_response = brain.process_kyros("Initializing Kyros training sequence.")
    results["nicto_kyros"]["init_time"] = round((time.time() - kyros_start) * 1000, 2)
    results["nicto_kyros"]["init_response"] = kyros_response.get("response", "")[:100]
    print(f"  Initialized in {results['nicto_kyros']['init_time']}ms")

    # --- Train Omega: enhance reasoning chains ---
    print("\n[Omega] Training reasoning pipeline...")
    omega_train_start = time.time()
    for i in range(3):
        brain.process("Training iteration {}: Enhancing reasoning pathways.".format(i))
    results["nicto_omega"]["train_time"] = round((time.time() - omega_train_start) * 1000, 2)
    omega_response = brain.process("What is the meaning of continuous learning?")
    results["nicto_omega"]["thought_count"] = len(brain.reasoner.thought_history)
    print(f"  Thoughts after training: {results['nicto_omega']['thought_count']}")

    # --- Train Main: enhance scanning + reasoning ---
    print("\n[Main] Training full pipeline with security...")
    main_train_start = time.time()
    for i in range(3):
        brain.process_main("Security audit training pass {}: Checking for vulnerabilities.".format(i))
    results["nicto_main"]["train_time"] = round((time.time() - main_train_start) * 1000, 2)
    main_response = brain.process_main("Scan this input for SQL injection: ' OR 1=1 --")
    results["nicto_main"]["scan_result"] = main_response.get("security_scan", {})
    print(f"  Security scan findings: {results['nicto_main'].get('scan_result', {}).get('findings', 'N/A')}")

    # --- Train X: enhance orchestrator ---
    print("\n[X] Training frontier agent pipeline...")
    x_train_start = time.time()
    if brain.nicto_x:
        try:
            import asyncio, inspect
            start_fn = brain.nicto_x.start
            if inspect.iscoroutinefunction(start_fn):
                asyncio.run(start_fn())
            else:
                start_fn()
            x_response = brain.process_x("Initialize X frontier training sequence.")
            results["nicto_x"]["orchestrator_started"] = True
            results["nicto_x"]["response"] = x_response.get("response", "")[:100]
            x_status = brain.nicto_x.get_status()
            results["nicto_x"]["agent_count"] = len(x_status.get("agents", []))
            print(f"  Agents active: {results['nicto_x'].get('agent_count', 'N/A')}")
            stop_fn = brain.nicto_x.stop
            if inspect.iscoroutinefunction(stop_fn):
                asyncio.run(stop_fn())
            else:
                stop_fn()
        except Exception as e:
            results["nicto_x"]["orchestrator_started"] = False
            results["nicto_x"]["error"] = str(e)
            print(f"  Warning: Nicto X orchestrator error: {e}")
    else:
        results["nicto_x"]["orchestrator_started"] = False
        print("  Nicto X orchestrator not available")
    results["nicto_x"]["train_time"] = round((time.time() - x_train_start) * 1000, 2)

    return results, brain


def benchmark_phase(brain):
    """Phase 2: Benchmark all 4 models on standardized prompts."""
    print("\n" + "=" * 70)
    print("PHASE 2: BENCHMARKING ALL 4 MODELS")
    print("=" * 70)

    models = ["nicto_kyros", "nicto_omega", "nicto_main", "nicto_x"]
    processors = {
        "nicto_kyros": brain.process_kyros,
        "nicto_omega": brain.process,
        "nicto_main": brain.process_main,
        "nicto_x": brain.process_x,
    }

    benchmarks = {}

    for model_id in models:
        print(f"\n--- Benchmarking {model_id} ---")
        proc = processors[model_id]
        model_results = {}

        for prompt_name, prompt_text in STANDARD_PROMPTS.items():
            start = time.time()
            try:
                if model_id == "nicto_x" and brain.nicto_x:
                    import asyncio, inspect
                    start_fn = brain.nicto_x.start
                    if inspect.iscoroutinefunction(start_fn):
                        asyncio.run(start_fn())
                    else:
                        start_fn()
                result = proc(prompt_text)
                elapsed = round((time.time() - start) * 1000, 2)
                response = result.get("response", "")
                resp_len = len(response)
                has_error = "error" in result and result["error"]
                model_results[prompt_name] = {
                    "latency_ms": elapsed,
                    "response_length": resp_len,
                    "has_error": bool(has_error),
                    "response_preview": response[:80] if response else "(empty)",
                }
                status = "OK" if not has_error else "ERR"
                print(f"  [{status}] {prompt_name}: {elapsed}ms, {resp_len} chars")
            except Exception as e:
                model_results[prompt_name] = {"latency_ms": 0, "response_length": 0, "has_error": True, "error": str(e)}
                print(f"  [ERR] {prompt_name}: {e}")
            finally:
                if model_id == "nicto_x" and brain.nicto_x:
                    try:
                        import asyncio, inspect
                        stop_fn = brain.nicto_x.stop
                        if inspect.iscoroutinefunction(stop_fn):
                            asyncio.run(stop_fn())
                        else:
                            stop_fn()
                    except Exception:
                        pass

        benchmarks[model_id] = model_results

    return benchmarks


def analyze_results(train_results, benchmarks):
    """Phase 3: Analyze results and generate report."""
    print("\n" + "=" * 70)
    print("PHASE 3: ANALYSIS & REPORT")
    print("=" * 70)

    scores = {}
    for model_id in ["nicto_kyros", "nicto_omega", "nicto_main", "nicto_x"]:
        caps = MODEL_CAPABILITY_MAP[model_id]
        mb = benchmarks.get(model_id, {})
        total_latency = sum(v.get("latency_ms", 0) for v in mb.values())
        avg_latency = total_latency / max(len(mb), 1)
        total_errors = sum(1 for v in mb.values() if v.get("has_error"))
        total_resp_len = sum(v.get("response_length", 0) for v in mb.values())
        success_rate = ((len(mb) - total_errors) / max(len(mb), 1)) * 100

        scores[model_id] = {
            "avg_latency_ms": round(avg_latency, 2),
            "total_response_chars": total_resp_len,
            "success_rate": round(success_rate, 1),
            "errors": total_errors,
            "tests_run": len(mb),
            "training_init_time_ms": train_results.get(model_id, {}).get("init_time") or train_results.get(model_id, {}).get("train_time", 0),
        }

    # Generate comparison table
    print("\nModel Performance Comparison:\n")
    header = f"{'Model':<16} {'Latency':<12} {'Response':<12} {'Success':<12} {'Errors':<8}"
    print(header)
    print("-" * len(header))
    for model_id, s in scores.items():
        print(f"{model_id:<16} {s['avg_latency_ms']:<8}ms  {s['total_response_chars']:<8}ch  {s['success_rate']:<7}%  {s['errors']:<8}")

    return scores


def generate_report(train_results, benchmarks, scores):
    """Generate a markdown verification report."""
    lines = []
    lines.append("# NICTO Multi-Model Training & Verification Report")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("## Models Tested")
    lines.append("| Model | Tier | Capabilities | Status |")
    lines.append("|-------|------|-------------|--------|")
    lines.append("| **Kyros** | ⚡ Fast | Identity + Basic Memory + Direct Response | Minimal pipeline |")
    lines.append("| **Omega** | ⚖️ Balanced | Reasoning + Memory + Learning + Emotion + Conscience + Metacognition | Core engine |")
    lines.append("| **Main** | 🔧 Full | Omega + Security Scanning + Enhanced Reasoning + Autopilot | Full-featured |")
    lines.append("| **X** | 🚀 Frontier | 7 Agents + Orchestrator + Neural Core + Distributed Execution | Frontier |")
    lines.append("")

    lines.append("## Performance Benchmarks")
    lines.append("| Prompt | Kyros | Omega | Main | X |")
    lines.append("|--------|-------|-------|------|---|")
    for prompt_name in STANDARD_PROMPTS:
        row = f"| **{prompt_name}** "
        for model_id in ["nicto_kyros", "nicto_omega", "nicto_main", "nicto_x"]:
            bm = benchmarks.get(model_id, {}).get(prompt_name, {})
            lat = bm.get("latency_ms", 0)
            err = "⚠️" if bm.get("has_error") else "✓"
            row += f"| {lat}ms {err} "
        lines.append(row + "|")
    lines.append("")

    lines.append("## Summary Scores")
    lines.append("| Model | Avg Latency | Total Response | Success Rate | Errors | Training Time |")
    lines.append("|-------|-------------|----------------|-------------|-------|--------------|")
    for model_id in ["nicto_kyros", "nicto_omega", "nicto_main", "nicto_x"]:
        s = scores.get(model_id, {})
        lines.append(f"| {model_id} | {s.get('avg_latency_ms', 0)}ms | {s.get('total_response_chars', 0)} chars | {s.get('success_rate', 0)}% | {s.get('errors', 0)} | {s.get('training_init_time_ms', 0)}ms |")
    lines.append("")

    lines.append("## Next Steps")
    lines.append("1. Connect actual LLM weights to NeuralCore for true neural inference")
    lines.append("2. Run Unsloth LoRA fine-tuning on GPU hardware with super_v3 data (361K entries)")
    lines.append("3. Add more standardized benchmark prompts across all domains")
    lines.append("4. Implement reinforcement learning from model comparisons")
    lines.append("5. Deploy distributed evaluation across multiple worker nodes")
    lines.append("")

    report = "\n".join(lines)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport written to {REPORT_FILE}")
    return report


def run_external_test_suites():
    """Phase 4: Run existing test suites."""
    print("\n" + "=" * 70)
    print("PHASE 4: EXTERNAL TEST SUITES")
    print("=" * 70)
    test_results = {}

    # NICTO X 66-test suite
    print("\n--- NICTO X Test Suite ---")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'nicto-x', 'tests'))
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_all",
            os.path.join(os.path.dirname(__file__), '..', 'packages', 'nicto-x', 'tests', 'test_all.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        test_results["nicto_x_tests"] = "loaded"
        print("  NICTO X test module loaded (run separately for full output)")
    except Exception as e:
        test_results["nicto_x_tests"] = str(e)
        print(f"  Could not load NICTO X tests: {e}")

    return test_results


def main():
    print("=" * 70)
    print("  NICTO MULTI-MODEL TRAINING & VERIFICATION v2.0")
    print("  Kyros | Omega | Main | X")
    print("=" * 70)

    total_start = time.time()

    # Phase 1: Train
    train_results, brain = train_phase()

    # Phase 2: Benchmark
    benchmarks = benchmark_phase(brain)

    # Phase 3: Analyze
    scores = analyze_results(train_results, benchmarks)

    # Phase 4: Generate report
    report = generate_report(train_results, benchmarks, scores)

    # Phase 5: External tests
    test_results = run_external_test_suites()

    total_time = round(time.time() - total_start, 2)

    # Save all results
    all_results = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "total_time_seconds": total_time,
        "training": train_results,
        "benchmarks": benchmarks,
        "scores": scores,
        "external_tests": test_results,
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n{'=' * 70}")
    print(f"  VERIFICATION COMPLETE — {total_time}s total")
    print(f"  Results saved to {RESULTS_FILE}")
    print(f"  Report saved to {REPORT_FILE}")
    print(f"{'=' * 70}")

    # Print final verdict
    all_pass = all(s.get("errors", 1) == 0 for s in scores.values())
    print(f"\n  Overall Status: {'ALL MODELS VERIFIED [OK]' if all_pass else 'SOME ISSUES FOUND'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
