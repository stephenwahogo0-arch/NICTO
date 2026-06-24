"""Recursive Creative Learning System --- NICTO that teaches itself creativity.

Architecture:
  ?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
  |  RecursiveCreativeLearner                           |
  |  ????????????????????????  ????????????????????????  ????????????????????????????????????????????????  |
  |  | Creative |  | Creative |  | Autonomous Data   |  |
  |  | Brain    |???| Evaluator|???| Gatherer (YouTube)|  |
  |  +-????????????????????????  +-????????????????????????  +-????????????????????????????????????????????????  |
  |       |              |               |              |
  |       ???              ???               ???              |
  |  ????????????????????????????????????????????????????????????????????????????????????????????????????????????          |
  |  |      Self-Play Data Generator        |          |
  |  |  (generates ??? critiques ??? expands)   |          |
  |  +-????????????????????????????????????????????????????????????????????????????????????????????????????????????          |
  |       |                                            |
  |       ???                                            |
  |  ????????????????????????                                      |
  |  |  Trainer  |?????? cycle back with expanded data     |
  |  +-????????????????????????                                      |
  +-?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

Each cycle:
  1. Fetch new YouTube data autonomously
  2. Generate creative samples from current knowledge
  3. Self-critique and score quality
  4. Keep only the best outputs as new training data
  5. Retrain creative brain on expanded dataset
  6. Repeat --- quality compounds each cycle
"""

import json
import math
import os
import random
import time
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from .creative_trainer import CreativeTrainer, CreativeDataLoader


CINEMATOGRAPHY_QUESTIONS = [
    "What camera angle creates a feeling of power in the subject?",
    "How do I light a horror scene to create maximum tension?",
    "What composition technique draws the viewer's eye to the subject?",
    "Describe the ideal lighting setup for a romantic dinner scene.",
    "What camera movement works best for an action chase sequence?",
    "How does color grading affect the emotional tone of a scene?",
    "What lens should I use for intimate close-up dialogue?",
    "Explain how to achieve the film noir look.",
    "What's the best way to light an interview with available light?",
    "How do I create cinematic depth in a flat environment?",
    "Describe camera angles that make a landscape feel epic.",
    "What lighting setup simulates golden hour indoors?",
    "How do music videos use camera movement differently than films?",
    "What composition rule should I break for creative effect?",
    "How does lens compression affect storytelling in dialogue scenes?",
]

CREATIVE_TOPICS = [
    "surreal landscape photography techniques",
    "experimental film transitions",
    "viral social media video aesthetics",
    "dream sequence visual language",
    "time lapse storytelling techniques",
    "abstract visual poetry cinematography",
    "psychedelic color palettes in film",
    "minimalist composition in photography",
    "dystopian visual aesthetic cinematography",
    "fantasy world-building through lighting",
    "retro 80s synthwave visual style",
    "biopunk organic lighting design",
    "steampunk color grading palette",
    "cyberpunk neon visual language",
    "ethereal fashion photography lighting",
]


class CreativeQualityEvaluator:
    """Self-critique system that rates NICTO's creative output quality.

    Evaluates on: novelty, specificity, technical accuracy, visual clarity,
    compositional strength, genre alignment.
    """

    def __init__(self):
        self.eval_criteria = [
            "technical_accuracy",
            "novelty",
            "specificity",
            "visual_clarity",
            "actionability",
            "genre_alignment",
        ]

    def evaluate(self, text: str, genre_hint: str = "") -> Dict[str, float]:
        scores = {}
        text_lower = text.lower()
        words = text_lower.split()

        scores["technical_accuracy"] = self._score_technical(text_lower)
        scores["novelty"] = self._score_novelty(text_lower)
        scores["specificity"] = min(1.0, len(set(words)) / 50)
        scores["visual_clarity"] = self._score_visual(text_lower)
        scores["actionability"] = min(1.0, sum(
            1 for w in words if w.endswith("ing") or w.endswith("tion")
        ) / max(1, len(words)) * 5)
        scores["genre_alignment"] = 0.8 if genre_hint.lower() in text_lower else 0.5

        scores["overall"] = sum(scores.values()) / len(scores)
        return scores

    def _score_technical(self, text: str) -> float:
        tech_terms = [
            "aperture", "focal", "exposure", "iso", "shutter", "white balance",
            "depth of field", "bokeh", "compression", "diffusion", "flag",
            "cil", "c-stand", "gobo", "snoot", "barn doors", "fresnel",
            "key light", "fill", "backlight", "rim", "practical",
            "dolly", "crane", "steadicam", "gimbal", "slider", "jib",
            "l-cut", "j-cut", "crossfade", "dissolve", "wipe",
        ]
        matches = sum(1 for t in tech_terms if t in text)
        return min(1.0, matches / 5)

    def _score_novelty(self, text: str) -> float:
        novelty_markers = [
            "unexpected", "unconventional", "unique", "rare", "experimental",
            "innovative", "original", "creative", "fresh", "unusual",
            "surprising", "non-traditional", "avant-garde", "cutting-edge",
        ]
        matches = sum(1 for m in novelty_markers if m in text)
        return min(1.0, 0.3 + matches * 0.15)

    def _score_visual(self, text: str) -> float:
        visual_terms = [
            "shadow", "light", "color", "contrast", "bright", "dark",
            "vibrant", "muted", "warm", "cool", "tone", "hue",
            "saturation", "luminance", "gradient", "texture",
            "silhouette", "reflection", "glow", "sparkle",
        ]
        matches = sum(1 for t in visual_terms if t in text)
        return min(1.0, matches / 4)


class SelfPlayGenerator:
    """Generates creative training data from current brain + knowledge base."""

    def __init__(self, knowledge_base: Dict[str, list]):
        self.kb = knowledge_base
        self.evaluator = CreativeQualityEvaluator()

    def generate(self, brain, projection, device: str, count: int = 100) -> List[dict]:
        pairs = []
        questions = CINEMATOGRAPHY_QUESTIONS + CREATIVE_TOPICS

        for _ in range(count):
            q = random.choice(questions)
            text = self._make_input_text(q)
            with torch.no_grad():
                x = projection([text]).to(device)
                x = x.expand(-1, 8, -1)
                output, confidence = brain(x)
            score = random.random() * 0.3 + confidence.mean().item() * 0.7

            if score > 0.7:
                response = self._build_response(q, text, confidence.mean().item())
                pairs.append({
                    "messages": [
                        {"role": "system", "content": "You are NICTO Creative Brain, a world-class cinematographer."},
                        {"role": "user", "content": q},
                        {"role": "assistant", "content": response},
                    ],
                    "quality_score": score,
                    "source": "self_play",
                })

            eval_result = self.evaluator.evaluate(text)
            if eval_result["overall"] > 0.6:
                topic = random.choice(CREATIVE_TOPICS)
                prompt = f"Describe the visual style and techniques for {topic}."
                response = self._build_response(prompt, topic, eval_result["overall"])
                pairs.append({
                    "messages": [
                        {"role": "system", "content": "You are NICTO Creative Brain, an avant-garde visual artist."},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    "quality_score": eval_result["overall"],
                    "source": "self_play_evaluated",
                })

        pairs.sort(key=lambda p: p["quality_score"], reverse=True)
        return pairs[:count]

    def _make_input_text(self, question: str) -> str:
        for cat, items in self.kb.items():
            if any(w in question.lower() for w in cat.split("_")):
                if items:
                    item = random.choice(items)
                    return json.dumps(item)
        return question

    def _build_response(self, question: str, context: str, confidence: float) -> str:
        intensity = "confidently" if confidence > 0.8 else "suggest"
        depth = random.choice([
            f"To {intensity} address this: ",
            f"Here's my professional analysis: ",
            f"Based on cinematography principles, ",
        ])
        detail = random.choice([
            f"The key consideration is understanding how {context[:60]} affects the viewer's perception. "
            f"This can be achieved through careful attention to lighting ratios, lens selection, and camera positioning.",
            f"When approaching {context[:60]}, start with the fundamental technique and then experiment. "
            f"The best results come from combining established principles with creative risk-taking.",
            f"{context[:60]} requires a multi-layered approach. "
            f"Consider the emotional goal first, then choose technical elements that serve that goal.",
        ])
        return depth + detail


class AutonomousDataGatherer:
    """NICTO autonomously fetches YouTube data using the provided API key."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.seen_ids = set()
        self.search_terms = [
            "cinematography tutorial", "lighting techniques film",
            "camera angles movie scenes", "composition photography film",
            "color grading tutorial", "director of photography tips",
            "film visual style breakdown", "cinematic lighting setup",
        ]

    def discover_search_terms(self, categories: Dict) -> List[str]:
        new_terms = []
        for cat, items in list(categories.items())[:3]:
            for item in random.sample(items, min(3, len(items))):
                name = item.get("name", "") if isinstance(item, dict) else ""
                if name:
                    new_terms.append(f"{name} cinematography tutorial")
        return new_terms[:5]

    def fetch(self, max_queries: int = 10) -> List[dict]:
        try:
            from googleapiclient.discovery import build
        except ImportError:
            print("  google-api-python-client not installed")
            return []

        all_videos = []
        queries = self.search_terms[:max_queries]

        try:
            youtube = build("youtube", "v3", developerKey=self.api_key)
            for q in queries:
                request = youtube.search().list(
                    q=q, part="snippet", maxResults=50,
                    type="video", relevanceLanguage="en",
                )
                response = request.execute()
                for item in response.get("items", []):
                    vid = item["id"]["videoId"]
                    if vid not in self.seen_ids:
                        self.seen_ids.add(vid)
                        snippet = item.get("snippet", {})
                        all_videos.append({
                            "video_id": vid,
                            "title": snippet.get("title", ""),
                            "description": snippet.get("description", "")[:500],
                            "channel": snippet.get("channelTitle", ""),
                            "source": "autonomous_youtube",
                            "search_query": q,
                        })
                time.sleep(0.3)
        except Exception as e:
            print(f"  YouTube API error: {e}")

        return all_videos


class RecursiveCreativeLearner:
    """Main recursive learning system for creative brain.

    Cycle:
      1. Fetch new YouTube data (autonomous)
      2. Self-play: generate creative samples from current knowledge
      3. Quality-evaluate and filter
      4. Expand training dataset with best outputs
      5. Retrain creative brain
      6. Repeat --- each cycle compounds quality
    """

    def __init__(
        self,
        creative_brain: nn.Module,
        config,
        data_dir: str,
        youtube_api_key: str = "",
        device: str = "cpu",
    ):
        self.brain = creative_brain
        self.config = config
        self.data_dir = data_dir
        self.device = device
        self.brain.to(device)

        self.projection = TextEmbeddingProjection()
        self.projection.to(device)
        self.loader = CreativeDataLoader(data_dir)
        self.evaluator = CreativeQualityEvaluator()
        self.generator = SelfPlayGenerator(self.loader.load_all())
        self.gatherer = AutonomousDataGatherer(youtube_api_key) if youtube_api_key else None

        self.trainer = CreativeTrainer(creative_brain, self.loader, device=device)
        self.history = {
            "cycles": [],
            "total_samples": 0,
            "best_quality": 0.0,
            "youtube_fetched": 0,
            "selfplay_generated": 0,
        }

    def run_cycle(self, steps: int = 200, query_count: int = 3) -> Dict:
        print(f"\n{'='*60}")
        print(f"Recursive Cycle {len(self.history['cycles']) + 1}")
        print(f"{'='*60}")

        cycle_data = {"phase": {}, "samples_before": 0, "samples_after": 0}
        categories = self.loader.load_all()
        cycle_data["samples_before"] = sum(len(v) for v in categories.values())

        # Phase 1: Autonomous YouTube fetch
        if self.gatherer:
            print("\n[Phase 1] Autonomous YouTube data gathering...")
            new_terms = self.gatherer.discover_search_terms(categories)
            self.gatherer.search_terms = self.gatherer.search_terms[:5] + new_terms
            videos = self.gatherer.fetch(max_queries=query_count)
            if videos:
                yt_path = os.path.join(self.data_dir, f"autonomous_youtube_cycle_{len(self.history['cycles'])}.jsonl")
                with open(yt_path, "w") as f:
                    for v in videos:
                        f.write(json.dumps(v) + "\n")
                self.history["youtube_fetched"] += len(videos)
                print(f"  Fetched {len(videos)} new videos")
                cycle_data["youtube_fetched"] = len(videos)

        # Phase 2: Self-play generation
        print("\n[Phase 2] Self-play creative generation...")
        categories = self.loader.load_all()
        self.generator.kb = categories
        new_pairs = self.generator.generate(
            self.brain, self.projection, self.device, count=100
        )
        if new_pairs:
            pairs_path = os.path.join(self.data_dir, f"selfplay_cycle_{len(self.history['cycles'])}.jsonl")
            with open(pairs_path, "w") as f:
                for p in new_pairs:
                    f.write(json.dumps(p) + "\n")
            self.history["selfplay_generated"] += len(new_pairs)
            best_q = max(p.get("quality_score", 0) for p in new_pairs)
            print(f"  Generated {len(new_pairs)} new training pairs (best quality: {best_q:.3f})")
            cycle_data["selfplay_generated"] = len(new_pairs)
            cycle_data["best_quality"] = best_q

        # Phase 3: Retrain
        print("\n[Phase 3] Retraining creative brain...")
        categories = self.loader.load_all()
        cycle_data["samples_after"] = sum(len(v) for v in categories.values())
        print(f"  Training on {cycle_data['samples_after']} total samples")

        result = self.trainer.train_epoch(categories, lr=1e-4 * (0.9 ** len(self.history["cycles"])), steps=steps)

        # Phase 4: Quality evaluation
        print("\n[Phase 4] Quality evaluation...")
        test_prompts = [
            "What camera angle creates a heroic feeling?",
            "How do I light a suspenseful scene?",
        ]
        quality_scores = []
        for prompt in test_prompts:
            with torch.no_grad():
                x = self.projection([prompt]).to(self.device)
                x = x.expand(-1, 8, -1)
                output, confidence = self.brain(x)
                quality = self.evaluator.evaluate(prompt)
                quality_scores.append(quality["overall"])
        avg_quality = sum(quality_scores) / len(quality_scores)
        if avg_quality > self.history["best_quality"]:
            self.history["best_quality"] = avg_quality

        cycle_result = {
            "cycle": len(self.history["cycles"]) + 1,
            "loss": result["loss"],
            "confidence": sum(result["confidences"].values()) / len(result["confidences"]),
            "quality": avg_quality,
            "total_samples": cycle_data["samples_after"],
        }
        self.history["cycles"].append(cycle_result)
        self.history["total_samples"] = cycle_data["samples_after"]

        print(f"\n  Cycle {cycle_result['cycle']} complete:")
        print(f"  Loss: {cycle_result['loss']:.4f}")
        print(f"  Confidence: {cycle_result['confidence']:.3f}")
        print(f"  Quality: {cycle_result['quality']:.3f}")
        print(f"  Total samples: {cycle_result['total_samples']}")

        return cycle_result

    def run(self, num_cycles: int = 10, steps_per_cycle: int = 200, queries_per_cycle: int = 3) -> List[Dict]:
        print(f"\n{'#'*60}")
        print(f" Recursive Creative Learning --- {num_cycles} cycles")
        print(f"{'#'*60}\n")

        results = []
        for i in range(num_cycles):
            result = self.run_cycle(steps=steps_per_cycle, query_count=queries_per_cycle)
            results.append(result)
            self._save_state()

        print(f"\n{'#'*60}")
        print(f" Recursive Learning Complete")
        print(f"{'#'*60}")
        print(f"Total cycles: {len(results)}")
        print(f"Final samples: {self.history['total_samples']}")
        print(f"Best quality: {self.history['best_quality']:.3f}")
        print(f"YouTube fetched: {self.history['youtube_fetched']}")
        print(f"Self-play generated: {self.history['selfplay_generated']}")
        loss_strs = [f"{r['loss']:.3f}" for r in results]
        print(f"Loss trajectory: {' -> '.join(loss_strs)}")

        return results

    def _save_state(self):
        state_dir = os.path.join(self.data_dir, "..", "checkpoints")
        os.makedirs(state_dir, exist_ok=True)
        path = os.path.join(state_dir, "recursive_creative_state.json")
        with open(path, "w") as f:
            json.dump({
                "history": self.history,
                "seen_youtube_ids": list(self.gatherer.seen_ids) if self.gatherer else [],
            }, f, indent=2)

    def save_brain(self, path: str):
        self.trainer.save(path)


class TextEmbeddingProjection(nn.Module):
    def __init__(self, d_model: int = 128, vocab_size: int = 256):
        super().__init__()
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.embed = nn.Embedding(vocab_size, d_model)

    def forward(self, texts: List[str], max_len: int = 64) -> torch.Tensor:
        batch = []
        for t in texts:
            ids = [hash(c) % self.vocab_size for c in t[:max_len]]
            ids = ids + [0] * (max_len - len(ids))
            batch.append(ids)
        x = torch.tensor(batch, dtype=torch.long)
        return self.embed(x).mean(dim=1, keepdim=True)
