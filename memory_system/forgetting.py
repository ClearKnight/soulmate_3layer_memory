"""
Forgetting Scheduler - Memory Consolidation and Forgetting

This module handles the scheduling of memory consolidation,
forgetting, and promotion between layers.

Based on the Ebbinghaus forgetting curve and human memory consolidation patterns.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

from memory_system.memory_interface import MemorySystem
from memory_system.models import MemoryType, MemoryGraphEvent
from memory_system.soul_service import SoulLayerService
from memory_system.recent_service import RecentLayerService

logger = logging.getLogger(__name__)


class ForgettingScheduler:
    """
    Scheduler for memory consolidation and forgetting.

    Key principles:
    - Memories are strengthened when accessed
    - Memories fade if not accessed
    - Important memories are promoted to soul layer
    - Low-importance memories are eventually archived
    """

    # Timing constants (in days)
    COMPRESS_AFTER_DAYS = 7
    DEMOTE_AFTER_DAYS = 30
    ARCHIVE_AFTER_DAYS = 90

    # Importance thresholds
    SOUL_PROMOTION_THRESHOLD = 0.7
    DORMANT_THRESHOLD = 0.3

    def __init__(self, memory_system: MemorySystem):
        self.ms = memory_system
        self.soul_service = SoulLayerService(memory_system)
        self.recent_service = RecentLayerService(memory_system)
        self._running = False

    async def start_background_tasks(self):
        """Start background tasks for forgetting schedule"""
        self._running = True

        # Run forgetting check every hour
        asyncio.create_task(self._forgetting_loop())

        logger.info("Forgetting scheduler started")

    async def stop(self):
        """Stop the forgetting scheduler"""
        self._running = False

    async def _forgetting_loop(self):
        """Main forgetting loop - runs periodically"""
        while self._running:
            try:
                await self._run_consolidation()
            except Exception as e:
                logger.error(f"Error in forgetting loop: {e}")

            # Wait 1 hour before next check
            await asyncio.sleep(3600)

    async def _run_consolidation(self):
        """Run memory consolidation tasks"""
        # This would typically:
        # 1. Get all active users
        # 2. For each user, check their memories for consolidation

        # For MVP, we'll just log that it's running
        logger.debug("Running memory consolidation check")

        # In production, this would:
        # - Check recent memories older than 7 days
        # - Compress them to summaries
        # - Check soul memories for importance decay
        # - Archive old memories

    async def compress_recent_to_summary(
        self,
        user_id: str,
        days: int = 7
    ):
        """
        Compress recent memories older than N days into summaries.

        Called by background scheduler, not on every interaction.
        """
        memories = await self.ms.retrieve_recent_memories(user_id, days=days)

        if len(memories) < 2:
            return None

        # In production, this would use an LLM to generate a summary
        # For now, simple concatenation
        summaries = [m.summary for m in memories]
        combined_summary = " ".join(summaries)

        # Create a memory graph event
        event = await self.ms.add_memory_graph_event(
            user_id=user_id,
            event_type="memory_compression",
            content={
                "action": "compressed_recent_memories",
                "count": len(memories),
                "result": combined_summary[:500]  # Truncate
            }
        )

        return combined_summary

    async def promote_to_soul_layer(
        self,
        user_id: str,
        source_memory_id: str,
        compressed_content: dict
    ):
        """
        Promote an important recent memory to the soul layer.

        Called when a memory has been accessed frequently enough
        and has high enough importance to become a permanent memory.
        """
        # Get the original memory
        soul_memories = await self.ms.retrieve_soul_memories(
            user_id, top_k=100
        )

        # Check if this content already exists
        for mem in soul_memories:
            if mem.id == source_memory_id:
                # Already promoted
                return mem

        # Create new soul memory from the recent memory
        promoted = await self.ms.store_soul_memory(
            user_id=user_id,
            memory_type=MemoryType.IMPORTANT_MEMORY,
            content=compressed_content,
            importance=0.8  # High importance for promoted memories
        )

        # Record in memory graph
        await self.ms.add_memory_graph_event(
            user_id=user_id,
            event_type="memory_promotion",
            content={
                "source_id": source_memory_id,
                "promoted_to": "soul_layer",
                "content_summary": str(compressed_content)[:200]
            },
            parent_id=source_memory_id
        )

        logger.info(f"Promoted memory {source_memory_id} to soul layer for user {user_id}")

        return promoted

    async def check_and_promote(
        self,
        user_id: str,
        memory_id: str,
        access_count: int,
        current_importance: float
    ):
        """
        Check if a memory should be promoted to soul layer.

        Called after each memory access.
        """
        if await self.soul_service.should_promote_to_soul(
            recent_memory_content={},
            access_count=access_count,
            importance_score=current_importance
        ):
            # Get full memory details and promote
            memories = await self.ms.retrieve_recent_memories(user_id, days=30)
            for mem in memories:
                if mem.id == memory_id:
                    await self.promote_to_soul_layer(
                        user_id,
                        memory_id,
                        {"summary": mem.summary, "topics": mem.key_topics}
                    )
                    break

    async def decay_importance(
        self,
        user_id: str,
        days_since_access: int
    ):
        """
        Apply importance decay to memories that haven't been accessed.

        Based on Ebbinghaus curve: most forgetting happens soon after learning,
        then levels off.
        """
        decay_rate = 0.95  # 5% decay per period

        # In production, this would:
        # - Get soul memories
        # - Apply decay to those not accessed in N days
        # - Mark as dormant if below threshold

        logger.debug(f"Applying importance decay for user {user_id}")

    async def record_interaction(
        self,
        user_id: str,
        memory_id: str,
        interaction_type: str = "access"
    ):
        """
        Record an interaction with a memory for reinforcement.

        Each interaction makes the memory slightly stronger.
        """
        await self.ms.add_memory_graph_event(
            user_id=user_id,
            event_type="memory_interaction",
            content={
                "memory_id": memory_id,
                "interaction_type": interaction_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Increase importance
        await self.ms.mark_memory_accessed(memory_id)
