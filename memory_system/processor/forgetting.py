"""
ForgettingScheduler - Ebbinghaus Curve Simulation

Manages memory decay based on the Ebbinghaus forgetting curve.
"""
import math
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

from memory_system.layers import RecentLayer, SoulLayer
from memory_system.models import RecentMemory, SoulMemory
import config

logger = logging.getLogger(__name__)


class ForgettingScheduler:
    """
    Implements Ebbinghaus forgetting curve for memory decay.

    Key principle:
    - Memory strength decays exponentially: S = e^(-t/S)
    - S (stability) is derived from importance
    - Important memories decay more slowly

    Schedule:
    - 1h: First review reminder
    - 24h: Second review
    - 7d: Compress to summary
    - 30d: Demote to low priority
    - 90d: Archive or delete
    """

    # Decay thresholds
    STRENGTH_THRESHOLD = 0.3  # Below this, memory is "forgotten"
    COMPRESS_AFTER_DAYS = 7
    DEMOTE_AFTER_DAYS = 30
    ARCHIVE_AFTER_DAYS = 90

    def __init__(
        self,
        recent_layer: RecentLayer,
        soul_layer: SoulLayer
    ):
        self.recent = recent_layer
        self.soul = soul_layer
        self._running = False

    async def start_background_tasks(self):
        """Start background forgetting tasks"""
        self._running = True
        asyncio.create_task(self._decay_loop())
        logger.info("ForgettingScheduler started")

    async def stop(self):
        """Stop the forgetting scheduler"""
        self._running = False

    async def _decay_loop(self):
        """Main decay loop - runs periodically"""
        while self._running:
            try:
                await self._run_decay_check()
            except Exception as e:
                logger.error(f"Error in decay loop: {e}")

            # Run every hour
            await asyncio.sleep(3600)

    async def _run_decay_check(self):
        """
        Run decay check on all recent memories.
        In production, this would batch-process users.
        """
        # This is a simplified version
        # In production, you would:
        # 1. Get all active users
        # 2. For each user, check their recent memories
        # 3. Apply decay to memories older than threshold
        logger.debug("Running decay check")

    def calculate_strength(
        self,
        importance: float,
        hours_elapsed: float
    ) -> float:
        """
        Calculate current memory strength using Ebbinghaus formula.

        Formula: S = e^(-t/S_stability)
        Where stability is derived from importance

        Args:
            importance: 0.0 to 1.0
            hours_elapsed: hours since memory was created

        Returns:
            Strength: 0.0 to 1.0
        """
        # Stability = importance * 10 (important memories last longer)
        stability = max(1.0, importance * 10)

        # Ebbinghaus curve
        strength = math.exp(-hours_elapsed / stability)

        return strength

    def check_and_decay(
        self,
        memory: RecentMemory
    ) -> Optional[float]:
        """
        Check if a memory should decay and apply decay.

        Returns:
            New strength if decayed, None if no decay needed
        """
        if not memory.last_accessed:
            hours_elapsed = (
                datetime.utcnow() - memory.created_at
            ).total_seconds() / 3600
        else:
            hours_elapsed = (
                datetime.utcnow() - memory.last_accessed
            ).total_seconds() / 3600

        current_strength = self.calculate_strength(
            memory.importance_score,
            hours_elapsed
        )

        # Check if below threshold
        if current_strength < self.STRENGTH_THRESHOLD:
            # Memory should be "forgotten"
            return current_strength

        # Apply decay to importance
        new_importance = memory.importance_score * current_strength
        self.recent.update_importance(memory.id, new_importance)

        return current_strength

    def should_compress(self, memory: RecentMemory) -> bool:
        """
        Check if a memory should be compressed.
        Memories older than 7 days should be compressed.
        """
        days_old = (
            datetime.utcnow() - memory.created_at
        ).days

        return days_old >= self.COMPRESS_AFTER_DAYS

    def should_demote(self, memory: SoulMemory) -> bool:
        """
        Check if a soul memory should be demoted.
        Low importance memories are demoted over time.
        """
        # If not accessed for 30+ days and low importance
        if not memory.last_accessed:
            return memory.importance_score < 0.3

        days_since_access = (
            datetime.utcnow() - memory.last_accessed
        ).days

        if days_since_access >= self.DEMOTE_AFTER_DAYS:
            if memory.importance_score < 0.5:
                return True

        return False

    async def decay_all(self, user_id: str) -> dict:
        """
        Run decay on all memories for a user.

        Returns:
            dict with counts of decayed/demoted/archived memories
        """
        result = {
            "recent_decayed": 0,
            "soul_demoted": 0,
            "archived": 0
        }

        # Get all recent memories
        recent_memories = self.recent.get_by_user(user_id, days=365)

        for memory in recent_memories:
            # Check compression
            if self.should_compress(memory):
                # Would trigger compression in compressor
                pass

            # Check decay
            new_strength = self.check_and_decay(memory)
            if new_strength and new_strength < self.STRENGTH_THRESHOLD:
                result["recent_decayed"] += 1

        # Get all soul memories
        soul_memories = self.soul.get_all(user_id)

        for memory in soul_memories:
            if self.should_demote(memory):
                self.soul.demote(memory.id)
                result["soul_demoted"] += 1

        return result

    def get_decay_schedule(self, importance: float) -> dict:
        """
        Get the decay schedule for a given importance.

        Returns approximate days until each milestone.
        """
        stability = max(1.0, importance * 10)

        return {
            "first_review_hours": stability * 1,  # ~1 day for importance 0.5
            "second_review_hours": stability * 5,  # ~5 days
            "compress_days": stability * 7,        # ~7 days
            "demote_days": stability * 30,         # ~30 days
            "archive_days": stability * 90        # ~90 days
        }
