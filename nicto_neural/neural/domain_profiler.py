from typing import Optional


class DomainProfiler:
    DOMAINS = {
        "cybersecurity": {"description": "Penetration testing, CVEs, exploits", "target_elo": 1800},
        "programming": {"description": "All languages, frameworks, patterns", "target_elo": 1750},
        "mathematics": {"description": "Algebra, calculus, statistics, proofs", "target_elo": 1700},
        "reasoning": {"description": "Logic, inference, problem solving", "target_elo": 1750},
        "knowledge": {"description": "Facts, history, science, general", "target_elo": 1650},
        "creative": {"description": "Writing, ideation, design", "target_elo": 1600},
        "strategy": {"description": "Planning, architecture, decisions", "target_elo": 1700},
        "language": {"description": "Grammar, translation, linguistics", "target_elo": 1650},
    }

    def __init__(self, elo_system=None):
        self.elo = elo_system
        self._accuracy = {d: [] for d in self.DOMAINS}
        self._response_times = {d: [] for d in self.DOMAINS}

    def record(self, domain, accuracy, response_time_ms=0.0):
        if domain in self._accuracy:
            self._accuracy[domain].append(accuracy)
            self._accuracy[domain] = self._accuracy[domain][-100:]
        if domain in self._response_times:
            self._response_times[domain].append(response_time_ms)
            self._response_times[domain] = self._response_times[domain][-100:]

    def get_profile(self, domain: Optional[str] = None):
        if domain and domain in self.DOMAINS:
            return self._domain_profile(domain)
        profile = {}
        for d in self.DOMAINS:
            profile[d] = self._domain_profile(d)
        return {
            "domains": profile,
            "strongest": max(profile, key=lambda d: profile[d]["elo"]) if profile else "none",
            "weakest": min(profile, key=lambda d: profile[d]["elo"]) if profile else "none",
        }

    def _domain_profile(self, domain):
        if domain not in self.DOMAINS:
            return {"accuracy": 0.0, "elo": 0.0, "grade": "N/A"}
        info = self.DOMAINS[domain]
        acc_list = self._accuracy.get(domain, [])
        avg_acc = sum(acc_list) / len(acc_list) if acc_list else 0.0
        elo = self.elo.get_rating("analytical", domain) if self.elo else 1200.0
        time_list = self._response_times.get(domain, [])
        avg_time = sum(time_list) / len(time_list) if time_list else 0.0
        trend = "no_data"
        if len(acc_list) >= 5:
            recent = acc_list[-5:]
            if recent[-1] > recent[0] + 0.02:
                trend = "improving"
            elif recent[-1] < recent[0] - 0.02:
                trend = "degrading"
            else:
                trend = "stable"
        return {
            "description": info["description"],
            "accuracy": round(avg_acc, 4),
            "elo": round(elo, 1),
            "target_elo": info["target_elo"],
            "elo_gap": round(info["target_elo"] - elo, 1),
            "avg_response_ms": round(avg_time, 1),
            "samples": len(acc_list),
            "trend": trend,
            "grade": self._grade(avg_acc, elo),
        }

    def _grade(self, accuracy, elo):
        combined = accuracy * 0.5 + min(1.0, elo / 2000) * 0.5
        if combined >= 0.90: return "S"
        if combined >= 0.85: return "A+"
        if combined >= 0.80: return "A"
        if combined >= 0.75: return "B+"
        if combined >= 0.70: return "B"
        if combined >= 0.60: return "C"
        return "D"

    def compare_to_competitors(self):
        COMPETITOR_SCORES = {
            "deepseek_v3": {"cybersecurity": 0.72, "programming": 0.91, "mathematics": 0.88, "reasoning": 0.87, "knowledge": 0.81, "creative": 0.74, "strategy": 0.79, "language": 0.82},
            "gemini_25_pro": {"cybersecurity": 0.75, "programming": 0.88, "mathematics": 0.87, "reasoning": 0.89, "knowledge": 0.86, "creative": 0.80, "strategy": 0.82, "language": 0.85},
            "gpt4o": {"cybersecurity": 0.74, "programming": 0.87, "mathematics": 0.85, "reasoning": 0.88, "knowledge": 0.85, "creative": 0.82, "strategy": 0.83, "language": 0.86},
            "claude_opus45": {"cybersecurity": 0.77, "programming": 0.89, "mathematics": 0.86, "reasoning": 0.91, "knowledge": 0.87, "creative": 0.85, "strategy": 0.86, "language": 0.88},
        }
        nicto_profile = self.get_profile()
        comparison = {}
        for domain in self.DOMAINS:
            nicto_score = nicto_profile.get("domains", {}).get(domain, {}).get("accuracy", 0.0)
            if isinstance(nicto_profile, dict) and "domains" not in nicto_profile:
                nicto_score = nicto_profile.get(domain, {}).get("accuracy", 0.0)
            domain_comparison = {"nicto": nicto_score}
            for competitor, scores in COMPETITOR_SCORES.items():
                comp_score = scores.get(domain, 0.0)
                domain_comparison[competitor] = comp_score
                domain_comparison[f"nicto_vs_{competitor}"] = nicto_score - comp_score
            domain_comparison["nicto_leads"] = all(
                nicto_score >= scores.get(domain, 0.0) for scores in COMPETITOR_SCORES.values()
            )
            comparison[domain] = domain_comparison
        return comparison
