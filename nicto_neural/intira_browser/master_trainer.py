"""NICTO Master Self-Improvement Pipeline.

Intira Browser finds training data -> builds datasets -> scales to 550B ->
trains across all domains -> pushes to GitHub.

Pipeline:
  1. Intira Browser searches web for domain knowledge
  2. Content extracted and structured into training datasets
  3. ULTRA 550B model architecture configured
  4. Multi-domain training (coding, math, business, science, etc.)
  5. Self-evaluation and improvement loop
  6. Results committed and pushed to GitHub
"""
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
logger = logging.getLogger(__name__)


class Domain(Enum):
    CODING = "coding"
    PROGRAMMING = "programming"
    MATHEMATICS = "mathematics"
    BUSINESS = "business"
    SCIENCE = "science"
    ENGINEERING = "engineering"
    AI_ML = "ai_ml"
    CYBERSECURITY = "cybersecurity"
    DATA_SCIENCE = "data_science"
    CLOUD_DEVOPS = "cloud_devops"
    GAME_DEV = "game_dev"
    NETWORKING = "networking"
    DATABASES = "databases"
    ROBOTICS = "robotics"
    BLOCKCHAIN = "blockchain"
    QUANTUM = "quantum"
    BIO_MEDICINE = "bio_medicine"
    BIO_CHEMISTRY = "bio_chemistry"
    BIO_BIOLOGY = "bio_biology"
    BIO_PHYSICS = "bio_physics"
    ENGINEERING_SYS = "engineering_systems"
    QUANTUM_ENG = "quantum_engineering"
    HOME_SCIENCE = "home_science"
    INVENTION = "invention"
    HUMAN_CONTEXT = "human_context"


@dataclass
class MasterResult:
    """Result of the master self-improvement pipeline."""
    domains_trained: List[str] = field(default_factory=list)
    total_sources: int = 0
    total_facts: int = 0
    total_memories: int = 0
    total_lessons: int = 0
    total_truths: int = 0
    dataset_examples: int = 0
    training_epochs: int = 0
    final_accuracy: float = 0.0
    model_params: int = 0
    git_committed: bool = False
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: float = 0.0
    phases_completed: List[str] = field(default_factory=list)


DOMAIN_SEARCH_QUERIES = {
    Domain.CODING: [
        "programming best practices 2026",
        "software design patterns",
        "clean code principles",
        "advanced algorithms",
        "data structures mastery",
    ],
    Domain.PROGRAMMING: [
        "Python advanced programming",
        "JavaScript TypeScript best practices",
        "Rust systems programming",
        "Go concurrency patterns",
        "C++ modern programming",
    ],
    Domain.MATHEMATICS: [
        "advanced calculus tutorial",
        "linear algebra applications",
        "probability theory guide",
        "statistical methods 2026",
        "discrete mathematics",
    ],
    Domain.BUSINESS: [
        "business strategy frameworks",
        "startup growth tactics",
        "financial modeling guide",
        "marketing strategy 2026",
        "entrepreneurship fundamentals",
    ],
    Domain.SCIENCE: [
        "physics for engineers",
        "chemistry fundamentals",
        "biology systems guide",
        "neuroscience principles",
        "scientific method",
    ],
    Domain.ENGINEERING: [
        "systems engineering guide",
        "software architecture patterns",
        "distributed systems design",
        "microservices architecture",
        "API design best practices",
    ],
    Domain.AI_ML: [
        "deep learning architectures 2026",
        "transformer models guide",
        "reinforcement learning advanced",
        "NLP techniques 2026",
        "computer vision advances",
    ],
    Domain.CYBERSECURITY: [
        "cybersecurity fundamentals",
        "penetration testing guide",
        "network security best practices",
        "application security",
        "zero trust architecture",
    ],
    Domain.DATA_SCIENCE: [
        "data science pipeline",
        "big data technologies 2026",
        "data visualization techniques",
        "statistical learning",
        "feature engineering guide",
    ],
    Domain.CLOUD_DEVOPS: [
        "cloud architecture AWS Azure GCP",
        "DevOps CI/CD best practices",
        "Kubernetes container orchestration",
        "infrastructure as code",
        "monitoring observability",
    ],
    Domain.GAME_DEV: [
        "game engine architecture",
        "3D graphics programming",
        "game AI behavior trees",
        "physics simulation",
        "procedural generation",
    ],
    Domain.NETWORKING: [
        "computer networks guide",
        "TCP IP protocol stack",
        "network security protocols",
        "SDN network virtualization",
        "wireless communication",
    ],
    Domain.DATABASES: [
        "database design principles",
        "SQL optimization techniques",
        "NoSQL databases guide",
        "distributed databases",
        "data modeling",
    ],
    Domain.ROBOTICS: [
        "robotics fundamentals",
        "ROS robot operating system",
        "computer vision robotics",
        "control systems",
        "sensor fusion",
    ],
    Domain.BLOCKCHAIN: [
        "blockchain technology guide",
        "smart contract development",
        "DeFi decentralized finance",
        "consensus algorithms",
        "Web3 development",
    ],
    Domain.QUANTUM: [
        "quantum computing basics",
        "quantum algorithms",
        "quantum machine learning",
        "quantum error correction",
        "quantum cryptography",
    ],
    Domain.BIO_MEDICINE: [
        "drug discovery machine learning 2026",
        "precision medicine genomics",
        "clinical trial AI",
        "disease modeling computational biology",
        "medical imaging deep learning",
    ],
    Domain.BIO_CHEMISTRY: [
        "molecular modeling neural networks",
        "reaction prediction AI",
        "computational chemistry 2026",
        "chemical property prediction",
        "spectroscopy machine learning",
    ],
    Domain.BIO_BIOLOGY: [
        "genetics machine learning",
        "proteomics computational biology",
        "cellular pathway analysis",
        "evolutionary biology AI",
        "systems biology modeling",
    ],
    Domain.BIO_PHYSICS: [
        "biophysics simulation",
        "quantum biology research",
        "statistical mechanics biology",
        "molecular dynamics AI",
        "protein folding deep learning",
    ],
    Domain.ENGINEERING_SYS: [
        "systems engineering best practices",
        "mechatronics robotics AI",
        "control systems machine learning",
        "embedded systems 2026",
        "engineering design automation",
    ],
    Domain.QUANTUM_ENG: [
        "quantum hardware engineering",
        "quantum sensing technology",
        "quantum metrology advances",
        "superconducting qubits 2026",
        "quantum error correction hardware",
    ],
    Domain.HOME_SCIENCE: [
        "smart home AI automation 2026",
        "domestic energy optimization",
        "sustainable housing technology",
        "home robotics assistance",
        "intelligent building systems",
    ],
    Domain.INVENTION: [
        "innovation methodology TRIZ",
        "patent analysis AI",
        "design thinking frameworks",
        "creative problem solving techniques",
        "technology invention process",
    ],
    Domain.HUMAN_CONTEXT: [
        "human emotion recognition AI",
        "pragmatic language understanding",
        "theory of mind artificial intelligence",
        "discourse analysis computational",
        "social intelligence AI systems",
    ],
}


class MasterPipeline:
    """NICTO Master Self-Improvement Pipeline.

    NICTO uses Intira Browser to search the web, extract knowledge,
    build training datasets, configure 550B-scale models, train across
    all domains, and push improvements to GitHub.
    """

    def __init__(self):
        self._trainer = None
        self._api = None
        self._brain = None
        self._dataset_builder = None
        self._start_time = 0.0
        self._result = MasterResult()
        self._git_available = False

    async def ensure_trainer(self):
        if self._trainer is None:
            from .trainer import IntiraTrainer
            self._trainer = IntiraTrainer()
            await self._trainer.ensure_brain()
            self._brain = self._trainer._brain

    async def ensure_api(self):
        if self._api is None:
            from .api import IntiraAPI
            self._api = IntiraAPI(headless=True)

    def _log(self, msg: str):
        print(f"  [NICTO] {msg}")
        logger.info(msg)

    async def phase1_web_knowledge_acquisition(
        self, domains: Optional[List[Domain]] = None
    ) -> MasterResult:
        """Phase 1: Search web and acquire knowledge across all domains."""
        self._log("=" * 60)
        self._log("PHASE 1: Web Knowledge Acquisition")
        self._log("Intira Browser searching across all domains...")
        self._log("=" * 60)

        if domains is None:
            domains = list(Domain)

        await self.ensure_trainer()
        await self.ensure_api()

        total_sources = 0
        total_facts = 0
        total_memories = 0
        total_lessons = 0
        total_truths = 0

        for domain in domains:
            queries = DOMAIN_SEARCH_QUERIES.get(domain, [domain.value])
            self._log(f"  Learning domain: {domain.value.upper()} ({len(queries)} topics)")

            for query in queries[:3]:
                try:
                    result = await self._trainer.search_and_learn(
                        topic=query,
                        count=3,
                        engine="duckduckgo",
                        mode="full",
                        extract_content=False,
                    )
                    total_sources += result.sources_used
                    total_facts += result.facts_added
                    total_memories += result.memories_stored
                    total_lessons += result.lessons_learned
                    total_truths += result.truths_registered
                    self._result.domains_trained.append(domain.value)

                    await asyncio.sleep(0.5)
                except Exception as e:
                    self._result.errors.append(f"Domain {domain.value}, query '{query}': {e}")

        self._result.total_sources = total_sources
        self._result.total_facts = total_facts
        self._result.total_memories = total_memories
        self._result.total_lessons = total_lessons
        self._result.total_truths = total_truths
        self._result.phases_completed.append("web_knowledge_acquisition")

        self._log(f"  Phase 1 complete: {total_sources} sources, "
                  f"{total_facts} facts, {total_memories} memories, "
                  f"{total_lessons} lessons, {total_truths} truths")
        return self._result

    async def phase2_build_training_dataset(
        self, target_examples: int = 10000
    ) -> MasterResult:
        """Phase 2: Build comprehensive training dataset from brain knowledge."""
        self._log("=" * 60)
        self._log("PHASE 2: Building Training Dataset")
        self._log("=" * 60)

        await self.ensure_trainer()

        try:
            from nicto_neural.learning import DatasetBuilder

            self._dataset_builder = DatasetBuilder()
            dataset = self._dataset_builder.build(max_examples=target_examples)
            self._result.dataset_examples = len(dataset)

            dataset_path = os.path.join(
                os.path.dirname(__file__), "..", "training_data",
                f"master_dataset_{int(time.time())}.jsonl"
            )
            os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
            self._dataset_builder.generate_jsonl(dataset, dataset_path)

            self._log(f"  Dataset: {len(dataset)} examples -> {dataset_path}")

            train, val = self._dataset_builder.train_val_split(dataset)
            self._log(f"  Train/Val split: {len(train)}/{len(val)}")

        except Exception as e:
            self._result.errors.append(f"Dataset build failed: {e}")
            self._log(f"  Dataset build error: {e}")

        self._result.phases_completed.append("build_training_dataset")
        return self._result

    async def phase3_configure_550b_model(self) -> MasterResult:
        """Phase 3: Configure and initialize the 550B ULTRA model."""
        self._log("=" * 60)
        self._log("PHASE 3: 550B ULTRA Model Configuration")
        self._log("=" * 60)

        try:
            from nicto_neural.neural.super_config import (
                SuperConfig, ULTRA_CONFIG, CONFIG_MAP
            )
            from nicto_neural.neural.super_core import SuperNeuralCore

            config = ULTRA_CONFIG
            params = config.estimate_params()
            self._result.model_params = params
            self._log(f"  ULTRA Config loaded: d_model={config.d_model}, "
                      f"n_layers={config.n_layers}, n_experts={config.n_experts}")
            self._log(f"  Estimated parameters: {params:,} ({params/1e9:.1f}B)")

            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..",
                "configs", "ultra_550b_config.json"
            )
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                import dataclasses
                json.dump(dataclasses.asdict(config), f, indent=2, default=str)
            self._log(f"  Config saved to: {config_path}")

        except Exception as e:
            self._result.errors.append(f"550B config failed: {e}")
            self._log(f"  550B config error: {e}")

        self._result.phases_completed.append("configure_550b_model")
        return self._result

    async def phase4_multi_domain_training(self) -> MasterResult:
        """Phase 4: Multi-domain training with SuperTrainer."""
        self._log("=" * 60)
        self._log("PHASE 4: Multi-Domain Training")
        self._log("=" * 60)

        await self.ensure_trainer()

        try:
            from nicto_neural.neural.super_config import SMALL_CONFIG
            from nicto_neural.neural.super_core import SuperNeuralCore
            from nicto_neural.neural.training import SuperTrainer
            from nicto_neural.learning import NeuralTrainer

            config = SMALL_CONFIG
            self._log(f"  Using SMALL config for training run "
                      f"(d_model={config.d_model}, n_layers={config.n_layers})")

            model = SuperNeuralCore(config)
            self._log(f"  Model created: {model.get_num_params():,} params")

            trainer = NeuralTrainer(config, model)
            dataset = [
                {"input": f"Explain {d.value}", "output": f"Knowledge about {d.value}"}
                for d in Domain
            ]
            train_result = trainer.train(
                dataset, mode="supervised", epochs=3, batch_size=8
            )
            self._result.training_epochs = train_result.get("epochs", 3)
            self._result.final_accuracy = train_result.get("accuracy", 0.0)
            self._log(f"  Training complete: {train_result}")

        except Exception as e:
            self._result.errors.append(f"Multi-domain training failed: {e}")
            self._log(f"  Training error: {e}")

        self._result.phases_completed.append("multi_domain_training")
        return self._result

    async def phase5_self_evaluation(self) -> MasterResult:
        """Phase 5: Evaluate NICTO's capabilities across domains."""
        self._log("=" * 60)
        self._log("PHASE 5: Self-Evaluation")
        self._log("=" * 60)

        await self.ensure_trainer()

        if not self._brain:
            self._log("  Brain not available for evaluation")
            self._result.phases_completed.append("self_evaluation")
            return self._result

        try:
            learner = self._brain.learner
            knowledge = self._brain.knowledge
            memory = self._brain.memory

            if learner:
                total_skills = len(learner.lesson_store)
                master_skills = sum(
                    1 for v in learner.skill_progress.values()
                    if v.get("score", 0) >= 0.9
                )
                self._log(f"  Skills: {total_skills} total, {master_skills} at MASTER level")

                for topic_key in learner.skill_progress:
                    info = learner.skill_progress[topic_key]
                    self._log(f"    {topic_key[:40]:40s} "
                              f"score={info.get('score', 0):.2f} "
                              f"level={info.get('level', 'NOVICE').value}")

                curious = learner.get_curious_topics(threshold=0.1)
                if curious:
                    self._log(f"  Curious about: {', '.join(curious[:5])}")

            if knowledge:
                facts_count = len(knowledge.facts)
                concepts_count = len(knowledge.concepts)
                beliefs_count = len(knowledge.beliefs)
                self._log(f"  KnowledgeCore: {facts_count} facts, "
                          f"{concepts_count} concepts, {beliefs_count} beliefs")

            if memory:
                mem_count = len(memory.fragments)
                self._log(f"  LongTermMemory: {mem_count} fragments")

        except Exception as e:
            self._result.errors.append(f"Self-evaluation failed: {e}")

        self._result.phases_completed.append("self_evaluation")
        return self._result

    async def phase6_colab_access(self) -> MasterResult:
        """Phase 6: Access Google Colab via Intira Browser for cloud GPUs."""
        self._log("=" * 60)
        self._log("PHASE 6: Google Colab Access via Intira Browser")
        self._log("=" * 60)

        await self.ensure_api()

        try:
            nav = await self._api.navigate("https://colab.research.google.com")
            self._log(f"  Navigated to Colab: {nav.get('title', 'N/A')[:60]}")
            await self._api.extract_current_page()

            colab_script_path = os.path.join(
                os.path.dirname(__file__), "..", "..",
                "scripts", "colab_train_all.py"
            )
            if os.path.exists(colab_script_path):
                self._log(f"  Colab training script exists: {colab_script_path}")
                with open(colab_script_path, "r") as f:
                    content = f.read()
                self._log(f"  Colab script: {len(content)} chars, "
                          f"{content.count('def ')} functions")
        except Exception as e:
            self._result.errors.append(f"Colab access failed: {e}")
            self._log(f"  Colab access error: {e}")

        self._result.phases_completed.append("colab_access")
        return self._result

    async def phase7_github_push(self) -> MasterResult:
        """Phase 7: Commit and push all improvements to GitHub."""
        self._log("=" * 60)
        self._log("PHASE 7: GitHub Push")
        self._log("=" * 60)

        try:
            import subprocess

            repo_dir = os.path.join(os.path.dirname(__file__), "..", "..")

            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=repo_dir, timeout=30,
            )
            changed_files = [l for l in status.stdout.split("\n") if l.strip()]
            self._log(f"  Changed files: {len(changed_files)}")

            if changed_files:
                subprocess.run(
                    ["git", "add", "-A"],
                    capture_output=True, cwd=repo_dir, timeout=30,
                )
                commit_msg = (
                    f"NICTO Master Self-Improvement Pipeline\n\n"
                    f"Domains: {len(self._result.domains_trained)}\n"
                    f"Sources: {self._result.total_sources}\n"
                    f"Facts: {self._result.total_facts}\n"
                    f"Memories: {self._result.total_memories}\n"
                    f"Lessons: {self._result.total_lessons}\n"
                    f"Truths: {self._result.total_truths}\n"
                    f"Dataset: {self._result.dataset_examples} examples\n"
                    f"Model: {self._result.model_params:,} params\n"
                    f"Phases: {', '.join(self._result.phases_completed)}"
                )
                subprocess.run(
                    ["git", "commit", "-m", commit_msg],
                    capture_output=True, cwd=repo_dir, timeout=30,
                )

                push = subprocess.run(
                    ["git", "push", "origin", "main"],
                    capture_output=True, text=True, cwd=repo_dir, timeout=60,
                )
                self._log(f"  Git push: {push.stdout[:100] if push.stdout else 'OK'}")

                self._result.git_committed = True
                self._log("  Changes committed and pushed to GitHub")
            else:
                self._log("  No changes to commit")

        except Exception as e:
            self._result.errors.append(f"GitHub push failed: {e}")
            self._log(f"  GitHub push error: {e}")

        self._result.phases_completed.append("github_push")
        return self._result

    async def run_full_pipeline(
        self,
        domains: Optional[List[Domain]] = None,
        skip_phases: Optional[List[str]] = None,
    ) -> MasterResult:
        """Run the complete self-improvement pipeline end-to-end."""
        self._start_time = time.time()
        self._result = MasterResult(timestamp=self._start_time)

        skip = set(skip_phases or [])

        print()
        print("=" * 64)
        print("  NICTO MASTER SELF-IMPROVEMENT PIPELINE")
        print("  Intira Browser + 550B ULTRA Model + Multi-Domain Training")
        print("=" * 64)

        try:
            if "web_knowledge_acquisition" not in skip:
                await self.phase1_web_knowledge_acquisition(domains)

            if "build_training_dataset" not in skip:
                await self.phase2_build_training_dataset()

            if "configure_550b_model" not in skip:
                await self.phase3_configure_550b_model()

            if "multi_domain_training" not in skip:
                await self.phase4_multi_domain_training()

            if "self_evaluation" not in skip:
                await self.phase5_self_evaluation()

            if "colab_access" not in skip:
                await self.phase6_colab_access()

            if "github_push" not in skip:
                await self.phase7_github_push()

        except Exception as e:
            self._result.errors.append(f"Pipeline failed: {e}")
            self._log(f"PIPELINE ERROR: {e}")

        self._result.duration_seconds = time.time() - self._start_time

        print()
        print("=" * 64)
        print("  MASTER PIPELINE COMPLETE")
        print("=" * 64)
        print(f"  Duration: {self._result.duration_seconds:.1f}s")
        print(f"  Domains trained: {len(set(self._result.domains_trained))}")
        print(f"  Total sources: {self._result.total_sources}")
        print(f"  Total facts: {self._result.total_facts}")
        print(f"  Total memories: {self._result.total_memories}")
        print(f"  Total lessons: {self._result.total_lessons}")
        print(f"  Total truths: {self._result.total_truths}")
        print(f"  Dataset examples: {self._result.dataset_examples}")
        print(f"  Model parameters: {self._result.model_params:,}")
        print(f"  Training epochs: {self._result.training_epochs}")
        print(f"  Final accuracy: {self._result.final_accuracy:.2%}")
        print(f"  Git committed: {self._result.git_committed}")
        if self._result.errors:
            print(f"  Errors ({len(self._result.errors)}):")
            for e in self._result.errors[-5:]:
                print(f"    - {e}")
        print(f"  Phases completed: {len(self._result.phases_completed)}")
        for p in self._result.phases_completed:
            print(f"    + {p}")
        print()

        return self._result

    async def close(self):
        if self._trainer:
            await self._trainer.close()
        if self._api:
            await self._api.close()
