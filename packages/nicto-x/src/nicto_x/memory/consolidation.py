"""NICTO X — Memory consolidation: transfers important episodic content to semantic memory."""

from __future__ import annotations

import logging
import re
from typing import Optional

from nicto_x.memory.episodic import EpisodicMemory
from nicto_x.memory.semantic import SemanticMemory

logger = logging.getLogger("nicto_x.memory.consolidation")


class MemoryConsolidator:
    """Extracts facts from episodic memories and stores them as semantic knowledge."""

    def __init__(
        self,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
    ):
        self.episodic = episodic
        self.semantic = semantic

    async def run(self, limit: int = 50) -> int:
        recent = await self.episodic.get_recent(limit)
        consolidated = 0
        for ep in recent:
            content = ep.get("content", {})
            text = (
                content.get("output", "")
                or content.get("response", "")
                or str(content)
            )
            facts = self._extract_facts(text, ep.get("id", ""))
            for fact in facts:
                await self.semantic.store_fact(**fact)
                consolidated += 1
        if consolidated:
            logger.info("Consolidated %d facts from episodic memory.", consolidated)
        return consolidated

    def _extract_facts(self, text: str, source_id: str) -> list[dict]:
        facts = []
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            patterns = [
                (r"(.+?)\s+is\s+(a|an|the)\s+(.+)", "is_a"),
                (r"(.+?)\s+has\s+(.+)", "has"),
                (r"(.+?)\s+can\s+(.+)", "can"),
                (r"(.+?)\s+uses\s+(.+)", "uses"),
                (r"(.+?)\s+contains\s+(.+)", "contains"),
                (r"(.+?)\s+means\s+(.+)", "means"),
                (r"(.+?)\s+refers\s+to\s+(.+)", "refers_to"),
            ]
            for pattern, predicate in patterns:
                m = re.match(pattern, sentence, re.IGNORECASE)
                if m:
                    facts.append({
                        "subject": m.group(1).strip(),
                        "predicate": predicate,
                        "object_val": m.group(3).strip()
                        if len(m.groups()) > 2
                        else m.group(2).strip(),
                        "confidence": 0.6,
                        "source": source_id,
                    })
                    break
        return facts
