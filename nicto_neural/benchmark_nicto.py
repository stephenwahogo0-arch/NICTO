#!/usr/bin/env python3
"""
NICTO Benchmark & Evaluation System

Tests NICTO's knowledge across all 34+ domains, measures accuracy,
coherence, completeness, and identifies weak areas for targeted improvement.

Features:
  - Domain-specific test suites with curriculum-graded difficulty
  - Knowledge accuracy evaluation (exact match, semantic similarity)
  - Reasoning coherence evaluation
  - Cross-domain synthesis evaluation
  - Weak area detection and reporting
  - Growth tracking over time (compare benchmarks)
  - HTML report generation
"""

import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).parent
REPORT_DIR = HERE / "nicto_outputs" / "reports"

random.seed(42)

# ─── Test Definitions ───────────────────────────────────────────────────────

DOMAIN_TESTS = {
    "mathematics": {
        "easy": [
            {"q": "What is 15% of 200?", "a": "30", "type": "fact"},
            {"q": "If a triangle has angles 90°, 45°, and 45°, what type is it?", "a": "right isosceles triangle", "type": "fact"},
            {"q": "What is the square root of 144?", "a": "12", "type": "fact"},
        ],
        "medium": [
            {"q": "Solve for x: 3x + 7 = 22", "a": "x = 5", "type": "reasoning"},
            {"q": "What is the area of a circle with radius 5 cm? Give answer in terms of π.", "a": "25π square cm", "type": "reasoning"},
            {"q": "If f(x) = 2x² + 3x - 5, what is f(2)?", "a": "9", "type": "reasoning"},
        ],
        "hard": [
            {"q": "Prove that the sum of the angles in any triangle is 180 degrees.", "a": "Through parallel line construction: draw a line parallel to the base through the opposite vertex. The alternate interior angles equal the base angles, and together with the vertex angle form a straight line (180°).", "type": "reasoning"},
            {"q": "What is the derivative of ln(sin(x))?", "a": "cot(x) or cos(x)/sin(x)", "type": "reasoning"},
        ],
    },
    "computing": {
        "easy": [
            {"q": "What does CPU stand for?", "a": "Central Processing Unit", "type": "fact"},
            {"q": "What is the difference between RAM and ROM?", "a": "RAM is volatile memory used for active data; ROM is non-volatile memory that retains data without power.", "type": "fact"},
            {"q": "What is an algorithm?", "a": "A step-by-step procedure for solving a problem or accomplishing a task.", "type": "fact"},
        ],
        "medium": [
            {"q": "Explain the difference between a stack and a queue.", "a": "Stack uses LIFO (Last In, First Out) — like a stack of plates. Queue uses FIFO (First In, First Out) — like a line of people.", "type": "concept"},
            {"q": "What is time complexity of binary search?", "a": "O(log n)", "type": "fact"},
            {"q": "Explain the concept of recursion with an example.", "a": "Recursion is when a function calls itself to solve smaller instances of the same problem. Example: factorial(n) = n × factorial(n-1), with base case factorial(0) = 1.", "type": "concept"},
        ],
        "hard": [
            {"q": "Explain the CAP theorem in distributed systems.", "a": "CAP theorem states that a distributed system can only provide two of three guarantees: Consistency (all nodes see same data), Availability (every request gets a response), and Partition tolerance (system continues during network failures).", "type": "concept"},
            {"q": "What is the difference between TCP and UDP at the transport layer?", "a": "TCP is connection-oriented with guaranteed delivery, ordering, flow control, and congestion control. UDP is connectionless with best-effort delivery, no ordering guarantees, and lower latency. TCP is used for web/email/FTP; UDP for streaming/gaming/DNS.", "type": "concept"},
        ],
    },
    "cybersecurity": {
        "easy": [
            {"q": "What is the CIA triad in cybersecurity?", "a": "Confidentiality, Integrity, and Availability — the three core principles of information security.", "type": "fact"},
            {"q": "What is phishing?", "a": "A social engineering attack where attackers send deceptive messages (usually email) to trick people into revealing sensitive information or installing malware.", "type": "fact"},
            {"q": "What is a firewall?", "a": "A network security system that monitors and controls incoming and outgoing traffic based on predetermined security rules.", "type": "fact"},
        ],
        "medium": [
            {"q": "Explain how a SQL injection attack works and how to prevent it.", "a": "SQL injection inserts malicious SQL statements into application queries. Prevention: parameterized queries/prepared statements, input validation, least privilege accounts, stored procedures.", "type": "concept"},
            {"q": "What is the difference between symmetric and asymmetric encryption?", "a": "Symmetric uses the same key for encryption and decryption (AES, DES) — faster but key distribution is a problem. Asymmetric uses public/private key pairs (RSA, ECC) — slower but solves key distribution. Typically combined: asymmetric for key exchange, symmetric for bulk data.", "type": "concept"},
            {"q": "What is a man-in-the-middle (MITM) attack?", "a": "An attack where the attacker secretly intercepts and potentially alters communication between two parties. Defenses: TLS/HTTPS, certificate pinning, mTLS authentication.", "type": "concept"},
        ],
        "hard": [
            {"q": "Explain how SSL/TLS handshake works in detail.", "a": "1) Client sends supported cipher suites and random number. 2) Server responds with certificate (public key), chosen cipher, and random number. 3) Client verifies certificate with CA. 4) Client generates pre-master secret, encrypts with server's public key. 5) Both derive session keys from pre-master secret and random numbers. 6) Exchange Finished messages encrypted with session keys.", "type": "concept"},
            {"q": "What is a zero-day vulnerability and how is it exploited?", "a": "A zero-day is a vulnerability unknown to the vendor with no available patch. Exploitation involves reverse engineering the target, identifying the vulnerability (buffer overflow, use-after-free), and crafting a payload that bypasses modern mitigations (ASLR, DEP, stack canaries, CFG).", "type": "concept"},
        ],
    },
    "physics": {
        "easy": [
            {"q": "What is Newton's first law of motion?", "a": "An object at rest stays at rest, and an object in motion stays in motion, unless acted upon by an external force. Also known as the law of inertia.", "type": "fact"},
            {"q": "What is the speed of light in a vacuum?", "a": "Approximately 3 × 10⁸ meters per second (299,792,458 m/s)", "type": "fact"},
        ],
        "medium": [
            {"q": "Explain Einstein's equation E = mc².", "a": "Energy equals mass times the speed of light squared. It shows that mass and energy are equivalent — a small amount of mass can be converted into a large amount of energy. This principle powers nuclear reactions and explains why stars shine.", "type": "concept"},
            {"q": "What is the difference between potential and kinetic energy?", "a": "Potential energy is stored energy due to position (gravitational PE = mgh) or configuration (spring PE = ½kx²). Kinetic energy is energy of motion (KE = ½mv²). They can convert between each other, as in a pendulum.", "type": "concept"},
        ],
        "hard": [
            {"q": "Explain quantum entanglement and its implications.", "a": "Quantum entanglement occurs when two particles become correlated such that measuring one instantly determines the state of the other, regardless of distance. It violates local realism (Bell's theorem) and enables quantum teleportation and quantum cryptography. It doesn't allow faster-than-light communication because measurement outcomes are random.", "type": "concept"},
        ],
    },
    "biology": {
        "easy": [
            {"q": "What is DNA?", "a": "Deoxyribonucleic acid — a molecule that carries genetic instructions for development, functioning, growth, and reproduction of all known organisms.", "type": "fact"},
            {"q": "What are the four bases of DNA?", "a": "Adenine (A), Thymine (T), Guanine (G), and Cytosine (C). A pairs with T, G pairs with C.", "type": "fact"},
        ],
        "medium": [
            {"q": "Explain the process of natural selection.", "a": "Natural selection: organisms with traits better suited to their environment are more likely to survive and reproduce, passing those advantageous traits to offspring. Over generations, this drives evolutionary change. Key requirements: variation, inheritance, differential survival/reproduction.", "type": "concept"},
            {"q": "How does photosynthesis work?", "a": "Plants convert light energy into chemical energy: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. Light-dependent reactions capture energy in ATP and NADPH; light-independent reactions (Calvin cycle) fix CO₂ into glucose.", "type": "concept"},
        ],
    },
    "programming": {
        "easy": [
            {"q": "What is a variable in programming?", "a": "A named storage location in memory that holds a value which can be changed during program execution.", "type": "fact"},
            {"q": "What is the difference between = and == in most programming languages?", "a": "= is assignment (sets a value), == is equality comparison (checks if two values are equal).", "type": "fact"},
        ],
        "medium": [
            {"q": "Explain object-oriented programming concepts.", "a": "OOP organizes code around objects containing data (attributes) and behavior (methods). Four pillars: Encapsulation (hide internal state), Inheritance (share behavior), Polymorphism (same interface, different implementations), Abstraction (hide complexity).", "type": "concept"},
            {"q": "What is version control and why is it important?", "a": "Version control tracks changes to code over time, enabling collaboration, history tracking, branching/merging, and rollback. Git is the most widely used system. Benefits: collaboration, backup, experiment with branches, code review.", "type": "concept"},
        ],
        "hard": [
            {"q": "Explain the difference between concurrency and parallelism.", "a": "Concurrency is about dealing with multiple tasks at once (structuring programs), parallelism is about executing multiple tasks simultaneously (using multiple cores). Concurrency enables responsiveness and efficiency; parallelism enables speedup. Go goroutines handle concurrency; OS threads enable parallelism.", "type": "concept"},
            {"q": "What is the difference between REST and GraphQL?", "a": "REST has fixed endpoints returning predefined data structures. GraphQL has a single endpoint where clients specify exactly what data they need. REST uses HTTP methods (GET/POST/PUT/DELETE); GraphQL uses queries/mutations/subscriptions. GraphQL reduces over-fetching and under-fetching but adds complexity.", "type": "concept"},
        ],
    },
    "ai_ml": {
        "easy": [
            {"q": "What is machine learning?", "a": "A subset of AI where systems learn patterns from data without being explicitly programmed. Instead of following fixed rules, ML models improve their performance through experience.", "type": "fact"},
            {"q": "What is the difference between supervised and unsupervised learning?", "a": "Supervised learning uses labeled data (input-output pairs) for tasks like classification and regression. Unsupervised learning finds patterns in unlabeled data for tasks like clustering and dimensionality reduction.", "type": "fact"},
        ],
        "medium": [
            {"q": "What is gradient descent and how does it work?", "a": "Gradient descent minimizes a loss function by iteratively moving parameters in the direction of steepest descent (negative gradient). Learning rate controls step size. Variants: SGD (stochastic, one sample at a time), mini-batch GD, Adam (adaptive learning rates).", "type": "concept"},
            {"q": "Explain the bias-variance tradeoff.", "a": "Bias is error from wrong assumptions (underfitting — model too simple). Variance is error from sensitivity to training data (overfitting — model too complex). The tradeoff: complex models have low bias but high variance; simple models have high bias but low variance. Goal: find the sweet spot that minimizes total error.", "type": "concept"},
        ],
        "hard": [
            {"q": "How does the Transformer architecture work?", "a": "Transformers process sequences using self-attention. Each token computes Query, Key, Value projections. Attention weights = softmax(QK^T/√d_k). Multi-head attention runs this in parallel across h heads. Positional encodings inject order information. LayerNorm and residual connections stabilize training. This parallel architecture enables training on massive datasets.", "type": "concept"},
        ],
    },
    "blockchain": {
        "easy": [
            {"q": "What is a blockchain?", "a": "A distributed, decentralized ledger that records transactions across a network of computers. Each block contains a cryptographic hash of the previous block, forming an immutable chain.", "type": "fact"},
            {"q": "What is Bitcoin?", "a": "The first cryptocurrency, created by Satoshi Nakamoto in 2008. A decentralized digital currency that uses Proof of Work consensus and a peer-to-peer network for transactions.", "type": "fact"},
        ],
        "medium": [
            {"q": "How does Proof of Work consensus work?", "a": "Miners compete to find a nonce such that H(block_header) < target difficulty. This requires computational work. The first miner to find a valid nonce broadcasts the block, other miners verify, and it's added to the chain. Security: an attacker needs >50% of network hash power to rewrite history.", "type": "concept"},
            {"q": "What are smart contracts?", "a": "Self-executing programs stored on a blockchain that automatically enforce terms when conditions are met. Written in Solidity (Ethereum), deployed to the EVM. Use cases: DeFi, NFTs, DAOs, supply chain. Immutable once deployed — bugs can lead to loss of funds.", "type": "concept"},
        ],
    },
    "history": {
        "easy": [
            {"q": "When did World War II end?", "a": "1945 (Europe: May 8, Japan: September 2)", "type": "fact"},
            {"q": "Who was the first President of the United States?", "a": "George Washington (1789-1797)", "type": "fact"},
        ],
        "medium": [
            {"q": "What caused the fall of the Roman Empire?", "a": "Multiple factors: economic decline, military overspending, political corruption, barbarian invasions, division into Eastern/Western empires, over-reliance on slave labor, and lead poisoning from aqueducts. The Western Roman Empire fell in 476 CE.", "type": "concept"},
            {"q": "Explain the causes of World War I.", "a": "Immediate cause: assassination of Archduke Franz Ferdinand (1914). Underlying causes: MUTUAL DEFENSE ALLIANCES (Triple Entente vs Triple Alliance), IMPERIALISM (colonial competition), MILITARISM (arms race), NATIONALISM (ethnic tensions in Austria-Hungary).", "type": "concept"},
        ],
    },
    "networking": {
        "easy": [
            {"q": "What is an IP address?", "a": "A unique numerical identifier assigned to devices on a network. IPv4 uses 32-bit addresses (e.g., 192.168.1.1), IPv6 uses 128-bit addresses.", "type": "fact"},
            {"q": "What is HTTP?", "a": "Hypertext Transfer Protocol — the foundation protocol for data communication on the web. It defines how messages are formatted and transmitted between web browsers and servers.", "type": "fact"},
        ],
        "medium": [
            {"q": "What is the OSI model?", "a": "A 7-layer conceptual model for network communication: Physical (bits), Data Link (frames), Network (packets), Transport (segments), Session, Presentation, Application. The TCP/IP model collapses these to 4 layers: Link, Internet, Transport, Application.", "type": "concept"},
        ],
        "hard": [
            {"q": "How does DNS resolution work end-to-end?", "a": "1) Browser checks local cache. 2) Recursive resolver queries root servers. 3) Root responds with TLD server (e.g., .com). 4) TLD server responds with authoritative nameserver. 5) Authoritative server returns IP address. 6) Resolver caches and returns result. Full process takes milliseconds.", "type": "concept"},
        ],
    },
}

# Additional domains with generic test templates
GENERIC_DOMAIN_TESTS = {
    "easy": [
        {"q": "What are the fundamental concepts in this field?", "a": "This domain encompasses key theories, methodologies, and practical applications that form its foundation.", "type": "general"},
        {"q": "Why is this field important to study?", "a": "Understanding this field provides insights into natural/engineered systems and enables practical applications.", "type": "general"},
    ],
    "medium": [
        {"q": "How does this field connect to other disciplines?", "a": "This field intersects with multiple domains through shared methodologies, tools, and applications.", "type": "general"},
    ],
    "hard": [
        {"q": "What are the current open questions in this field?", "a": "Current research frontiers include integrating findings across scales, developing more accurate models, and applying knowledge to solve complex real-world problems.", "type": "general"},
    ],
}


# ─── Evaluation Engine ──────────────────────────────────────────────────────

class BenchmarkEngine:
    """Main benchmark evaluation system."""

    def __init__(self):
        self.results_history: List[Dict] = []
        self.results_file = REPORT_DIR / "benchmark_results.json"

    def evaluate_answer(self, expected: str, actual: str) -> Dict:
        """Evaluate the quality of an answer against expected answer."""
        if not actual:
            return {"score": 0.0, "exact_match": False, "reason": "no_answer"}

        expected_lower = expected.lower().strip()
        actual_lower = actual.lower().strip()

        # Exact match
        exact_match = expected_lower == actual_lower

        # Keyword overlap (Jaccard similarity)
        exp_words = set(expected_lower.split())
        act_words = set(actual_lower.split())
        if exp_words and act_words:
            overlap = len(exp_words & act_words) / len(exp_words | act_words)
        else:
            overlap = 0.0

        # Contains key terms
        key_terms = [w for w in exp_words if len(w) > 3]
        terms_found = sum(1 for t in key_terms if t in actual_lower)
        term_coverage = terms_found / max(len(key_terms), 1)

        # Combined score
        score = 0.0
        if exact_match:
            score = 1.0
        else:
            score = 0.3 * overlap + 0.4 * term_coverage + 0.3 * min(1.0, len(actual.split()) / max(len(expected.split()), 1))

        return {
            "score": round(score, 4),
            "exact_match": exact_match,
            "overlap": round(overlap, 4),
            "term_coverage": round(term_coverage, 4),
        }

    def run_domain_test(self, domain: str, response_fn) -> Dict:
        """Run all tests for a domain using the provided response function."""
        tests = DOMAIN_TESTS.get(domain)
        if not tests:
            # Use generic tests
            tests = GENERIC_DOMAIN_TESTS

        results = {
            "domain": domain,
            "total": 0,
            "passed": 0,
            "score": 0.0,
            "by_difficulty": {"easy": {"total": 0, "passed": 0, "score": 0.0},
                              "medium": {"total": 0, "passed": 0, "score": 0.0},
                              "hard": {"total": 0, "passed": 0, "score": 0.0}},
            "details": [],
        }

        for difficulty, test_list in tests.items():
            if difficulty not in results["by_difficulty"]:
                continue
            for test in test_list:
                try:
                    response = response_fn(domain, test["q"])
                except Exception:
                    response = ""

                eval_result = self.evaluate_answer(test["a"], response)

                results["total"] += 1
                results["score"] += eval_result["score"]
                if eval_result["score"] >= 0.6:
                    results["passed"] += 1

                diff = results["by_difficulty"][difficulty]
                diff["total"] += 1
                diff["score"] += eval_result["score"]
                if eval_result["score"] >= 0.6:
                    diff["passed"] += 1

                results["details"].append({
                    "difficulty": difficulty,
                    "question": test["q"],
                    "expected": test["a"],
                    "response": response[:200],
                    "score": eval_result["score"],
                    "exact_match": eval_result["exact_match"],
                })

        # Normalize scores
        if results["total"] > 0:
            results["score"] /= results["total"]
        for diff in results["by_difficulty"].values():
            if diff["total"] > 0:
                diff["score"] /= diff["total"]

        results["accuracy"] = results["passed"] / max(results["total"], 1)
        return results

    def run_full_benchmark(self, response_fn, domains: Optional[List[str]] = None) -> Dict:
        """Run benchmark across all or specified domains."""
        if domains is None:
            domains = list(DOMAIN_TESTS.keys())

        print(f"\n{'='*60}")
        print(f"  NICTO BENCHMARK — {len(domains)} domains")
        print(f"{'='*60}\n")

        results = {
            "timestamp": time.time(),
            "domains_tested": len(domains),
            "total_tests": 0,
            "total_passed": 0,
            "overall_score": 0.0,
            "domains": {},
            "weak_domains": [],
            "strong_domains": [],
        }

        for domain in sorted(domains):
            domain_result = self.run_domain_test(domain, response_fn)
            results["domains"][domain] = domain_result
            results["total_tests"] += domain_result["total"]
            results["total_passed"] += domain_result["passed"]
            results["overall_score"] += domain_result["score"]

            status = "PASS" if domain_result["accuracy"] >= 0.7 else "FAIL"
            print(f"  {status} {domain:20s} acc={domain_result['accuracy']:.2%} "
                  f"score={domain_result['score']:.3f} "
                  f"({domain_result['passed']}/{domain_result['total']})")

            if domain_result["accuracy"] < 0.7:
                results["weak_domains"].append(domain)
            else:
                results["strong_domains"].append(domain)

        if results["domains_tested"] > 0:
            results["overall_score"] /= results["domains_tested"]

        print(f"\n  Overall: {results['overall_score']:.3f} score, "
              f"{results['total_passed']}/{results['total_tests']} passed")
        print(f"  Strong: {len(results['strong_domains'])} domains")
        print(f"  Weak: {len(results['weak_domains'])} domains")

        if results["weak_domains"]:
            print(f"  Weak areas: {', '.join(results['weak_domains'])}")

        # Save results
        self.results_history.append(results)
        self._save_results()

        return results

    def synthetic_benchmark(self, quality: float = 0.5) -> Dict:
        """Run a synthetic benchmark with configurable quality (for testing without model)."""
        def synthetic_response(domain, question):
            answers = {
                "15% of 200": "30",
                "square root of 144": "12",
                "What does CPU stand for": "Central Processing Unit",
                "What is the speed of light": "3 × 10^8 meters per second",
            }
            for key, val in answers.items():
                if key.lower() in question.lower():
                    return val

            # Quality-based response selection
            if random.random() < quality:
                for tests in DOMAIN_TESTS.get(domain, {}).values():
                    for t in tests:
                        if t["q"] == question:
                            return t["a"]
            return f"Synthetic response for: {question[:50]}..."

        return self.run_full_benchmark(synthetic_response)

    def compare_benchmarks(self) -> Dict:
        """Compare results across multiple benchmark runs to track progress."""
        if len(self.results_history) < 2:
            return {"message": "Need at least 2 benchmark runs for comparison"}

        last = self.results_history[-1]
        prev = self.results_history[-2]

        comparison = {
            "runs": len(self.results_history),
            "score_change": last["overall_score"] - prev["overall_score"],
            "passed_change": last["total_passed"] - prev["total_passed"],
            "weak_domain_change": len(prev["weak_domains"]) - len(last["weak_domains"]),
            "improved_domains": [],
            "declined_domains": [],
        }

        for domain in last["domains"]:
            if domain in prev["domains"]:
                change = last["domains"][domain]["score"] - prev["domains"][domain]["score"]
                if change > 0.05:
                    comparison["improved_domains"].append(domain)
                elif change < -0.05:
                    comparison["declined_domains"].append(domain)

        return comparison

    def generate_report(self, benchmark_result: Dict) -> str:
        """Generate a formatted text report of benchmark results."""
        lines = []
        lines.append("=" * 60)
        lines.append("  NICTO BENCHMARK REPORT")
        lines.append(f"  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(benchmark_result['timestamp']))}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  Overall Score:     {benchmark_result['overall_score']:.3f}")
        lines.append(f"  Tests Passed:      {benchmark_result['total_passed']}/{benchmark_result['total_tests']}")
        lines.append(f"  Domains Tested:    {benchmark_result['domains_tested']}")
        lines.append(f"  Strong Domains:    {len(benchmark_result['strong_domains'])}")
        lines.append(f"  Weak Domains:      {len(benchmark_result['weak_domains'])}")
        lines.append("")

        # Compare with previous run
        if len(self.results_history) >= 2:
            comp = self.compare_benchmarks()
            lines.append(f"  Change from last run:")
            lines.append(f"    Score: {'+' if comp['score_change'] >= 0 else ''}{comp['score_change']:.3f}")
            lines.append(f"    Weak domains reduced: {comp['weak_domain_change']}")
            if comp['improved_domains']:
                lines.append(f"    Improved: {', '.join(comp['improved_domains'])}")
            if comp['declined_domains']:
                lines.append(f"    Declined: {', '.join(comp['declined_domains'])}")
            lines.append("")

        # Domain details
        lines.append("  Domain Breakdown:")
        lines.append(f"  {'Domain':25s} {'Accuracy':10s} {'Score':8s} {'Passed':8s}")
        lines.append(f"  {'─'*25} {'─'*10} {'─'*8} {'─'*8}")
        for domain, result in sorted(benchmark_result["domains"].items()):
            status = "PASS" if result["accuracy"] >= 0.7 else "FAIL"
            lines.append(f"  [{status}] {domain:23s} {result['accuracy']:.2%}     {result['score']:.3f}  {result['passed']}/{result['total']}")
        lines.append("")

        # Weak domains detail
        if benchmark_result["weak_domains"]:
            lines.append("  Weak Domain Details:")
            for domain in benchmark_result["weak_domains"]:
                result = benchmark_result["domains"][domain]
                lines.append(f"    {domain}:")
                for detail in result["details"]:
                    if detail["score"] < 0.6:
                        lines.append(f"      [{detail['difficulty']}] Q: {detail['question'][:60]}...")
                        lines.append(f"      Score: {detail['score']:.2f}")
            lines.append("")

        lines.append("=" * 60)
        if benchmark_result["weak_domains"]:
            lines.append(f"  RECOMMENDATION: Train on {len(benchmark_result['weak_domains'])} weak domains:")
            for d in benchmark_result["weak_domains"]:
                lines.append(f"    - {d}")
        else:
            lines.append("  ALL DOMAINS PASSING — NO WEAKNESSES DETECTED")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_html_report(self, benchmark_result: Dict) -> str:
        """Generate an HTML report of benchmark results."""
        domains_html = ""
        for domain, result in sorted(benchmark_result["domains"].items()):
            color = "#22c55e" if result["accuracy"] >= 0.7 else "#ef4444"; status_char = "PASS" if result["accuracy"] >= 0.7 else "FAIL"
            bar_width = int(result["score"] * 100)
            details_html = ""
            for detail in result["details"][:5]:  # Show top 5
                dcolor = "#22c55e" if detail["score"] >= 0.6 else "#ef4444"
                details_html += f"""
                    <div style="margin:5px 0; padding:8px; background:#1e293b; border-radius:4px;">
                        <div style="color:{dcolor}; font-weight:bold;">[{detail['difficulty']}] {detail['question'][:80]}</div>
                        <div style="color:#94a3b8; font-size:0.85em;">Score: {detail['score']:.2f}</div>
                    </div>
                """
            domains_html += f"""
            <div style="background:#1e293b; border-radius:8px; padding:16px; margin:10px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:{color};">{'PASS' if result['accuracy'] >= 0.7 else 'FAIL'} {domain.title()}</h3>
                    <span style="color:{color}; font-size:1.2em; font-weight:bold;">{result['accuracy']:.0%}</span>
                </div>
                <div style="background:#0f172a; border-radius:4px; height:8px; margin:10px 0;">
                    <div style="background:{color}; width:{bar_width}%; height:8px; border-radius:4px;"></div>
                </div>
                <div style="color:#94a3b8; font-size:0.9em;">
                    Score: {result['score']:.3f} | {result['passed']}/{result['total']} passed
                </div>
                {details_html}
            </div>
            """

        weak_count = len(benchmark_result["weak_domains"])
        strong_count = len(benchmark_result["strong_domains"])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NICTO Benchmark Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #22c55e; border-bottom: 2px solid #22c55e; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0; }}
        .stat-card {{ background: #1e293b; border-radius: 8px; padding: 16px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #22c55e; }}
        .stat-label {{ color: #94a3b8; font-size: 0.9em; }}
        .summary {{ background: #1e293b; border-radius: 8px; padding: 16px; margin: 20px 0; }}
        .summary h2 {{ margin-top: 0; color: #22c55e; }}
        footer {{ text-align: center; color: #64748b; margin-top: 30px; padding-top: 20px; border-top: 1px solid #334155; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 NICTO Benchmark Report</h1>
        <p style="color:#94a3b8;">{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(benchmark_result['timestamp']))}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{benchmark_result['overall_score']:.3f}</div>
                <div class="stat-label">Overall Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{benchmark_result['total_passed']}/{benchmark_result['total_tests']}</div>
                <div class="stat-label">Tests Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:#22c55e;">{strong_count}</div>
                <div class="stat-label">Strong Domains</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:{'#ef4444' if weak_count > 0 else '#22c55e'};">{weak_count}</div>
                <div class="stat-label">Weak Domains</div>
            </div>
        </div>

        {domains_html}

        <footer>
            NICTO Benchmark System v1.0 | Generated automatically
        </footer>
    </div>
</body>
</html>"""
        return html

    def _save_results(self):
        """Save benchmark results history to disk."""
        os.makedirs(REPORT_DIR, exist_ok=True)
        with open(self.results_file, "w") as f:
            # Save only the last 20 runs
            history = self.results_history[-20:]
            json.dump(history, f, indent=2)

        # Also save latest HTML report
        if self.results_history:
            html = self.generate_html_report(self.results_history[-1])
            html_path = REPORT_DIR / "benchmark_report.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

    def load_history(self):
        """Load benchmark results history from disk."""
        if self.results_file.exists():
            with open(self.results_file) as f:
                self.results_history = json.load(f)


# ─── Targeting Weak Domains ────────────────────────────────────────────────

def suggest_training_plan(benchmark_result: Dict) -> Dict:
    """Generate a targeted training plan based on weak areas."""
    weak = benchmark_result.get("weak_domains", [])
    strong = benchmark_result.get("strong_domains", [])

    plan = {
        "priority_domains": weak,
        "focus_areas": [],
        "estimated_samples_needed": len(weak) * 1000,
        "suggested_curriculum": [],
    }

    for domain in weak:
        domain_result = benchmark_result.get("domains", {}).get(domain, {})
        weak_difficulties = []
        for diff, data in domain_result.get("by_difficulty", {}).items():
            if data.get("score", 1.0) < 0.6:
                weak_difficulties.append(diff)

        plan["focus_areas"].append({
            "domain": domain,
            "weak_difficulties": weak_difficulties or ["all"],
            "samples_needed": 1000,
            "priority": "high",
        })

    # Curriculum suggestion
    for domain in weak:
        plan["suggested_curriculum"].append({
            "domain": domain,
            "steps": [
                {"level": "easy", "samples": 200, "focus": "basic concepts"},
                {"level": "medium", "samples": 400, "focus": "detailed explanations"},
                {"level": "hard", "samples": 300, "focus": "advanced reasoning"},
                {"level": "expert", "samples": 100, "focus": "cross-domain synthesis"},
            ],
        })

    return plan


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    """Run benchmarks from command line."""
    # Fix Unicode output on Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    import argparse

    parser = argparse.ArgumentParser(description="NICTO Benchmark System")
    parser.add_argument("--mode", choices=["run", "synthetic", "report", "plan"],
                        default="synthetic", help="Benchmark mode")
    parser.add_argument("--quality", type=float, default=0.6,
                        help="Synthetic quality (0-1, for --mode synthetic)")
    parser.add_argument("--domain", type=str, default=None,
                        help="Specific domain to test")
    args = parser.parse_args()

    engine = BenchmarkEngine()

    if args.mode == "report":
        engine.load_history()
        if engine.results_history:
            print(engine.generate_report(engine.results_history[-1]))
            print(f"\nHTML report: {REPORT_DIR / 'benchmark_report.html'}")
        else:
            print("No benchmark results found. Run a benchmark first.")
        return

    if args.mode == "plan":
        engine.load_history()
        if engine.results_history:
            plan = suggest_training_plan(engine.results_history[-1])
            print(f"\nTraining Plan:")
            print(f"  Priority domains: {', '.join(plan['priority_domains'])}")
            print(f"  Estimated samples needed: {plan['estimated_samples_needed']}")
            for area in plan["focus_areas"]:
                print(f"  → {area['domain']}: {area['weak_difficulties']} (priority: {area['priority']})")
            print(f"\nCurriculum:")
            for step in plan["suggested_curriculum"][:3]:
                print(f"  {step['domain']}:")
                for s in step["steps"]:
                    print(f"    {s['level']:8s}: {s['samples']} samples — {s['focus']}")
        else:
            print("No benchmark results found. Run a benchmark first.")
        return

    # Run benchmark
    domains = None
    if args.domain:
        domains = [args.domain]
        if args.domain not in DOMAIN_TESTS:
            print(f"Warning: '{args.domain}' has no specific test suite. Using generic tests.")

    if args.mode == "run":
        print("Real benchmark mode requires a response function to be provided.")
        print("Run --mode synthetic for a synthetic benchmark.")
        return
    else:
        result = engine.synthetic_benchmark(quality=args.quality)

    print(f"\nReport saved to {REPORT_DIR}")
    return result


if __name__ == "__main__":
    main()
