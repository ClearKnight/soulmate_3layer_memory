"""
Collector - Memory Collection

Collects memories from agent events and routes them to appropriate layers.
"""
from typing import Optional
from datetime import datetime

from memory_system.models import (
    MemoryInput,
    MemoryType,
    RecentMemory,
    SoulMemory,
    ShortTermContext,
)
from memory_system.layers import ShortLayer, RecentLayer, SoulLayer
from memory_system.embedding import get_embedding_service


class Collector:
    """
    Collects memories from agent events and routes them to appropriate layers.

    Decision logic:
    - importance > 0.7 → Direct to Soul layer
    - importance > 0.3 → Recent layer (may be promoted later)
    - importance <= 0.3 → Short layer only (session only)
    """

    # Emotional keywords for simple sentiment analysis
    POSITIVE_WORDS = {"开心", "高兴", "棒", "好开心", "冲", "兴奋", "love", "happy", "great", "good", "太好了"}
    NEGATIVE_WORDS = {"难过", "伤心", "累", "气", "烦", "压力", "sad", "angry", "tired", "stressed", "讨厌"}

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

    async def collect(
        self,
        user_id: str,
        session_id: str,
        content: str,
        event_type: str = "user_said",
        emotion: Optional[str] = None,
        topics: list[str] = [],
        metadata: dict = {}
    ) -> dict:
        """
        Collect a memory event.

        Returns:
            dict with: memory_id, layer ("short", "recent", "soul"), stored
        """
        # 1. Analyze emotion
        emotional_score = self._analyze_emotion(content, emotion)

        # 2. Estimate importance
        importance = self._estimate_importance(
            content=content,
            emotional_score=emotional_score,
            topics=topics,
            event_type=event_type
        )

        # 3. Route to appropriate layer
        if importance > 0.7:
            # High importance → Direct to Soul
            memory = SoulMemory(
                user_id=user_id,
                memory_type=self._classify_memory_type(content, topics),
                content={
                    "text": content,
                    "topics": topics,
                    "metadata": metadata
                },
                importance_score=importance,
                emotional_weight=emotional_score
            )

            # Generate and store embedding
            embeddings = await self.embedding_service.embed([content])
            if embeddings and embeddings[0]:
                self.soul.save_with_embedding(memory, embeddings[0])
            else:
                self.soul.save(memory)

            # Also save to short for current session
            await self.short.append_message(
                user_id=user_id,
                session_id=session_id,
                role=event_type,
                content=content,
                emotion=emotion or self._score_to_emotion(emotional_score),
                topic=topics[0] if topics else None
            )

            return {
                "memory_id": memory.id,
                "layer": "soul",
                "stored": True
            }

        elif importance > 0.3:
            # Medium importance → Recent layer
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Check if today's summary exists
            existing = self.recent.get_today(user_id)

            if existing:
                # Append to existing summary
                existing.summary += f"\n{content}"
                existing.topics = list(set(existing.topics + topics))
                existing.emotional_weight = (
                    existing.emotional_weight * 0.7 + emotional_score * 0.3
                )
                # Re-generate embedding for updated content
                embeddings = await self.embedding_service.embed([existing.summary])
                if embeddings and embeddings[0]:
                    self.recent.save_with_embedding(existing, embeddings[0])
                else:
                    self.recent.save(existing)
                memory_id = existing.id
            else:
                # Create new recent memory
                memory = RecentMemory(
                    user_id=user_id,
                    date=today,
                    summary=content,
                    emotion=emotion or self._score_to_emotion(emotional_score),
                    topics=topics,
                    importance_score=importance,
                    emotional_weight=emotional_score
                )
                # Generate and store embedding
                embeddings = await self.embedding_service.embed([content])
                if embeddings and embeddings[0]:
                    self.recent.save_with_embedding(memory, embeddings[0])
                else:
                    self.recent.save(memory)
                memory_id = memory.id

            # Also save to short
            await self.short.append_message(
                user_id=user_id,
                session_id=session_id,
                role=event_type,
                content=content,
                emotion=emotion or self._score_to_emotion(emotional_score),
                topic=topics[0] if topics else None
            )

            return {
                "memory_id": memory_id,
                "layer": "recent",
                "stored": True
            }

        else:
            # Low importance → Short layer only
            context = await self.short.append_message(
                user_id=user_id,
                session_id=session_id,
                role=event_type,
                content=content,
                emotion=emotion or self._score_to_emotion(emotional_score),
                topic=topics[0] if topics else None
            )

            return {
                "memory_id": context.session_id,
                "layer": "short",
                "stored": True
            }

    def _analyze_emotion(
        self,
        content: str,
        emotion: Optional[str]
    ) -> float:
        """
        Analyze emotional score from content.
        Returns 0.0 (negative) to 1.0 (positive).
        """
        # Use provided emotion if available
        if emotion:
            if emotion in ("positive", "positive"):
                return 0.8
            elif emotion in ("negative", "neg"):
                return 0.2
            return 0.5

        # Simple keyword-based analysis
        content_lower = content.lower()
        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in content_lower)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in content_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.5

        return pos_count / total

    def _estimate_importance(
        self,
        content: str,
        emotional_score: float,
        topics: list[str],
        event_type: str
    ) -> float:
        """
        Estimate importance score (0.0 to 1.0).

        Factors:
        - Emotional intensity (deviation from 0.5)
        - Presence of important topics
        - Event type
        """
        # Emotional intensity (0.0 to 0.5)
        emotional_intensity = abs(emotional_score - 0.5) * 2  # 0.0 to 1.0

        # Event type modifier
        event_weights = {
            "user_said": 0.5,
            "agent_response": 0.3,
            "user_feedback": 0.7,
            "system_event": 0.6
        }
        event_weight = event_weights.get(event_type, 0.5)

        # Important topics
        important_topics = {"工作", "健康", "感情", "家庭", "朋友", "梦想", "目标", "未来"}
        topic_bonus = 0.1 if any(t in important_topics for t in topics) else 0.0

        # Calculate score
        score = (
            emotional_intensity * 0.3 +
            event_weight * 0.4 +
            topic_bonus
        )

        return min(1.0, max(0.0, score))

    def _classify_memory_type(self, content: str, topics: list[str]) -> MemoryType:
        """
        Classify memory type based on content.
        """
        content_lower = content.lower()

        # Simple classification based on keywords
        if any(w in content_lower for w in ["喜欢", "偏好", "爱好", "prefer", "like"]):
            return MemoryType.PREFERENCE
        elif any(w in content_lower for w in ["觉得", "认为", "价值观", "相信", "value", "believe"]):
            return MemoryType.VALUE
        elif any(w in content_lower for w in ["每次都", "经常", "总是", "习惯", "habit", "always"]):
            return MemoryType.HABIT
        elif any(w in content_lower for w in ["记得", "那次", "发生", "happened", "remember"]):
            return MemoryType.IMPORTANT_EVENT
        elif topics:
            # Default to preference if topics exist
            return MemoryType.PREFERENCE
        else:
            return MemoryType.RELATIONSHIP

    def _score_to_emotion(self, score: float) -> str:
        """Convert numeric score to emotion label"""
        if score > 0.6:
            return "positive"
        elif score < 0.4:
            return "negative"
        return "neutral"
