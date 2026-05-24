"""
NiktoKnowledgeCore — NICTO's Internal Knowledge Base.

NICTO's internal knowledge base is its brain's storage.
This is distinct from memory — knowledge is facts and
understanding, memory is experiences and episodes.

Organized into knowledge domains that NICTO maintains
confidence scores for.
"""

import asyncio
from typing import Optional
from uuid import uuid4

from .models import KnowledgeFact, KnowledgeSet, Perception


class KnowledgeVectorStore:
    """
    Vector-based knowledge storage and retrieval.
    
    Uses embedding-based search to find relevant knowledge
    based on semantic similarity to the query.
    
    For simplicity, this uses keyword-based matching as a fallback
    when vector embeddings are not available.
    """

    def __init__(self):
        """Initialize the vector store with empty knowledge base."""
        self._knowledge: list[KnowledgeFact] = []
        self._domain_index: dict[str, list[KnowledgeFact]] = {}

    async def add(self, fact: KnowledgeFact) -> None:
        """
        Add a new knowledge fact to the store.
        
        Args:
            fact: The knowledge fact to store
        """
        self._knowledge.append(fact)
        
        # Index by domain
        if fact.domain not in self._domain_index:
            self._domain_index[fact.domain] = []
        self._domain_index[fact.domain].append(fact)

    async def search(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = 15
    ) -> list[KnowledgeFact]:
        """
        Search for knowledge relevant to a query.
        
        Uses simple keyword matching for now.
        Can be enhanced with actual vector embeddings.
        
        Args:
            query: The search query
            domain: Optional domain filter
            limit: Maximum number of results
            
        Returns:
            List of relevant knowledge facts
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        candidates = []
        if domain and domain in self._domain_index:
            candidates = self._domain_index[domain]
        else:
            candidates = self._knowledge
        
        scored = []
        for fact in candidates:
            fact_words = set(fact.content.lower().split())
            
            # Calculate simple relevance score
            overlap = len(query_words & fact_words)
            if overlap > 0:
                # Score based on word overlap and confidence
                score = overlap * fact.confidence
                scored.append((score, fact))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [fact for _, fact in scored[:limit]]

    async def count(self) -> int:
        """Return total number of knowledge facts."""
        return len(self._knowledge)

    async def get_by_domain(self, domain: str) -> list[KnowledgeFact]:
        """Get all knowledge facts for a domain."""
        return self._domain_index.get(domain, [])


class KnowledgeGraph:
    """
    Graph-based knowledge relationships.
    
    Maintains relationships between concepts, facts, and rules
    to enable traversal and inference.
    """

    def __init__(self):
        """Initialize empty knowledge graph."""
        self._nodes: dict[str, KnowledgeFact] = {}
        self._edges: dict[str, list[str]] = {}
        self._concepts: dict[str, set[str]] = {}

    async def add_node(self, fact: KnowledgeFact) -> None:
        """
        Add a fact to the knowledge graph.
        
        Args:
            fact: The knowledge fact to add
        """
        self._nodes[fact.id] = fact
        
        # Extract concepts from content
        words = fact.content.lower().split()
        for word in words:
            if len(word) > 4:  # Skip short words
                if word not in self._concepts:
                    self._concepts[word] = set()
                self._concepts[word].add(fact.id)

    async def traverse(
        self,
        query: str,
        depth: int = 2
    ) -> list[KnowledgeFact]:
        """
        Traverse the knowledge graph to find related facts.
        
        Args:
            query: The query to traverse for
            depth: How deep to traverse
            
        Returns:
            List of related knowledge facts
        """
        query_words = set(query.lower().split())
        
        # Find initial nodes
        initial_nodes = set()
        for word in query_words:
            if word in self._concepts:
                initial_nodes.update(self._concepts[word])
        
        results = []
        for node_id in initial_nodes:
            if node_id in self._nodes:
                results.append(self._nodes[node_id])
        
        return results[:20]  # Limit results

    async def find_related(self, fact_id: str) -> list[KnowledgeFact]:
        """Find facts related to a specific fact."""
        if fact_id not in self._edges:
            return []
        
        related_ids = self._edges[fact_id]
        return [
            self._nodes[nid]
            for nid in related_ids
            if nid in self._nodes
        ]


class NiktoKnowledgeCore:
    """
    NICTO's internal knowledge base.
    
    Contains domain knowledge, facts, relationships,
    concepts, patterns, and rules NICTO uses to reason.
    
    Organized into knowledge domains with confidence scores:
    - cybersecurity
    - programming
    - ai_ml
    - mathematics
    - network_engineering
    - cryptography
    - game_development
    - system_administration
    - cloud_infrastructure
    - data_science
    - electronics_iot
    - general_world_knowledge
    
    Knowledge is retrieved based on perception context and
    ranked by relevance and confidence.
    """

    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        """Initialize NICTO's knowledge core with domain confidence."""
        self.vector_store = KnowledgeVectorStore()
        self.fact_graph = KnowledgeGraph()
        
        # Domain confidence scores (0.0 to 1.0)
        # NICTO is more confident in some domains than others
        self.domain_confidence = {
            "cybersecurity": 0.95,
            "programming": 0.95,
            "ai_ml": 0.90,
            "mathematics": 0.85,
            "network_engineering": 0.90,
            "cryptography": 0.90,
            "game_development": 0.85,
            "system_administration": 0.90,
            "cloud_infrastructure": 0.80,
            "data_science": 0.85,
            "electronics_iot": 0.75,
            "general_world_knowledge": 0.70,
        }
        
        # Initialize with foundational knowledge BEFORE setting references
        self._init_foundation_knowledge()
        
        # Reference to the vector store's knowledge list (after init)
        self._knowledge = self.vector_store._knowledge
        self._domain_index = self.vector_store._domain_index

    def _init_foundation_knowledge(self) -> None:
        """
        Initialize NICTO with foundational knowledge.
        
        This ensures NICTO has basic knowledge about its
        own capabilities and common domains.
        """
        foundation_facts = [
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="NICTO is a self-contained artificial intelligence with reasoning, memory, and learning",
                domain="ai_ml",
                confidence=0.95,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="SQL injection is a common web vulnerability that allows attackers to execute malicious SQL",
                domain="cybersecurity",
                confidence=0.95,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="XSS (Cross-Site Scripting) allows injection of malicious scripts into web pages",
                domain="cybersecurity",
                confidence=0.95,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="Python is a high-level programming language with dynamic semantics",
                domain="programming",
                confidence=0.95,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="Docker containers provide lightweight isolation for applications",
                domain="cloud_infrastructure",
                confidence=0.90,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="HTTPS uses TLS to encrypt communication between client and server",
                domain="network_engineering",
                confidence=0.95,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="AES is a symmetric encryption algorithm widely used for data encryption",
                domain="cryptography",
                confidence=0.95,
                source="system"
            ),
            KnowledgeFact(
                id=str(uuid4())[:12],
                content="Machine learning models learn patterns from data to make predictions",
                domain="ai_ml",
                confidence=0.90,
                source="system"
            ),
        ]
        
        # Add all foundation facts to vector_store directly
        for fact in foundation_facts:
            self.vector_store._knowledge.append(fact)
            if fact.domain not in self.vector_store._domain_index:
                self.vector_store._domain_index[fact.domain] = []
            self.vector_store._domain_index[fact.domain].append(fact)

    async def retrieve(
        self,
        perception: Perception,
        limit: int = 15
    ) -> KnowledgeSet:
        """
        Retrieve relevant knowledge for a given perception.
        
        Searches the vector store and knowledge graph for
        relevant facts and returns them with coverage score.
        
        Args:
            perception: The perception to retrieve knowledge for
            limit: Maximum number of knowledge items to return
            
        Returns:
            KnowledgeSet with relevant facts and coverage score
        """
        domain = perception.domain
        query = perception.raw_input
        
        # Search vector store
        vector_results = await self.vector_store.search(
            query, domain, limit
        )
        
        # Search knowledge graph for related concepts
        graph_results = await self.fact_graph.traverse(query, depth=2)
        
        # Combine and deduplicate
        all_knowledge = self._merge_results(vector_results, graph_results)
        
        # Filter by confidence threshold
        confident_knowledge = [
            k for k in all_knowledge
            if k.confidence >= self.CONFIDENCE_THRESHOLD
        ]
        
        # Identify gaps
        gaps = self._identify_gaps(query, confident_knowledge)
        
        # Calculate coverage score
        coverage_score = len(confident_knowledge) / max(limit, 1)
        
        return KnowledgeSet(
            items=confident_knowledge[:limit],
            domain=domain,
            coverage_score=coverage_score,
            gaps=gaps
        )

    def _merge_results(
        self,
        vector_results: list[KnowledgeFact],
        graph_results: list[KnowledgeFact]
    ) -> list[KnowledgeFact]:
        """
        Merge and deduplicate results from multiple sources.
        
        Args:
            vector_results: Results from vector store
            graph_results: Results from knowledge graph
            
        Returns:
            Deduplicated list of knowledge facts
        """
        seen_ids = set()
        merged = []
        
        # Add vector results first (usually more relevant)
        for fact in vector_results:
            if fact.id not in seen_ids:
                seen_ids.add(fact.id)
                merged.append(fact)
        
        # Add graph results that aren't duplicates
        for fact in graph_results:
            if fact.id not in seen_ids:
                seen_ids.add(fact.id)
                merged.append(fact)
        
        return merged

    def _identify_gaps(
        self,
        query: str,
        knowledge: list[KnowledgeFact]
    ) -> list[str]:
        """
        Identify gaps in knowledge coverage.
        
        Analyzes the query and existing knowledge to identify
        areas where NICTO may be lacking information.
        
        Args:
            query: The original query
            knowledge: Existing knowledge for the query
            
        Returns:
            List of identified knowledge gaps
        """
        gaps = []
        
        # Check for technical terms not covered
        technical_indicators = [
            "how to", "what is", "why does", "explain",
            "implement", "create", "build", "design"
        ]
        
        has_technical = any(t in query.lower() for t in technical_indicators)
        
        if has_technical and len(knowledge) < 3:
            gaps.append(f"Limited knowledge for technical query: {query[:50]}...")
        
        # Check for recent/new topics (would need web search in full implementation)
        recent_indicators = [
            "2024", "2025", "latest", "new version", "recent"
        ]
        
        has_recent = any(r in query for r in recent_indicators)
        
        if has_recent:
            gaps.append("Query references recent information that may be outdated")
        
        return gaps

    async def learn(self, fact: KnowledgeFact) -> None:
        """
        Add new knowledge to the core.
        
        Called when NICTO learns something new from an interaction
        or external source.
        
        Args:
            fact: The new knowledge fact to add
        """
        await self.vector_store.add(fact)
        await self.fact_graph.add_node(fact)
        
        # Update domain confidence based on new learning
        if fact.domain in self.domain_confidence:
            # Slightly increase confidence when learning new facts
            self.domain_confidence[fact.domain] = min(
                0.99,
                self.domain_confidence[fact.domain] + 0.01
            )

    def get_domain_confidence(self, domain: str) -> float:
        """
        Get confidence level for a specific domain.
        
        Args:
            domain: The domain to get confidence for
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        return self.domain_confidence.get(domain, 0.5)

    def set_domain_confidence(self, domain: str, confidence: float) -> None:
        """
        Set confidence level for a specific domain.
        
        Used by the learning system to adjust domain confidence
        based on performance.
        
        Args:
            domain: The domain to set confidence for
            confidence: New confidence level (0.0 to 1.0)
        """
        self.domain_confidence[domain] = max(0.0, min(1.0, confidence))

    async def get_domain_knowledge(self, domain: str) -> list[KnowledgeFact]:
        """
        Get all knowledge for a specific domain.
        
        Args:
            domain: The domain to get knowledge for
            
        Returns:
            List of knowledge facts in the domain
        """
        return await self.vector_store.get_by_domain(domain)

    async def get_all_domains(self) -> list[str]:
        """Get list of all known domains."""
        return list(self.domain_confidence.keys())

    def get_knowledge_stats(self) -> dict:
        """
        Get statistics about NICTO's knowledge.
        
        Returns:
            Dictionary with knowledge statistics
        """
        return {
            "total_facts": asyncio.run(self.vector_store.count()),
            "domains": list(self.domain_confidence.keys()),
            "domain_confidence": self.domain_confidence.copy(),
        }