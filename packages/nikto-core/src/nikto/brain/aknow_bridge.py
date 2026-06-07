import json
import sys
import os
import time
import math
from typing import Dict, List, Tuple, Optional, Any

_AKNOW_LOADED = False
_AKNOW_ROOT = r"C:\Users\BYU\Desktop\AKNOW##"
_Spider = None
_KnowledgeCultivator = None
_GrammarEngine = None
_SkillLibrary = None
_ThinkEngine = None
_AKNLib = None

try:
    if _AKNOW_ROOT not in sys.path:
        sys.path.insert(0, _AKNOW_ROOT)
    _sdk = os.path.join(_AKNOW_ROOT, "sdk")
    if _sdk not in sys.path:
        sys.path.insert(0, _sdk)
    import aknow as _aknow
    from rosetta import NeuralRosetta
    from aknow_omega import (
        GenesisCore, HyperDomainTree, FutureSocket, Hydra,
        Spider, KnowledgeCultivator, GrammarEngine,
        SkillLibrary, ThinkEngine, AKNLib,
    )
    _AKNOW_LOADED = True
except ImportError:
    NeuralRosetta = None
    GenesisCore = None
    HyperDomainTree = None
    FutureSocket = None
    Hydra = None

PHI = 1.6180339887498948482045868343656
MAX_STREAM_BYTES = 10_000_000


class AknowBridge:
    def __init__(self, depth: int = 128, mode: str = "full"):
        self.depth = depth
        self.mode = mode
        self._loaded = _AKNOW_LOADED
        self._genesis: Optional[GenesisCore] = None
        self._atlas: Optional[HyperDomainTree] = None
        self._rosetta: Optional[NeuralRosetta] = None
        self._socket: Optional[FutureSocket] = None
        self._hydra: Optional[Hydra] = None
        self._spider: Optional[Any] = None
        self._cultivator: Optional[Any] = None
        self._grammar: Optional[Any] = None
        self._skills: Optional[Any] = None
        self._think: Optional[Any] = None
        self._aknlib: Optional[Any] = None
        self._seed_store: Dict[str, int] = {}
        self._init_time = time.time()
        self._stats = {"expansions": 0, "total_bytes": 0, "errors": 0, "web_fetches": 0, "skills_discovered": 0}
        if self._loaded:
            self._init_engines()

    def _init_engines(self):
        self._genesis = GenesisCore()
        self._atlas = HyperDomainTree()
        self._rosetta = NeuralRosetta()
        self._socket = FutureSocket()
        self._hydra = Hydra()

    def _lazy_spider(self):
        if self._spider is None and self._loaded:
            self._spider = Spider()
        return self._spider

    def _lazy_cultivator(self):
        if self._cultivator is None and self._loaded:
            self._cultivator = KnowledgeCultivator()
        return self._cultivator

    def _lazy_grammar(self):
        if self._grammar is None and self._loaded:
            self._grammar = GrammarEngine(self._atlas)
        return self._grammar

    def _lazy_skills(self):
        if self._skills is None and self._loaded:
            self._skills = SkillLibrary()
        return self._skills

    def _lazy_think(self):
        if self._think is None and self._loaded:
            self._think = ThinkEngine()
        return self._think

    def _lazy_aknlib(self):
        if self._aknlib is None and self._loaded:
            self._aknlib = AKNLib()
        return self._aknlib

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # === CORE ===

    def expand_knowledge(self, topic: str, sentences: int = 5) -> str:
        if not self._loaded:
            return self._fallback_text(topic)
        seed = self._genesis.hash_to_seed(topic)
        grammar = self._lazy_grammar()
        text = grammar.generate(seed=seed, length=sentences * 2) if grammar else ""
        self._stats["expansions"] += 1
        self._stats["total_bytes"] += len(text.encode("utf-8"))
        return text

    def expand_seed_bytes(self, seed: int, depth: Optional[int] = None) -> bytes:
        if not self._loaded:
            return b""
        d = depth or self.depth
        raw = _aknow.expand_seed(seed, d)
        self._stats["expansions"] += 1
        self._stats["total_bytes"] += len(raw)
        return raw

    def decode_bytes(self, data: bytes) -> str:
        if not self._loaded or self._rosetta is None:
            return ""
        return self._rosetta.bytes_to_text(data)

    def seed_for_topic(self, topic: str) -> int:
        if not self._loaded or self._genesis is None:
            return hash(topic) & ((1 << 64) - 1)
        return self._genesis.hash_to_seed(topic)

    def resolve_domain(self, seed: int) -> Tuple[str, str]:
        if not self._loaded or self._atlas is None:
            return "general", "General"
        domain_name, info = self._atlas.resolve(seed)
        return domain_name, info.get("family", "General")

    def generate_context(self, query: str, max_words: int = 600) -> Dict[str, Any]:
        if not self._loaded:
            return {"domain": "unknown", "seed": 0, "context": "", "available": False}
        seed = self.seed_for_topic(query)
        domain, family = self.resolve_domain(seed)
        grammar = self._lazy_grammar()
        grammar_text = grammar.generate(seed=seed, length=30) if grammar else ""
        expanded = self.expand_seed_bytes(seed)
        decoded = self._rosetta.bytes_to_text(expanded) if expanded and self._rosetta else ""
        text = grammar_text or decoded
        words = text.split()
        if len(words) > max_words:
            text = " ".join(words[:max_words])
        return {
            "domain": domain,
            "family": family,
            "seed": seed,
            "seed_hex": f"{seed:#018x}",
            "context": text,
            "word_count": len(text.split()),
            "available": True,
            "decoded_from_seed": bool(expanded),
            "grammar_generated": bool(grammar_text),
        }

    def list_domains(self) -> List[Dict[str, Any]]:
        if not self._loaded or self._atlas is None:
            return []
        families = self._atlas.families()
        results = []
        for family_name, domain_names in families.items():
            for name in domain_names:
                results.append({"name": name, "family": family_name})
        return results

    def families(self) -> Dict[str, List[str]]:
        if not self._loaded or self._atlas is None:
            return {}
        return self._atlas.families()

    def verify_determinism(self, seed: int = 999999, samples: int = 3) -> bool:
        if not self._loaded or self._genesis is None:
            return False
        return self._genesis.verify_determinism(seed, samples)

    def benchmark(self, iterations: int = 50) -> Dict[str, float]:
        if not self._loaded:
            return {"error": "AKNOW# not loaded"}
        seeds = [i * 9973 for i in range(iterations)]
        grammar = self._lazy_grammar()
        start = time.perf_counter()
        for s in seeds:
            if grammar:
                grammar.generate(seed=s, length=5)
        elapsed = time.perf_counter() - start
        return {
            "iterations": iterations,
            "total_seconds": round(elapsed, 4),
            "avg_ms": round(elapsed / iterations * 1000, 4),
            "per_second": round(iterations / elapsed, 1),
        }

    def parallel_expand(self, count: int = 10) -> str:
        if not self._loaded or self._hydra is None:
            return "AKNOW# not loaded"
        self._hydra.launch(count)
        return self._hydra.report()

    def platform_report(self) -> str:
        if not self._loaded or self._socket is None:
            return "AKNOW# not loaded"
        return self._socket.report()

    # === NEW: SPIDER (Web Intelligence) ===

    def web_fetch(self, url: str) -> str:
        sp = self._lazy_spider()
        if not sp:
            return ""
        self._stats["web_fetches"] += 1
        return sp.fetch_text(url)

    def web_layers(self) -> Dict[int, str]:
        sp = self._lazy_spider()
        if not sp:
            return {}
        return sp.LAYER_NAMES

    def web_harvest(self, urls: List[str]) -> str:
        sp = self._lazy_spider()
        if not sp:
            return ""
        results = []
        for url in urls[:5]:
            text = sp.fetch_text(url)
            if text:
                results.append(f"[{url}]: {text[:200]}")
            self._stats["web_fetches"] += 1
        return "\n".join(results)

    # === NEW: KNOWLEDGE CULTIVATOR ===

    def extract_keywords(self, text: str) -> List[str]:
        kc = self._lazy_cultivator()
        if not kc:
            return []
        return kc.extract_keywords(text)

    def classify_text(self, text: str) -> str:
        kc = self._lazy_cultivator()
        if not kc:
            return "general"
        return kc.classify(text)

    def compress_to_seed(self, text: str) -> int:
        kc = self._lazy_cultivator()
        if not kc:
            return hash(text) & ((1 << 64) - 1)
        return kc.compress_to_seed(text)

    def expand_from_seed(self, seed: int, length: int = 50) -> str:
        kc = self._lazy_cultivator()
        if not kc:
            return ""
        return kc.expand_from_seed(seed, length)

    def cultivate_knowledge(self, text: str) -> Dict[str, Any]:
        kc = self._lazy_cultivator()
        if not kc:
            return {}
        return kc.cultivate(text)

    # === NEW: GRAMMAR ENGINE ===

    def grammar_generate(self, seed: int, length: int = 10) -> str:
        gr = self._lazy_grammar()
        if not gr:
            return ""
        return gr.generate(seed=seed, length=length)

    # === NEW: SKILL LIBRARY ===

    def discover_skills(self, query: str, layers: int = 4, max_results: int = 5) -> Any:
        sk = self._lazy_skills()
        if not sk:
            return []
        result = sk.discover(query, layers=layers, max_skills=max_results)
        self._stats["skills_discovered"] += 1
        return result

    def skill_layers(self) -> List[str]:
        sk = self._lazy_skills()
        if not sk:
            return []
        return sk.LAYER_NAMES

    def compose_skills(self, seeds: List[int]) -> str:
        sk = self._lazy_skills()
        if not sk:
            return ""
        return sk.compose(seeds)

    def fetch_skill(self, seed: int) -> str:
        sk = self._lazy_skills()
        if not sk:
            return ""
        return str(sk.fetch(seed))

    # === NEW: THINK ENGINE ===

    def think_explain(self, topic: str) -> str:
        th = self._lazy_think()
        if not th:
            return ""
        try:
            seed = self._genesis.hash_to_seed(topic) if self._genesis else hash(topic)
            return th.explain(seed)
        except Exception:
            return f"[ThinkEngine] Could not explain '{topic}'"

    def think_ask(self, question: str) -> str:
        th = self._lazy_think()
        if not th:
            return ""
        try:
            return th.ask(question)
        except Exception:
            return f"[ThinkEngine] Could not answer '{question}'"

    def think_history(self) -> List[str]:
        th = self._lazy_think()
        if not th:
            return []
        try:
            return th.history()
        except Exception:
            return []

    # === NEW: AKNLIB ===

    def akn_compare(self, a: str, b: str) -> str:
        lib = self._lazy_aknlib()
        if not lib:
            return ""
        try:
            return lib.compare(a, b)
        except Exception:
            return f"Compare({a}, {b}) not available"

    def akn_crypto(self, data: str, mode: str = "hash") -> str:
        lib = self._lazy_aknlib()
        if not lib:
            return ""
        return str(lib.crypto(mode, data))

    def akn_eyes(self) -> str:
        lib = self._lazy_aknlib()
        if not lib:
            return ""
        return str(lib.eyes())

    # === UTILITY ===

    def store_seed(self, key: str, seed: int):
        self._seed_store[key] = seed

    def get_stored_seed(self, key: str) -> Optional[int]:
        return self._seed_store.get(key)

    def seed_count(self) -> int:
        return len(self._seed_store)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "mode": self.mode,
            "depth": self.depth,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "expansions": self._stats["expansions"],
            "total_bytes": self._stats["total_bytes"],
            "errors": self._stats["errors"],
            "web_fetches": self._stats["web_fetches"],
            "skills_discovered": self._stats["skills_discovered"],
            "domains_available": len(self.list_domains()),
            "seeds_stored": self.seed_count(),
            "families": list(self.families().keys()),
            "engines": {
                "genesis": self._genesis is not None,
                "atlas": self._atlas is not None,
                "rosetta": self._rosetta is not None,
                "socket": self._socket is not None,
                "hydra": self._hydra is not None,
                "spider": self._spider is not None,
                "cultivator": self._cultivator is not None,
                "grammar": self._grammar is not None,
                "skills": self._skills is not None,
                "think": self._think is not None,
                "aknlib": self._aknlib is not None,
                "lazy_spider": self._spider is None,
                "lazy_cultivator": self._cultivator is None,
                "lazy_grammar": self._grammar is None,
                "lazy_skills": self._skills is None,
                "lazy_think": self._think is None,
                "lazy_aknlib": self._aknlib is None,
            },
            "phi": PHI,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "aknow_loaded": self._loaded,
            "mode": self.mode,
            "depth": self.depth,
            "expansions": self._stats["expansions"],
            "domains": len(self.list_domains()),
            "seeds_stored": self.seed_count(),
            "web_fetches": self._stats["web_fetches"],
            "skills_discovered": self._stats["skills_discovered"],
        }

    def save(self) -> dict:
        return {
            "seed_store": self._seed_store,
            "stats": self._stats,
            "depth": self.depth,
            "mode": self.mode,
        }

    def load(self, data: dict):
        self._seed_store = data.get("seed_store", {})
        self._stats = data.get("stats", {"expansions": 0, "total_bytes": 0, "errors": 0, "web_fetches": 0, "skills_discovered": 0})
        self.depth = data.get("depth", self.depth)
        self.mode = data.get("mode", self.mode)

    @staticmethod
    def _fallback_text(topic: str) -> str:
        seed = hash(topic) & ((1 << 64) - 1)
        rng = __import__("random").Random(seed)
        nouns = ["knowledge", "system", "seed", "determinism", "expansion", "phi", "golden-ratio", "chaos", "order", "complexity"]
        verbs = ["generates", "expands", "recurses", "converges", "stabilizes"]
        adjs = ["deterministic", "chaotic", "recursive", "golden", "infinite"]
        words = [rng.choice(nouns + verbs + adjs) for _ in range(30)]
        text = " ".join(words)
        return f"[Fallback] The {rng.choice(adjs)} {rng.choice(nouns)} {rng.choice(verbs)}.\n{text[:1].upper() + text[1:]}."
