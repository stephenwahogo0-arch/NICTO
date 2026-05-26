import uuid


class PatternDiscoveryEngine:
    MIN_FREQUENCY = 3

    def __init__(self, cross_session_memory=None, elo_system=None):
        self.memory = cross_session_memory
        self.elo = elo_system
        self._discovered_patterns = []
        self._cross_domain_links = {}

    def discover(self):
        patterns = []
        trends = self._analyze_elo_trends()
        patterns.extend(trends)
        question_patterns = self._find_question_patterns()
        patterns.extend(question_patterns)
        cross_domain = self._find_cross_domain_links()
        patterns.extend(cross_domain)
        for pattern in patterns:
            if pattern.get("confidence", 0) > 0.7:
                self._discovered_patterns.append(pattern)
                if self.memory:
                    self.memory.store_insight(
                        insight_id=pattern.get("id", str(uuid.uuid4())[:8]),
                        insight=pattern.get("description", ""),
                        domain=pattern.get("domain", "general"),
                        strength=pattern.get("confidence", 0.5),
                    )
        return patterns

    def _analyze_elo_trends(self):
        if not self.elo:
            return []
        trends = []
        for domain in ["cybersecurity", "programming", "mathematics"]:
            history = self.elo.get_history("analytical", domain, 20)
            if len(history) >= 5:
                recent_ratings = [h[1] for h in history[-5:]]
                slope = (recent_ratings[-1] - recent_ratings[0]) / 5
                if slope > 5:
                    trends.append({
                        "id": f"elo_trend_{domain}", "type": "elo_improving",
                        "domain": domain,
                        "description": f"ELO improving in {domain}: +{slope:.1f}/check",
                        "confidence": 0.85,
                    })
                elif slope < -5:
                    trends.append({
                        "id": f"elo_decline_{domain}", "type": "elo_declining",
                        "domain": domain,
                        "description": f"ELO declining in {domain}: {slope:.1f}/check",
                        "confidence": 0.85,
                    })
        return trends

    def _find_question_patterns(self):
        if not self.memory:
            return []
        facts = self.memory.recall_facts(limit=100)
        type_counts = {}
        for fact in facts:
            domain = fact.get("domain", "general")
            type_counts[domain] = type_counts.get(domain, 0) + 1
        patterns = []
        for domain, count in type_counts.items():
            if count >= self.MIN_FREQUENCY:
                patterns.append({
                    "id": f"freq_{domain}", "type": "frequent_domain",
                    "domain": domain,
                    "description": f"Domain '{domain}' appears {count}x in memory",
                    "confidence": min(0.95, count / 10), "frequency": count,
                })
        return patterns

    def _find_cross_domain_links(self):
        if not self.elo:
            return []
        links = []
        domain_pairs = [
            ("cybersecurity", "programming"),
            ("mathematics", "reasoning"),
            ("strategy", "knowledge"),
        ]
        for d1, d2 in domain_pairs:
            elo1 = self.elo.get_rating("analytical", d1)
            elo2 = self.elo.get_rating("analytical", d2)
            correlation = 1.0 - abs(elo1 - elo2) / 400
            if correlation > 0.8:
                links.append({
                    "id": f"link_{d1}_{d2}", "type": "domain_correlation",
                    "domain": d1, "linked_domain": d2,
                    "description": f"Strong correlation between {d1} and {d2} performance (r={correlation:.2f})",
                    "confidence": correlation,
                })
        return links

    def get_insights(self):
        return self._discovered_patterns[-20:]
