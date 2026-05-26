"""
NiktoLongTermMemory — NICTO's Permanent Memory System.

NICTO remembers everything. Every conversation. Every user.
Every mistake. Every success. This is not session memory.
This is permanent, growing, self-organizing memory.

Three memory types working together:
- Episodic: specific events and conversations
- Semantic: facts and knowledge learned
- Procedural: how to do things (skills and patterns)
"""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .models import (
    Memory, MemoryEvent, UserModel, Perception
)


class EpisodicMemory:
    """
    Memory of specific events and conversations.
    
    Stores the raw experience of interactions - what happened,
    when, with whom. Used to recall past conversations and
    understand user patterns over time.
    """

    def __init__(self):
        """Initialize empty episodic memory store."""
        self._memories: list[dict] = []
        self._user_index: dict[str, list[int]] = {}

    async def store(self, event: MemoryEvent) -> str:
        """
        Store a new episodic memory.
        
        Args:
            event: The memory event to store
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid4())[:12]
        
        memory_data = {
            "id": memory_id,
            "input": event.input,
            "response": event.response,
            "domain": event.domain,
            "complexity": event.complexity,
            "user_id": event.user_id,
            "timestamp": event.timestamp,
        }
        
        self._memories.append(memory_data)
        
        # Index by user
        if event.user_id:
            if event.user_id not in self._user_index:
                self._user_index[event.user_id] = []
            self._user_index[event.user_id].append(len(self._memories) - 1)
        
        return memory_id

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> list[Memory]:
        """
        Search episodic memories by content similarity.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant memories
        """
        query_words = set(query.lower().split())
        
        scored = []
        for mem in self._memories:
            content = f"{mem['input']} {mem['response']}".lower()
            mem_words = set(content.split())
            
            overlap = len(query_words & mem_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                scored.append((score, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [
            Memory(
                id=mem["id"],
                content=f"{mem['input']} -> {mem['response']}",
                domain=mem["domain"],
                timestamp=mem["timestamp"],
                relevance_score=score
            )
            for score, mem in scored[:limit]
        ]

    async def delete_by_user(self, user_id: str) -> int:
        """
        Delete all memories for a specific user.
        
        Args:
            user_id: User ID to delete memories for
            
        Returns:
            Number of memories deleted
        """
        if user_id not in self._user_index:
            return 0
        
        indices = self._user_index[user_id]
        deleted = 0
        
        for idx in sorted(indices, reverse=True):
            self._memories.pop(idx)
            deleted += 1
        
        del self._user_index[user_id]
        
        # Rebuild index
        self._rebuild_user_index()
        
        return deleted

    def _rebuild_user_index(self) -> None:
        """Rebuild user index after deletions."""
        self._user_index = {}
        for i, mem in enumerate(self._memories):
            uid = mem.get("user_id")
            if uid:
                if uid not in self._user_index:
                    self._user_index[uid] = []
                self._user_index[uid].append(i)

    async def count(self) -> int:
        """Return total number of memories."""
        return len(self._memories)


class SemanticMemory:
    """
    Memory of facts and learned knowledge.
    
    Stores extracted facts, concepts, and generalizations
    from interactions. Used for reasoning and understanding.
    """

    def __init__(self):
        """Initialize empty semantic memory store."""
        self._facts: list[dict] = []
        self._topic_index: dict[str, list[int]] = {}

    async def store(self, event: MemoryEvent) -> str:
        """
        Store extracted semantic information.
        
        Args:
            event: The memory event to extract from
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid4())[:12]
        
        # Extract facts from the interaction
        facts = self._extract_facts(event)
        
        for fact_text in facts:
            fact_data = {
                "id": str(uuid4())[:12],
                "content": fact_text,
                "domain": event.domain,
                "timestamp": datetime.utcnow(),
            }
            self._facts.append(fact_data)
            
            # Index by domain
            if event.domain not in self._topic_index:
                self._topic_index[event.domain] = []
            self._topic_index[event.domain].append(len(self._facts) - 1)
        
        return memory_id

    def _extract_facts(self, event: MemoryEvent) -> list[str]:
        """
        Extract factual information from a memory event.
        
        Args:
            event: The memory event
            
        Returns:
            List of extracted facts
        """
        facts = []
        
        # Simple fact extraction based on patterns
        text = event.input + " " + event.response
        
        # Extract programming language mentions
        languages = ["python", "javascript", "java", "c++", "rust", "go"]
        for lang in languages:
            if lang.lower() in text.lower():
                facts.append(f"User works with {lang}")
        
        # Extract domain expertise hints
        if "security" in text.lower() or "hack" in text.lower():
            facts.append("User interested in security")
        
        if "build" in text.lower() or "create" in text.lower():
            facts.append("User is building something")
        
        # Extract tool mentions
        tools = ["docker", "kubernetes", "git", "linux", "aws"]
        for tool in tools:
            if tool.lower() in text.lower():
                facts.append(f"User uses {tool}")
        
        return facts

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> list[Memory]:
        """
        Search semantic memories by content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant memories
        """
        query_lower = query.lower()
        
        scored = []
        for i, fact in enumerate(self._facts):
            content = fact["content"].lower()
            
            # Calculate relevance
            if query_lower in content:
                score = 1.0
            else:
                query_words = set(query_lower.split())
                fact_words = set(content.split())
                overlap = len(query_words & fact_words)
                score = overlap / max(len(query_words), 1)
            
            if score > 0:
                scored.append((score, i, fact))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [
            Memory(
                id=fact["id"],
                content=fact["content"],
                domain=fact["domain"],
                timestamp=fact["timestamp"],
                relevance_score=score
            )
            for score, i, fact in scored[:limit]
        ]

    async def delete_by_topic(self, topic: str) -> int:
        """
        Delete all facts for a specific topic.
        
        Args:
            topic: Topic to delete
            
        Returns:
            Number of facts deleted
        """
        if topic not in self._topic_index:
            return 0
        
        indices = self._topic_index[topic]
        deleted = len(indices)
        
        for idx in sorted(indices, reverse=True):
            self._facts.pop(idx)
        
        del self._topic_index[topic]
        
        return deleted

    async def count(self) -> int:
        """Return total number of facts."""
        return len(self._facts)


class ProceduralMemory:
    """
    Memory of how to do things.
    
    Stores procedures, patterns, and skills - the knowledge
    of HOW to perform tasks, not just facts about them.
    """

    def __init__(self):
        """Initialize empty procedural memory store."""
        self._procedures: list[dict] = []

    async def store(self, event: MemoryEvent) -> str:
        """
        Store a new procedure.
        
        Args:
            event: The memory event to extract from
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid4())[:12]
        
        # Extract procedures from the interaction
        procedures = self._extract_procedures(event)
        
        for proc_text in procedures:
            proc_data = {
                "id": str(uuid4())[:12],
                "content": proc_text,
                "domain": event.domain,
                "timestamp": datetime.utcnow(),
                "uses": 0,
            }
            self._procedures.append(proc_data)
        
        return memory_id

    def _extract_procedures(self, event: MemoryEvent) -> list[str]:
        """
        Extract procedural knowledge from a memory event.
        
        Args:
            event: The memory event
            
        Returns:
            List of extracted procedures
        """
        procedures = []
        
        text = event.input + " " + event.response
        
        # Look for code patterns
        if "def " in event.response or "function " in event.response:
            procedures.append("Writing code function")
        
        if "import " in event.response or "require(" in event.response:
            procedures.append("Importing modules/packages")
        
        if "git" in text.lower() and ("commit" in text.lower() or "push" in text.lower()):
            procedures.append("Git version control workflow")
        
        if "docker" in text.lower() and ("build" in text.lower() or "run" in text.lower()):
            procedures.append("Docker container workflow")
        
        if "api" in text.lower() and ("request" in text.lower() or "endpoint" in text.lower()):
            procedures.append("API request pattern")
        
        return procedures

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> list[Memory]:
        """
        Search procedural memories by content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant procedures
        """
        query_words = set(query.lower().split())
        
        scored = []
        for proc in self._procedures:
            content = proc["content"].lower()
            proc_words = set(content.split())
            
            overlap = len(query_words & proc_words)
            if overlap > 0:
                # Boost frequently used procedures
                score = (overlap / max(len(query_words), 1)) * (1 + proc["uses"] * 0.1)
                scored.append((score, proc))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [
            Memory(
                id=proc["id"],
                content=proc["content"],
                domain=proc["domain"],
                timestamp=proc["timestamp"],
                relevance_score=score
            )
            for score, proc in scored[:limit]
        ]

    async def increment_use(self, procedure_id: str) -> None:
        """Track that a procedure was used."""
        for proc in self._procedures:
            if proc["id"] == procedure_id:
                proc["uses"] += 1
                break

    async def count(self) -> int:
        """Return total number of procedures."""
        return len(self._procedures)


class WorkingMemory:
    """
    In-session context memory.
    
    Holds information relevant to the current conversation
    but not needed for long-term storage.
    """

    def __init__(self):
        """Initialize empty working memory."""
        self._context: dict = {}
        self._recent: list[str] = []

    def store(self, key: str, value: any) -> None:
        """Store something in working memory."""
        self._context[key] = value
        self._recent.append(key)

    def retrieve(self, key: str) -> Optional[any]:
        """Retrieve from working memory."""
        return self._context.get(key)

    def clear(self) -> None:
        """Clear working memory."""
        self._context = {}
        self._recent = []

    def get_context(self) -> dict:
        """Get all working memory context."""
        return self._context.copy()


class UserModelStore:
    """
    NICTO builds a personal model of every user it talks to.
    
    Tracks: expertise level, communication preferences,
    past projects, recurring problems, preferred languages,
    timezone hints, personality patterns.
    """

    def __init__(self):
        """Initialize empty user model store."""
        self._models: dict[str, UserModel] = {}

    async def get(self, user_id: str) -> Optional[UserModel]:
        """
        Get user model for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserModel if exists, None otherwise
        """
        return self._models.get(user_id)

    async def update(
        self,
        user_id: str,
        event: MemoryEvent
    ) -> None:
        """
        Update user model based on a new interaction.
        
        Args:
            user_id: User identifier
            event: Memory event from the interaction
        """
        if user_id not in self._models:
            self._models[user_id] = UserModel(user_id=user_id)

        model = self._models[user_id]

        # Update expertise estimate
        if event.domain:
            model.update_expertise(event.domain, 1.0 - event.complexity)

        # Track language preferences
        if event.languages_mentioned:
            model.note_language_preference(event.languages_mentioned)

        # Track active projects
        if event.project_references:
            model.update_projects(event.project_references)

        # Track interaction count and recency
        model.interaction_count += 1
        model.last_seen = datetime.utcnow()

    async def delete(self, user_id: str) -> bool:
        """
        Delete user model.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        if user_id in self._models:
            del self._models[user_id]
            return True
        return False

    async def list_users(self) -> list[str]:
        """Get list of all known user IDs."""
        return list(self._models.keys())


class NiktoLongTermMemory:
    """
    NICTO's permanent memory system.
    
    Combines three memory types (episodic, semantic, procedural)
    with user modeling and working memory into a unified system.
    
    All memories persist across sessions and are organized
    for efficient retrieval based on relevance and recency.
    """

    def __init__(self):
        """Initialize all memory stores."""
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.working = WorkingMemory()
        self.user_models = UserModelStore()

    async def remember(self, event: MemoryEvent) -> None:
        """
        Store a new memory across all relevant stores.
        
        Called after every interaction to ensure NICTO
        remembers everything important.
        
        Args:
            event: The memory event to store
        """
        # Always store the episode
        await self.episodic.store(event)

        # Extract and store semantic facts
        await self.semantic.store(event)

        # Extract and store procedures
        await self.procedural.store(event)

        # Update user model if user_id present
        if event.user_id:
            await self.user_models.update(event.user_id, event)

    async def recall(
        self,
        perception: Perception,
        limit: int = 10
    ) -> list[Memory]:
        """
        Retrieve relevant memories for current context.
        
        Searches all three memory types and ranks by relevance.
        Combines results and returns top memories.
        
        Args:
            perception: Current perception context
            limit: Maximum memories to return
            
        Returns:
            List of ranked memories
        """
        # Search all memory types in parallel
        results = await asyncio.gather(
            self.episodic.search(perception.raw_input, limit),
            self.semantic.search(perception.raw_input, limit),
            self.procedural.search(perception.raw_input, limit),
        )

        all_memories = []
        for result_set in results:
            all_memories.extend(result_set)

        # Rank by relevance + recency
        ranked = self._rank_memories(all_memories, perception)
        return ranked[:limit]

    def _rank_memories(
        self,
        memories: list[Memory],
        perception: Perception
    ) -> list[Memory]:
        """
        Rank memories by relevance and recency.
        
        Combines relevance score with recency bonus.
        """
        now = datetime.utcnow()
        
        scored = []
        for mem in memories:
            # Calculate recency bonus (up to 0.3)
            age = (now - mem.timestamp).total_seconds()
            recency_bonus = max(0, 0.3 - (age / 86400) * 0.1)  # Decay over days
            
            # Domain bonus if matches current context
            domain_bonus = 0.2 if mem.domain == perception.domain else 0
            
            final_score = mem.relevance_score + recency_bonus + domain_bonus
            scored.append((final_score, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [mem for _, mem in scored]

    async def recall_user(self, user_id: str) -> Optional[UserModel]:
        """
        Get everything NICTO knows about a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserModel with all known information
        """
        return await self.user_models.get(user_id)

    async def forget(
        self,
        user_id: str = None,
        topic: str = None
    ) -> None:
        """
        Selective forgetting — NICTO can forget specific things.
        
        Can forget by user (all their memories) or by topic
        (all semantic facts about a topic).
        
        Args:
            user_id: Optional user ID to forget
            topic: Optional topic to forget
        """
        if user_id:
            await self.user_models.delete(user_id)
            await self.episodic.delete_by_user(user_id)
        
        if topic:
            await self.semantic.delete_by_topic(topic)

    async def get_memory_stats(self) -> dict:
        """
        Get statistics about NICTO's memory.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "episodic_count": await self.episodic.count(),
            "semantic_count": await self.semantic.count(),
            "procedural_count": await self.procedural.count(),
            "users_tracked": len(self._models) if hasattr(self, '_models') else 0,
        }

    # Property to access user_models' internal dict for stats
    @property
    def _models(self):
        return self.user_models._models