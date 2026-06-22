import re
import time
import hashlib
from typing import Any, Callable, Dict, List, Optional, Tuple


class MemoryManager:
    def __init__(self):
        self.reflection_store: List[Dict] = []
        self.consistency_store: Dict[str, List[float]] = {}
        self.performance_store: Dict[str, Dict[str, float]] = {}
        self._max_reflections = 1000

    def store_reflection(self, reflection: Dict) -> None:
        self.reflection_store.append(reflection)
        if len(self.reflection_store) > self._max_reflections:
            self.reflection_store.pop(0)

    def store_performance(self, brain: str, domain: str, metric: str, value: float) -> None:
        key = f"{brain}:{domain}"
        if key not in self.performance_store:
            self.performance_store[key] = {}
        self.performance_store[key][metric] = value

    def store_consistency(self, brain: str, domain: str, score: float) -> None:
        key = f"{brain}:{domain}"
        if key not in self.consistency_store:
            self.consistency_store[key] = []
        self.consistency_store[key].append(score)

    def get_recent_reflections(self, n: int = 50) -> List[Dict]:
        return self.reflection_store[-n:]

    def get_performance(self, brain: str, domain: str) -> Dict[str, float]:
        return self.performance_store.get(f"{brain}:{domain}", {})


class ConsistencyTracker:
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory = memory_manager if memory_manager is not None else MemoryManager()
        self._records: List[Dict] = []

    def logical_coherence(self, chain: List[str]) -> float:
        if not chain:
            return 0.0
        if len(chain) == 1:
            return 1.0

        negation_signal = re.compile(r'\b(not|never|none|nothing|no one|nowhere|neither|nor|without|except|exclude|false|disagree|oppose|deny|refuse|reject)\b', re.IGNORECASE)
        affirmation_signal = re.compile(r'\b(always|all|every|everyone|everything|positive|true|yes|include|contain|support|agree|accept|confirm|affirm)\b', re.IGNORECASE)

        total_checks = 0
        contradictions = 0

        for i in range(len(chain) - 1):
            step_i = chain[i]
            step_j = chain[i + 1]

            neg_i = negation_signal.findall(step_i)
            neg_j = negation_signal.findall(step_j)
            aff_i = affirmation_signal.findall(step_i)
            aff_j = affirmation_signal.findall(step_j)

            nonneg_i = set(re.findall(r'\b[a-zA-Z]\w+\b', step_i.lower())) - {s.lower() for s in neg_i} - {s.lower() for s in aff_i}
            nonneg_j = set(re.findall(r'\b[a-zA-Z]\w+\b', step_j.lower())) - {s.lower() for s in neg_j} - {s.lower() for s in aff_j}

            shared_topics = nonneg_i & nonneg_j
            if len(shared_topics) >= 2:
                total_checks += 1
                if (len(neg_i) > 0 and len(neg_j) == 0 and len(aff_j) > 0):
                    contradictions += 1
                elif (len(neg_j) > 0 and len(neg_i) == 0 and len(aff_i) > 0):
                    contradictions += 1

            for k in range(i + 2, min(len(chain), i + 5)):
                step_k = chain[k]
                neg_k = negation_signal.findall(step_k)
                aff_k = affirmation_signal.findall(step_k)

                nonneg_k = set(re.findall(r'\b[a-zA-Z]\w+\b', step_k.lower())) - {s.lower() for s in neg_k} - {s.lower() for s in aff_k}
                shared_ik = nonneg_i & nonneg_k

                if len(shared_ik) >= 2:
                    total_checks += 1
                    if (len(neg_i) > 0 and len(neg_k) == 0 and len(aff_k) > 0):
                        contradictions += 1
                    elif (len(neg_k) > 0 and len(neg_i) == 0 and len(aff_i) > 0):
                        contradictions += 1

        if total_checks == 0:
            step_overlap = 0.0
            step_pairs = 0
            for i in range(len(chain) - 1):
                words_i = set(re.findall(r'\b[a-zA-Z]\w+\b', chain[i].lower()))
                words_j = set(re.findall(r'\b[a-zA-Z]\w+\b', chain[i + 1].lower()))
                union = words_i | words_j
                if union:
                    step_overlap += len(words_i & words_j) / len(union)
                    step_pairs += 1
            if step_pairs > 0:
                return min(1.0, step_overlap / step_pairs * 2.0)
            return 0.5

        coherence = max(0.0, 1.0 - (contradictions / total_checks))
        return min(1.0, coherence)

    def output_stability(self, task: Dict, brain_func: Callable, n: int = 5) -> float:
        outputs = []
        for i in range(n):
            try:
                result = brain_func(task)
                outputs.append(str(result))
            except Exception:
                outputs.append(f"error_{i}")

        if len(outputs) < 2:
            return 1.0

        ngrams = {}
        for out in outputs:
            words = tuple(re.findall(r'\w+', out.lower()))
            ngrams[words] = ngrams.get(words, 0) + 1

        if len(ngrams) == 1:
            return 1.0

        max_freq = max(ngrams.values())
        dominant_ratio = max_freq / len(outputs)

        pairwise_similarity = 0.0
        pairs = 0
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                if outputs[i] == outputs[j]:
                    pairwise_similarity += 1.0
                else:
                    seq = re.findall(r'\w+', outputs[i].lower())
                    seq_j = re.findall(r'\w+', outputs[j].lower())
                    shared = set(seq) & set(seq_j)
                    union = set(seq) | set(seq_j)
                    if union:
                        jaccard = len(shared) / len(union)
                        pairwise_similarity += jaccard
                    else:
                        pairwise_similarity += 0.0
                pairs += 1

        avg_pairwise = pairwise_similarity / pairs if pairs > 0 else 0.0
        stability = 0.6 * dominant_ratio + 0.4 * avg_pairwise
        return min(1.0, stability)

    def contradiction_count(self, statements: List[str]) -> int:
        if len(statements) < 2:
            return 0

        contradictions = 0
        negation_signal = re.compile(r'\b(not|never|none|nothing|without|except|exclude|false|disagree|oppose|deny|refuse|reject|lack|missing|absent)\b', re.IGNORECASE)
        affirmation_signal = re.compile(r'\b(always|all|every|everyone|everything|positive|true|yes|include|contain|support|agree|accept|confirm|affirm|present|exist|have|has)\b', re.IGNORECASE)
        exclusive_pairs = [
            (r'\bincrease\b', r'\bdecrease\b'),
            (r'\bgreater\b', r'\bsmaller\b'),
            (r'\bhigher\b', r'\blower\b'),
            (r'\bfaster\b', r'\bslower\b'),
            (r'\bmore\b', r'\bless\b'),
            (r'\bwin\b', r'\blose\b'),
            (r'\bsuccess\b', r'\bfailure\b'),
            (r'\bstart\b', r'\bstop\b'),
            (r'\bbegin\b', r'\bend\b'),
            (r'\benable\b', r'\bdisable\b'),
            (r'\bopen\b', r'\bclose\b'),
        ]

        for i in range(len(statements)):
            for j in range(i + 1, len(statements)):
                s_i = statements[i].lower()
                s_j = statements[j].lower()

                neg_i = bool(negation_signal.search(s_i))
                neg_j = bool(negation_signal.search(s_j))
                aff_i = bool(affirmation_signal.search(s_i))
                aff_j = bool(affirmation_signal.search(s_j))

                if neg_i and aff_j:
                    contradictions += 1
                elif neg_j and aff_i:
                    contradictions += 1

                for pat_a, pat_b in exclusive_pairs:
                    has_a_i = bool(re.search(pat_a, s_i))
                    has_b_i = bool(re.search(pat_b, s_i))
                    has_a_j = bool(re.search(pat_a, s_j))
                    has_b_j = bool(re.search(pat_b, s_j))
                    if (has_a_i and has_b_j) or (has_b_i and has_a_j):
                        contradictions += 1

        return contradictions

    def coherence_score(self, chain: List[str]) -> Dict:
        coherence = self.logical_coherence(chain)
        contradictions = self.contradiction_count(chain)

        if len(chain) > 0:
            topic_words = []
            for step in chain:
                words = set(re.findall(r'\b[a-zA-Z]\w+\b', step.lower()))
                topic_words.append(words)
            topic_drift = 0.0
            if len(topic_words) > 1:
                for i in range(len(topic_words) - 1):
                    union = topic_words[i] | topic_words[i + 1]
                    if union:
                        topic_drift += 1.0 - (len(topic_words[i] & topic_words[i + 1]) / len(union))
                topic_drift /= len(topic_words) - 1
        else:
            topic_drift = 0.0

        stability = max(0.0, 1.0 - topic_drift)
        combined = 0.6 * coherence + 0.4 * stability

        return {
            "coherence": round(coherence, 4),
            "contradictions": contradictions,
            "topic_drift": round(topic_drift, 4),
            "stability": round(stability, 4),
            "combined": round(combined, 4),
        }

    def track_consistency(self, brain: str, domain: str, coherence: float, stability: float, contradictions: int) -> None:
        combined = 0.6 * coherence + 0.4 * stability
        record = {
            "timestamp": time.time(),
            "brain": brain,
            "domain": domain,
            "coherence": round(coherence, 4),
            "stability": round(stability, 4),
            "contradictions": contradictions,
            "combined_score": round(combined, 4),
        }
        self._records.append(record)
        self.memory.store_consistency(brain, domain, combined)
        self.memory.store_performance(brain, domain, "coherence", coherence)
        self.memory.store_performance(brain, domain, "stability", stability)

    def get_consistency_report(self, brain: Optional[str] = None, domain: Optional[str] = None) -> Dict:
        filtered = self._records
        if brain is not None:
            filtered = [r for r in filtered if r["brain"] == brain]
        if domain is not None:
            filtered = [r for r in filtered if r["domain"] == domain]

        if not filtered:
            return {
                "records": [],
                "avg_coherence": 0.0,
                "avg_stability": 0.0,
                "avg_combined": 0.0,
                "total_contradictions": 0,
                "filters": {"brain": brain, "domain": domain},
            }

        avg_coherence = sum(r["coherence"] for r in filtered) / len(filtered)
        avg_stability = sum(r["stability"] for r in filtered) / len(filtered)
        avg_combined = sum(r["combined_score"] for r in filtered) / len(filtered)
        total_contradictions = sum(r["contradictions"] for r in filtered)

        return {
            "records": filtered,
            "avg_coherence": round(avg_coherence, 4),
            "avg_stability": round(avg_stability, 4),
            "avg_combined": round(avg_combined, 4),
            "total_contradictions": total_contradictions,
            "num_records": len(filtered),
            "filters": {"brain": brain, "domain": domain},
        }
