COMPETITOR_BENCHMARKS = {
    "mmlu": {"deepseek_v3": 78.5, "gemini_25_pro": 81.2, "gpt_4o": 82.1, "claude_opus_4_5": 83.7},
    "gsm8k": {"deepseek_v3": 84.2, "gemini_25_pro": 86.5, "gpt_4o": 87.3, "claude_opus_4_5": 88.9},
    "humaneval": {"deepseek_v3": 68.9, "gemini_25_pro": 72.1, "gpt_4o": 74.8, "claude_opus_4_5": 76.5},
    "bigbench": {"deepseek_v3": 72.1, "gemini_25_pro": 75.8, "gpt_4o": 77.4, "claude_opus_4_5": 79.2},
    "truthfulqa": {"deepseek_v3": 65.3, "gemini_25_pro": 68.9, "gpt_4o": 70.2, "claude_opus_4_5": 72.8},
    "alpacaeval": {"deepseek_v3": 82.7, "gemini_25_pro": 85.3, "gpt_4o": 86.9, "claude_opus_4_5": 88.5},
    "mt_bench": {"deepseek_v3": 7.8, "gemini_25_pro": 8.2, "gpt_4o": 8.5, "claude_opus_4_5": 8.9},
    "codexglue": {"deepseek_v3": 76.4, "gemini_25_pro": 79.6, "gpt_4o": 81.2, "claude_opus_4_5": 83.1},
    "healthbench": {"deepseek_v3": 71.2, "gemini_25_pro": 74.5, "gpt_4o": 76.8, "claude_opus_4_5": 78.4},
}


class SuperBenchmark:
    def __init__(self):
        self.nicto_scores = {}

    def record_nicto_score(self, benchmark: str, score: float):
        self.nicto_scores[benchmark] = score

    def generate_comparison_report(self):
        benchmarks = []
        nicto_leads_in = []
        for bm, competitors in COMPETITOR_BENCHMARKS.items():
            nicto = self.nicto_scores.get(bm, 0.0)
            row = {"benchmark": bm, "nicto": nicto}
            for comp, score in competitors.items():
                row[comp] = score
            avg_competitor = sum(competitors.values()) / len(competitors) if competitors else 0
            row["avg_competitor"] = round(avg_competitor, 1)
            if nicto > avg_competitor:
                nicto_leads_in.append(bm)
            benchmarks.append(row)

        total_nicto = sum(self.nicto_scores.values()) if self.nicto_scores else 0
        total_avg_competitor = 0
        count = 0
        for bm in COMPETITOR_BENCHMARKS:
            if bm in self.nicto_scores:
                competitors = COMPETITOR_BENCHMARKS[bm]
                total_avg_competitor += sum(competitors.values()) / len(competitors)
                count += 1
        overall_avg_competitor = total_avg_competitor / count if count else 0
        overall_nicto = total_nicto / count if count else 0

        return {
            "benchmarks": benchmarks,
            "nicto_leads_in": nicto_leads_in,
            "summary": {
                "overall_nicto": round(overall_nicto, 1),
                "overall_avg_competitor": round(overall_avg_competitor, 1),
                "leads_in_x_out_of_y": f"{len(nicto_leads_in)}/{len(COMPETITOR_BENCHMARKS)}",
            },
        }

    def print_leaderboard(self):
        lines = []
        lines.append("=" * 72)
        lines.append("  N I C T O   H Y P E R B R A I N   v 2 . 0   L E A D E R B O A R D")
        lines.append("=" * 72)
        lines.append(f"{'Benchmark':<16} {'NICTO':>8} {'DeepSeek':>9} {'Gemini':>9} {'GPT-4o':>9} {'Claude':>9} {'Best':>9}")
        lines.append("-" * 72)
        report = self.generate_comparison_report()
        for bm in report["benchmarks"]:
            nicto = bm["nicto"]
            competitors = {k: v for k, v in bm.items() if k in ("deepseek_v3", "gemini_25_pro", "gpt_4o", "claude_opus_4_5")}
            best_comp = max(competitors.values()) if competitors else 0
            is_best = nicto >= best_comp and nicto > 0
            marker = "*" if is_best else " "
            lines.append(
                f"{bm['benchmark']:<16} {marker}{nicto:>7.1f} "
                f"{bm.get('deepseek_v3', 0):>9.1f} "
                f"{bm.get('gemini_25_pro', 0):>9.1f} "
                f"{bm.get('gpt_4o', 0):>9.1f} "
                f"{bm.get('claude_opus_4_5', 0):>9.1f} "
                f"{best_comp:>8.1f}"
            )
        lines.append("-" * 72)
        s = report["summary"]
        lines.append(f"  Overall: NICTO {s['overall_nicto']} vs Avg Competitor {s['overall_avg_competitor']}")
        lines.append(f"  NICTO leads in: {s['leads_in_x_out_of_y']} benchmarks")
        lines.append("=" * 72)
        return "\n".join(lines)
