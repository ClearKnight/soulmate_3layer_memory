"""
Retriever - Memory Retrieval

Retrieves and fuses context from all three memory layers.
"""
import asyncio
from typing import Optional

from memory_system.layers import ShortLayer, RecentLayer, SoulLayer
from memory_system.models import RetrievedContext, RetrievedMemory, ShortTermContext
from memory_system.embedding import get_embedding_service
import config


class Retriever:
    """
    Retrieves context from all three memory layers and fuses them.

    Key features:
    - Vector-based semantic search (MiniMax embeddings)
    - Text search fallback
    - Weighted scoring (relevance × importance)
    - Context window management (token limit)
    """

    def __init__(
        self,
        short_layer: ShortLayer,
        recent_layer: RecentLayer,
        soul_layer: SoulLayer
    ):
        self.short = short_layer
        self.recent = recent_layer
        self.soul = soul_layer
        self.embedding_service = get_embedding_service()

    async def retrieve(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        max_memories: int = 10
    ) -> RetrievedContext:
        """
        Retrieve combined context from all layers using vector search.

        Args:
            user_id: User ID
            query: Current query/context request
            session_id: Optional session ID for short-term context
            max_memories: Max memories to return per layer

        Returns:
            RetrievedContext with memories from all layers
        """
        # Generate query embedding
        embeddings = await self.embedding_service.embed([query])
        query_embedding = embeddings[0] if embeddings else None

        # Soul layer search (vector + text fallback)
        soul_results = self._get_soul_memories_sync(user_id, query, query_embedding, max_memories)

        # Recent layer search (vector + text fallback)
        recent_results = self._get_recent_memories_sync(user_id, query, query_embedding, max_memories)

        # Short layer (if session_id provided)
        short_context = None
        if session_id:
            short_context = await self.short.get_context(user_id, session_id)

        # Score and rank memories
        scored_soul = self._score_memories(soul_results, layer="soul")
        scored_recent = self._score_memories(recent_results, layer="recent")

        # Combine and sort
        all_scored = scored_soul + scored_recent
        all_scored.sort(key=lambda x: x[0], reverse=True)  # Sort by score

        # Take top memories
        top_soul = [m for s, m, l in all_scored if l == "soul"][:5]
        top_recent = [m for s, m, l in all_scored if l == "recent"][:3]

        return RetrievedContext(
            user_id=user_id,
            query=query,
            soul_memories=top_soul,
            recent_memories=top_recent,
            short_context=short_context,
            total_context_window=config.SHORT_TERM_MAX_MESSAGES * 50  # Rough token estimate
        )

    def _get_soul_memories_sync(
        self,
        user_id: str,
        query: str,
        query_embedding: Optional[list[float]],
        top_k: int
    ) -> list[RetrievedMemory]:
        """Get and score soul memories with vector search"""
        results = []

        # Try vector search first
        if query_embedding:
            vector_results = self.soul.search_with_vector(user_id, query_embedding, top_k)
            for memory, similarity in vector_results:
                results.append(
                    RetrievedMemory(
                        memory_id=memory.id,
                        memory_type="soul",
                        content=memory.content,
                        relevance_score=similarity,
                        importance_score=memory.importance_score,
                        last_accessed=memory.last_accessed
                    )
                )
                self.soul.increment_access(memory.id)

        # Fallback to text search if no vector results or supplement
        if len(results) < top_k:
            text_results = self.soul.search(user_id, query, top_k)
            for memory in text_results:
                # Skip if already in results
                if not any(r.memory_id == memory.id for r in results):
                    results.append(
                        RetrievedMemory(
                            memory_id=memory.id,
                            memory_type="soul",
                            content=memory.content,
                            relevance_score=0.5,  # Lower score for text match
                            importance_score=memory.importance_score,
                            last_accessed=memory.last_accessed
                        )
                    )
                    self.soul.increment_access(memory.id)

        return results[:top_k]

    def _get_recent_memories_sync(
        self,
        user_id: str,
        query: str,
        query_embedding: Optional[list[float]],
        top_k: int
    ) -> list[RetrievedMemory]:
        """Get and score recent memories with vector search"""
        results = []

        # Try vector search first
        if query_embedding:
            vector_results = self.recent.search_with_vector(user_id, query_embedding, top_k)
            for memory, similarity in vector_results:
                results.append(
                    RetrievedMemory(
                        memory_id=memory.id,
                        memory_type="recent",
                        content={
                            "summary": memory.summary,
                            "topics": memory.topics,
                            "emotion": memory.emotion
                        },
                        relevance_score=similarity,
                        importance_score=memory.importance_score,
                        last_accessed=memory.last_accessed
                    )
                )
                self.recent.increment_access(memory.id)

        # Fallback to text search if no vector results or supplement
        if len(results) < top_k:
            text_results = self.recent.search(user_id, query, top_k)
            for memory in text_results:
                # Skip if already in results
                if not any(r.memory_id == memory.id for r in results):
                    results.append(
                        RetrievedMemory(
                            memory_id=memory.id,
                            memory_type="recent",
                            content={
                                "summary": memory.summary,
                                "topics": memory.topics,
                                "emotion": memory.emotion
                            },
                            relevance_score=0.5,  # Lower score for text match
                            importance_score=memory.importance_score,
                            last_accessed=memory.last_accessed
                        )
                    )
                    self.recent.increment_access(memory.id)

        return results[:top_k]

    async def _get_short_context(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[ShortTermContext]:
        """Get short-term context"""
        return await self.short.get_context(user_id, session_id)

    def _score_memories(
        self,
        memories: list[RetrievedMemory],
        layer: str
    ) -> list[tuple[float, RetrievedMemory, str]]:
        """
        Score memories with weighted formula.

        Soul layer: importance_weight=0.7, relevance_weight=0.3
        Recent layer: importance_weight=0.4, relevance_weight=0.6
        """
        if layer == "soul":
            importance_weight = 0.7
            relevance_weight = 0.3
        else:
            importance_weight = 0.4
            relevance_weight = 0.6

        scored = []
        for memory in memories:
            score = (
                memory.relevance_score * relevance_weight +
                memory.importance_score * importance_weight
            )
            scored.append((score, memory, layer))

        return scored

    def format_context_text(self, context: RetrievedContext) -> str:
        """
        Format retrieved context as text for LLM consumption.

        Returns a formatted string with all relevant memories.
        """
        parts = []

        # Soul memories (core preferences)
        if context.soul_memories:
            parts.append("【关于你的核心信息】")
            for memory in context.soul_memories:
                if isinstance(memory.content, dict):
                    text = memory.content.get("text", str(memory.content))
                else:
                    text = str(memory.content)
                parts.append(f"• {text[:100]}")
            parts.append("")

        # Recent memories (last 3 days)
        if context.recent_memories:
            parts.append("【最近聊过】")
            for memory in context.recent_memories:
                if isinstance(memory.content, dict):
                    summary = memory.content.get("summary", str(memory.content))
                else:
                    summary = str(memory.content)
                parts.append(f"• {summary[:80]}")
            parts.append("")

        # Short context (current session)
        if context.short_context:
            parts.append("【当前对话】")
            for msg in context.short_context.messages[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                parts.append(f"{role}: {content[:50]}")
            parts.append("")

        return "\n".join(parts) if parts else "（目前记忆较少）"
