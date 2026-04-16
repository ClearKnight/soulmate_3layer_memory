"""
Promoter - Memory Promotion

Decides which memories should be promoted from Recent to Soul layer.
"""
from datetime import datetime

from memory_system.layers import RecentLayer, SoulLayer
from memory_system.models import RecentMemory, SoulMemory, MemoryType, PromotionDecision
import config


class Promoter:
    """
    Decides when to promote recent memories to soul layer.

    Promotion criteria:
    1. Access count >= 3 (mentioned multiple times)
    2. Importance score >= threshold (0.7)
    3. Emotional weight >= 0.5 (has emotional significance)

    Also handles demotion of soul memories when they become less relevant.
    """

    # Promotion thresholds
    ACCESS_COUNT_THRESHOLD = 3
    IMPORTANCE_THRESHOLD = config.SOUL_MEMORY_IMPORTANCE_THRESHOLD  # 0.7
    EMOTIONAL_THRESHOLD = 0.5

    def __init__(
        self,
        recent_layer: RecentLayer,
        soul_layer: SoulLayer
    ):
        self.recent = recent_layer
        self.soul = soul_layer

    def should_promote(self, memory: RecentMemory) -> PromotionDecision:
        """
        Determine if a recent memory should be promoted to soul layer.

        Args:
            memory: RecentMemory to evaluate

        Returns:
            PromotionDecision with should_promote flag and reason
        """
        reasons = []
        checks_passed = 0

        # Check 1: Access count
        if memory.access_count >= self.ACCESS_COUNT_THRESHOLD:
            checks_passed += 1
            reasons.append(f"访问次数={memory.access_count}>=3")
        else:
            reasons.append(f"访问次数={memory.access_count}<3")

        # Check 2: Importance
        if memory.importance_score >= self.IMPORTANCE_THRESHOLD:
            checks_passed += 1
            reasons.append(f"重要性={memory.importance_score:.2f}>=0.7")
        else:
            reasons.append(f"重要性={memory.importance_score:.2f}<0.7")

        # Check 3: Emotional weight
        if memory.emotional_weight >= self.EMOTIONAL_THRESHOLD:
            checks_passed += 1
            reasons.append(f"情感权重={memory.emotional_weight:.2f}>=0.5")
        else:
            reasons.append(f"情感权重={memory.emotional_weight:.2f}<0.5")

        should_promote = checks_passed >= 2  # At least 2 of 3

        return PromotionDecision(
            memory_id=memory.id,
            should_promote=should_promote,
            reason="; ".join(reasons),
            confidence=checks_passed / 3
        )

    def promote(self, memory: RecentMemory) -> SoulMemory:
        """
        Promote a recent memory to soul layer.

        Args:
            memory: RecentMemory to promote

        Returns:
            Created SoulMemory
        """
        # Determine memory type from content
        memory_type = self._classify_memory(memory.summary, memory.topics)

        # Create soul memory
        soul_memory = SoulMemory(
            user_id=memory.user_id,
            memory_type=memory_type,
            content={
                "original_summary": memory.summary,
                "original_topics": memory.topics,
                "promoted_from": memory.id
            },
            importance_score=memory.importance_score,
            emotional_weight=memory.emotional_weight
        )

        self.soul.save(soul_memory)

        # Increment access to mark as recently accessed
        self.soul.increment_access(soul_memory.id)

        return soul_memory

    def check_and_promote(self, memory: RecentMemory) -> PromotionDecision:
        """
        Check if memory should promote and promote if yes.

        Returns:
            PromotionDecision (with promoted=True if actually promoted)
        """
        decision = self.should_promote(memory)

        if decision.should_promote:
            self.promote(memory)

        return decision

    def process_user_memories(self, user_id: str) -> dict:
        """
        Process all recent memories for a user, promoting as needed.

        Returns:
            dict with promotion stats
        """
        recent_memories = self.recent.get_by_user(user_id, days=365)

        promoted = 0
        skipped = 0

        for memory in recent_memories:
            decision = self.should_promote(memory)
            if decision.should_promote:
                self.promote(memory)
                promoted += 1
            else:
                skipped += 1

        return {
            "processed": len(recent_memories),
            "promoted": promoted,
            "skipped": skipped
        }

    def _classify_memory(self, summary: str, topics: list[str]) -> MemoryType:
        """
        Classify memory type for soul layer storage.
        """
        summary_lower = summary.lower()

        if any(w in summary_lower for w in ["喜欢", "爱好", "prefer", "like"]):
            return MemoryType.PREFERENCE
        elif any(w in summary_lower for w in ["觉得", "认为", "价值", "believe"]):
            return MemoryType.VALUE
        elif any(w in summary_lower for w in ["每次", "经常", "总是", "习惯", "habit"]):
            return MemoryType.HABIT
        elif any(w in summary_lower for w in ["记得", "那次", "重要", "happened"]):
            return MemoryType.IMPORTANT_EVENT
        elif topics:
            return MemoryType.PREFERENCE
        else:
            return MemoryType.RELATIONSHIP

    def demote_low_importance(self, user_id: str) -> int:
        """
        Demote soul memories with low importance and low access.

        Returns:
            Number of memories demoted
        """
        all_soul = self.soul.get_all(user_id)

        demoted = 0
        for memory in all_soul:
            # If low importance and not accessed recently
            if memory.importance_score < 0.3:
                self.soul.demote(memory.id)
                demoted += 1

        return demoted
