"""IntiraTrainer — NICTO self-trains from web data fetched by Intira Browser.

Pipeline: Intira Browser fetches web data → ContentExtractor structures it →
IntiraTrainer injects into NICTO's brain subsystems:
  - KnowledgeCore.add_fact()      → permanent facts
  - LongTermMemory.store()        → episodic memories with tags
  - Learner.learn()               → skills & lessons with mastery
  - TruthEngine.register_fact()   → verified fact registry
  - Teacher                       → structured study plans
"""
import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from enum import Enum


logger = logging.getLogger(__name__)


class TrainingMode(Enum):
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    SKILL = "skill"
    TRUTH = "truth"
    FULL = "full"


@dataclass
class TrainingResult:
    topic: str
    sources_used: int = 0
    facts_added: int = 0
    memories_stored: int = 0
    lessons_learned: int = 0
    truths_registered: int = 0
    concepts_created: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: float = 0.0


class IntiraTrainer:
    """Self-training engine: Intira Browser fetches → NICTO learns.

    NICTO uses Intira Browser to search the web for topics it wants to learn,
    then feeds the extracted content into its own brain subsystems for
    permanent knowledge acquisition, memory formation, and skill development.
    """

    def __init__(self, brain=None, api=None):
        self._brain = brain
        self._api = api
        self._train_history: List[TrainingResult] = []
        self._learning_queue: List[Dict[str, Any]] = []
        self._autonomous_mode: bool = False

    async def ensure_brain(self):
        if self._brain is None:
            from nikto import NiktoBrain
            self._brain = NiktoBrain()
            await self._brain.awaken(restore=True)

    async def ensure_api(self):
        if self._api is None:
            from .api import IntiraAPI
            self._api = IntiraAPI(headless=True)

    async def search_and_learn(
        self,
        topic: str,
        count: int = 5,
        engine: str = "duckduckgo",
        mode: TrainingMode = TrainingMode.FULL,
        extract_content: bool = True,
    ) -> TrainingResult:
        """Search the web for a topic and train NICTO on the results.

        This is the main pipeline:
        1. Intira Browser searches the web
        2. Content is extracted and structured
        3. Results are injected into NICTO's brain subsystems
        """
        await self.ensure_api()
        await self.ensure_brain()

        if isinstance(mode, str):
            try:
                mode = TrainingMode(mode)
            except ValueError:
                mode = TrainingMode.FULL

        start_time = time.time()
        result = TrainingResult(topic=topic, timestamp=start_time)
        self._train_history.append(result)

        try:
            search_result = await self._api.search(
                query=topic, count=count, engine=engine
            )
            web_results = search_result.get("results", [])
            result.sources_used = len(web_results)

            if not web_results:
                result.errors.append(f"No results found for '{topic}'")
                return result

            logger.info(
                f"IntiraTrainer: Learning '{topic}' from "
                f"{len(web_results)} web sources"
            )

            for i, item in enumerate(web_results):
                try:
                    title = item.get("title", "")
                    url = item.get("url", "")
                    snippet = item.get("snippet", "")

                    content_text = snippet or title
                    if extract_content and url and len(content_text) < 50:
                        try:
                            page = await self._api.fetch(url)
                            fetched = page.get("content", "")
                            if fetched and len(fetched) > len(content_text):
                                content_text = fetched
                        except Exception as e:
                            logger.debug(f"Content fetch failed for {url}: {e}")

                    if mode in (TrainingMode.FULL, TrainingMode.KNOWLEDGE):
                        self._train_knowledge(topic, title, url, content_text)

                    if mode in (TrainingMode.FULL, TrainingMode.MEMORY):
                        self._train_memory(topic, title, url, content_text)

                    if mode in (TrainingMode.FULL, TrainingMode.SKILL):
                        self._train_skill(topic, content_text, url)

                    if mode in (TrainingMode.FULL, TrainingMode.TRUTH):
                        self._train_truth(topic, content_text, url, title)

                    await asyncio.sleep(0.1)
                except Exception as e:
                    err = f"Item {i} failed: {e}"
                    logger.warning(err)
                    result.errors.append(err)

            if mode in (TrainingMode.FULL, TrainingMode.KNOWLEDGE):
                concepts = self._build_concepts(topic, web_results)
                result.concepts_created = concepts

        except Exception as e:
            err = f"Search and learn failed: {e}"
            logger.error(err)
            result.errors.append(err)

        result.duration_seconds = time.time() - start_time

        await self._brain.sleep()

        logger.info(
            f"IntiraTrainer: Learned '{topic}' in {result.duration_seconds:.1f}s "
            f"- {result.facts_added}facts {result.memories_stored}memories "
            f"{result.lessons_learned}lessons {result.truths_registered}truths"
        )
        return result

    def _train_knowledge(
        self, topic: str, title: str, url: str, content: str
    ):
        """Inject web data into NiktoKnowledgeCore as permanent facts."""
        if not content or len(content.strip()) < 20:
            logger.debug(f"Skip knowledge: content too short ({len(content) if content else 0})")
            return

        try:
            knowledge = self._brain.knowledge if self._brain else None
            if knowledge is None:
                return
        except Exception as e:
            logger.debug(f"Skip knowledge: brain access failed: {e}")
            return

        statements = self._extract_statements(content)
        for i, stmt in enumerate(statements[:3]):
            try:
                fact_text = f"{stmt} (source: {title})" if title else stmt
                knowledge.add_fact(
                    fact=fact_text,
                    source=f"intira_browser:{url}",
                    confidence=0.7,
                )
                self._train_history[-1].facts_added += 1
            except Exception as e:
                logger.debug(f"Knowledge add_fact failed: {e}")

    def _train_memory(
        self, topic: str, title: str, url: str, content: str
    ):
        """Store web data as episodic memories in NiktoLongTermMemory."""
        memory = self._brain.memory
        if not memory:
            return

        tags = [
            "web", "intira", topic.lower().replace(" ", "_"),
            *[w.lower()[:15] for w in topic.split() if len(w) > 3],
        ]

        memory_text = f"[Intira Browser] {title}: {content[:300]}"
        try:
            importance = 0.5 + (0.3 if len(content) > 100 else 0.0)
            memory.store(
                content=memory_text[:500],
                tags=tags,
                importance=min(importance, 1.0),
            )
            self._train_history[-1].memories_stored += 1
        except Exception as e:
            logger.debug(f"Memory store failed: {e}")

    def _train_skill(
        self, topic: str, content: str, source: str
    ):
        """Train NICTO skills from web content via NiktoLearner."""
        learner = self._brain.learner
        if not learner:
            return

        try:
            lesson_content = content[:200] if content else topic
            learner.learn(
                topic=topic,
                content=lesson_content,
                source=f"intira_browser:{source}",
            )
            self._train_history[-1].lessons_learned += 1

            learner.set_curiosity(topic, intensity=0.3)
        except Exception as e:
            logger.debug(f"Learner learn failed: {e}")

    def _train_truth(
        self, topic: str, content: str, url: str, title: str
    ):
        """Register web data as verified facts in NiktoTruthEngine."""
        truth = self._brain.truth
        if not truth:
            return

        try:
            claim = content[:200] if content else title
            if len(claim) > 20:
                truth.register_fact(
                    claim=claim,
                    confidence=0.6,
                    source=f"intira_browser:{url}",
                    category=topic,
                    evidence=[url],
                    tags=["web", topic],
                )
                self._train_history[-1].truths_registered += 1
        except Exception as e:
            logger.debug(f"Truth register_fact failed: {e}")

    def _build_concepts(
        self, topic: str, results: List[dict]
    ) -> int:
        """Build concept definitions from aggregated search results."""
        knowledge = self._brain.knowledge
        if not knowledge:
            return 0

        snippets = [
            r.get("snippet", "") or r.get("title", "") for r in results
        ]
        combined = " ".join(snippets)[:500]
        if len(combined) < 50:
            return 0

        try:
            knowledge.add_concept(
                name=topic,
                definition=combined[:300],
                attributes={"source": "intira_browser", "results": len(results)},
            )
            return 1
        except Exception as e:
            logger.debug(f"Concept creation failed: {e}")
            return 0

    def _extract_statements(self, text: str) -> List[str]:
        """Extract meaningful factual statements from text."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        clean = []
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and len(s) < 500:
                s = re.sub(r'\s+', ' ', s)
                clean.append(s)
        return clean[:5]

    async def autonomous_learning_cycle(
        self, topics: Optional[List[str]] = None, max_topics: int = 3
    ) -> List[TrainingResult]:
        """Run an autonomous learning cycle.

        NICTO picks topics it's curious about (from Learner.curious_topics),
        searches the web via Intira Browser, and trains itself.
        """
        await self.ensure_brain()

        if not topics:
            try:
                topics = self._brain.learner.get_curious_topics(
                    threshold=0.3
                )[:max_topics]
            except Exception:
                topics = []
            if not topics:
                topics = [
                    "artificial intelligence",
                    "web browser technology",
                    "machine learning",
                ][:max_topics]

        logger.info(
            f"IntiraTrainer: Starting autonomous learning cycle on "
            f"{len(topics)} topics: {topics}"
        )

        results = []
        for topic in topics:
            try:
                tr = await self.search_and_learn(
                    topic=topic, count=5, engine="duckduckgo"
                )
                results.append(tr)
            except Exception as e:
                logger.error(f"Autonomous learn '{topic}' failed: {e}")

        return results

    async def queue_topic(self, topic: str, priority: int = 5):
        """Queue a topic for future learning."""
        self._learning_queue.append({
            "topic": topic,
            "priority": priority,
            "queued_at": time.time(),
        })
        self._learning_queue.sort(key=lambda x: -x["priority"])

    async def process_queue(self, max_items: int = 5) -> List[TrainingResult]:
        """Process the learning queue."""
        results = []
        for _ in range(min(max_items, len(self._learning_queue))):
            item = self._learning_queue.pop(0)
            tr = await self.search_and_learn(
                topic=item["topic"], count=5, engine="duckduckgo"
            )
            results.append(tr)
        return results

    def get_training_history(self) -> List[dict]:
        return [
            {
                "topic": r.topic,
                "sources": r.sources_used,
                "facts": r.facts_added,
                "memories": r.memories_stored,
                "lessons": r.lessons_learned,
                "truths": r.truths_registered,
                "concepts": r.concepts_created,
                "duration": f"{r.duration_seconds:.1f}s",
                "errors": r.errors,
            }
            for r in self._train_history
        ]

    def get_status(self) -> dict:
        return {
            "total_training_sessions": len(self._train_history),
            "queue_size": len(self._learning_queue),
            "autonomous_mode": self._autonomous_mode,
            "brain_connected": self._brain is not None,
            "api_connected": self._api is not None,
            "recent_sessions": self._train_history[-3:] if self._train_history else [],
        }

    async def close(self):
        if self._brain:
            try:
                await self._brain.sleep()
            except Exception:
                pass
        if self._api:
            await self._api.close()
