"""NIKTO Dream Steerer — Latent-space thought augmentation via dream patterns."""

import json
import math
import random
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class DreamPattern:
    """A single dream pattern that can steer thinking."""
    def __init__(self, name: str, description: str, mode: str,
                 vector: list = None, tags: list = None,
                 strength: float = 0.5, metadata: dict = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.description = description
        self.mode = mode  # directive, explorative, consolidative, creative, corrective
        self.vector = vector or [random.uniform(-1, 1) for _ in range(64)]
        self.tags = tags or []
        self.strength = max(0.0, min(1.0, strength))
        self.created = datetime.now(timezone.utc).isoformat()
        self.usage_count = 0
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class DreamSession:
    """A recorded dream session."""
    def __init__(self, input_text: str, mode: str, patterns_applied: list,
                 output: str, coherence: float = 0.5):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.input_text = input_text
        self.mode = mode
        self.patterns_applied = patterns_applied
        self.output = output
        self.coherence = coherence
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoDreamSteerer:
    """
    Dream Steerer — augments thoughts by projecting into latent dream space
    and applying learned steering patterns.
    """

    STEERING_MODES = {
        "directive": "Focus thought toward a specific goal or conclusion",
        "explorative": "Branch out into adjacent conceptual spaces",
        "consolidative": "Reinforce and integrate existing knowledge",
        "creative": "Generate novel combinations and unexpected connections",
        "corrective": "Identify and repair contradictions or gaps",
    }

    def __init__(self, latent_dim: int = 64):
        self.latent_dim = latent_dim
        self.patterns = {}  # name -> DreamPattern
        self.sessions = []
        self.max_sessions = 500
        self._init_default_patterns()

    # ── Default Dream Patterns ────────────────────────────────────────

    def _init_default_patterns(self):
        defaults = [
            ("analytical_focus", "Sharpen analytical reasoning by pruning irrelevant branches",
             "directive", ["logic", "analysis", "precision"], 0.7),
            ("lateral_exploration", "Explore adjacent concepts for novel insights",
             "explorative", ["creativity", "breadth", "analogy"], 0.6),
            ("memory_integration", "Bind recent experiences into stable long-term patterns",
             "consolidative", ["memory", "learning", "stability"], 0.8),
            ("contradiction_resolution", "Detect and resolve logical contradictions",
             "corrective", ["logic", "consistency", "repair"], 0.75),
            ("novel_synthesis", "Combine unrelated concepts into new ideas",
             "creative", ["novelty", "combination", "emergence"], 0.65),
            ("pattern_completion", "Fill in missing pieces from partial information",
             "directive", ["pattern", "completion", "inference"], 0.6),
            ("abductive_leap", "Generate best explanations from sparse evidence",
             "explorative", ["abduction", "explanation", "leap"], 0.55),
            ("emotional_integration", "Weave emotional valence into reasoning",
             "consolidative", ["emotion", "valence", "integration"], 0.5),
            ("counterfactual_branch", "Explore what-if scenarios and alternative paths",
             "creative", ["counterfactual", "branching", "possibility"], 0.7),
            ("self_correction_loop", "Critique own output and refine iteratively",
             "corrective", ["self", "critique", "refinement"], 0.8),
            ("goal_alignment", "Steer thoughts toward primary objectives",
             "directive", ["goal", "alignment", "purpose"], 0.9),
            ("curiosity_drive", "Generate questions and knowledge gaps to explore",
             "explorative", ["curiosity", "questions", "gaps"], 0.6),
            ("temporal_binding", "Connect past, present, and future across timescales",
             "consolidative", ["time", "binding", "narrative"], 0.55),
            ("abstraction_ladder", "Move between concrete and abstract representations",
             "creative", ["abstraction", "ladder", "hierarchy"], 0.65),
            ("ambiguity_tolerance", "Hold multiple interpretations without premature closure",
             "corrective", ["ambiguity", "tolerance", "openness"], 0.5),
        ]
        for name, desc, mode, tags, strength in defaults:
            self.patterns[name] = DreamPattern(name, desc, mode, tags=tags, strength=strength)

    # ── Latent Space Operations ───────────────────────────────────────

    def _project_to_latent(self, text: str) -> list:
        """Project text into latent space vector."""
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        if HAS_NUMPY:
            vec = np.array([rng.uniform(-1, 1) for _ in range(self.latent_dim)])
            vec = vec / (np.linalg.norm(vec) + 1e-8)
            return vec.tolist()
        vec = [rng.uniform(-1, 1) for _ in range(self.latent_dim)]
        norm = math.sqrt(sum(v*v for v in vec)) + 1e-8
        return [v / norm for v in vec]

    def _latent_similarity(self, v1: list, v2: list) -> float:
        if HAS_NUMPY:
            a, b = np.array(v1), np.array(v2)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
        dot = sum(a*b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a*a for a in v1)) + 1e-8
        n2 = math.sqrt(sum(b*b for b in v2)) + 1e-8
        return dot / (n1 * n2)

    def _apply_pattern_to_vector(self, vec: list, pattern: DreamPattern,
                                  intensity: float = 1.0) -> list:
        """Blend a dream pattern vector into the latent vector."""
        alpha = pattern.strength * intensity * 0.3
        if HAS_NUMPY:
            v = np.array(vec)
            p = np.array(pattern.vector)
            blended = v * (1 - alpha) + p * alpha
            blended = blended / (np.linalg.norm(blended) + 1e-8)
            return blended.tolist()
        blended = [v * (1 - alpha) + p * alpha
                   for v, p in zip(vec, pattern.vector)]
        norm = math.sqrt(sum(x*x for x in blended)) + 1e-8
        return [x / norm for x in blended]

    # ── Core Steer Method ─────────────────────────────────────────────

    def steer(self, prompt: str, mode: str = "directive",
              intensity: float = 1.0, context: dict = None) -> dict:
        """
        Steer a thought through dream space.
        Returns augmented thought with pattern applications and coherence score.
        """
        context = context or {}
        if mode not in self.STEERING_MODES:
            mode = "directive"

        latent = self._project_to_latent(prompt)
        candidates = [p for p in self.patterns.values() if p.mode == mode]
        if not candidates:
            candidates = list(self.patterns.values())

        patterns_to_apply = context.get("patterns", candidates)
        applied = []
        current_vec = latent[:]

        for pat in patterns_to_apply:
            if pat not in candidates:
                continue
            sim = self._latent_similarity(current_vec, pat.vector)
            if sim < -0.8:
                continue  # too opposing
            current_vec = self._apply_pattern_to_vector(current_vec, pat, intensity)
            pat.usage_count += 1
            applied.append(pat.name)

        coherence = self._compute_coherence(current_vec, latent)
        output = self._vector_to_text(current_vec, prompt, applied, mode)

        session = DreamSession(prompt, mode, applied, output, coherence)
        self.sessions.append(session)
        if len(self.sessions) > self.max_sessions:
            self.sessions = self.sessions[-self.max_sessions:]

        return {
            "input": prompt,
            "mode": mode,
            "patterns_applied": applied,
            "coherence": round(coherence, 4),
            "output": output,
            "session_id": session.id,
        }

    def _compute_coherence(self, vec: list, original: list) -> float:
        sim = self._latent_similarity(vec, original)
        return max(0.0, min(1.0, (sim + 1) / 2))

    def _vector_to_text(self, vec: list, prompt: str,
                        patterns: list, mode: str) -> str:
        """Generate a textual description of the steered thought."""
        seed = int(sum(vec[:4]) * 10000) % 1000
        rng = random.Random(seed + len(patterns))

        mode_verbs = {
            "directive": ["focused", "targeted", "aligned", "sharpened"],
            "explorative": ["broadened", "expanded", "diverged", "explored"],
            "consolidative": ["integrated", "reinforced", "consolidated", "bound"],
            "creative": ["transformed", "recombined", "generated", "synthesized"],
            "corrective": ["corrected", "resolved", "repaired", "clarified"],
        }
        verbs = mode_verbs.get(mode, ["processed"])
        verb = rng.choice(verbs)

        pattern_names = [p.replace("_", " ") for p in patterns[:3]]
        pattern_desc = f" via {', '.join(pattern_names)}" if pattern_names else ""

        snippets = [
            f"Dream-steered ({mode}): {prompt[:100]} — {verb}{pattern_desc}.",
            f"Latent projection applied {len(patterns)} pattern(s) "
            f"in {mode} mode to augment: '{prompt[:80]}'.",
            f"Steering result [{mode}]: Original '{prompt[:60]}' → "
            f"{verb} through {len(patterns)} dream patterns.",
        ]
        return rng.choice(snippets)

    # ── Dream Replay for Memory Consolidation ───────────────────────

    def dream_replay(self, memories: list, top_k: int = 5) -> list:
        """
        Replay important memories through dream patterns for consolidation.
        memories: list of dicts with 'content', 'importance', 'tags'
        Returns list of steered consolidations.
        """
        sorted_mem = sorted(memories, key=lambda m: m.get("importance", 0), reverse=True)
        results = []
        for mem in sorted_mem[:top_k]:
            result = self.steer(
                mem.get("content", ""),
                mode="consolidative",
                intensity=mem.get("importance", 0.5) * 0.8 + 0.2,
                context={"patterns": self.get_patterns_by_mode("consolidative")},
            )
            results.append(result)
        return results

    # ── Pattern Management ────────────────────────────────────────────

    def add_pattern(self, name: str, description: str, mode: str,
                    vector: list = None, tags: list = None,
                    strength: float = 0.5) -> DreamPattern:
        if mode not in self.STEERING_MODES:
            raise ValueError(f"Invalid mode: {mode}. Choose from {list(self.STEERING_MODES.keys())}")
        pat = DreamPattern(name, description, mode, vector, tags, strength)
        self.patterns[name] = pat
        return pat

    def remove_pattern(self, name: str):
        self.patterns.pop(name, None)

    def get_pattern(self, name: str) -> Optional[dict]:
        pat = self.patterns.get(name)
        return pat.to_dict() if pat else None

    def get_patterns_by_mode(self, mode: str) -> list:
        return [p for p in self.patterns.values() if p.mode == mode]

    def list_patterns(self) -> list:
        return [p.to_dict() for p in self.patterns.values()]

    # ── Statistics ─────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        total_uses = sum(p.usage_count for p in self.patterns.values())
        return {
            "total_patterns": len(self.patterns),
            "total_sessions": len(self.sessions),
            "total_pattern_uses": total_uses,
            "modes": {m: len(self.get_patterns_by_mode(m)) for m in self.STEERING_MODES},
            "latent_dim": self.latent_dim,
            "has_numpy": HAS_NUMPY,
        }

    # ── Serialization ──────────────────────────────────────────────────

    def save(self) -> dict:
        return {
            "patterns": {n: p.to_dict() for n, p in self.patterns.items()},
            "sessions": [s.to_dict() for s in self.sessions[-100:]],
            "latent_dim": self.latent_dim,
        }

    def load(self, data: dict):
        self.latent_dim = data.get("latent_dim", 64)
        self.patterns = {}
        for name, pd in data.get("patterns", {}).items():
            p = DreamPattern(pd.get("name", name), pd.get("description", ""),
                             pd.get("mode", "directive"))
            p.__dict__.update(pd)
            self.patterns[name] = p
        self.sessions = []
        for sd in data.get("sessions", []):
            s = DreamSession(sd.get("input_text", ""), sd.get("mode", "directive"),
                             sd.get("patterns_applied", []), sd.get("output", ""))
            s.__dict__.update(sd)
            self.sessions.append(s)
