"""
Memory System - Main Facade

Unified interface for the 3-layer memory system (SQLite version).
"""
import asyncio
from typing import Optional
from pathlib import Path

from memory_system.layers import ShortLayer, RecentLayer, SoulLayer
from memory_system.processor import Collector, ForgettingScheduler, Compressor, Promoter
from memory_system.retriever import Retriever
from memory_system.models import (
    ShortTermContext,
    RetrievedContext,
    CollectRequest,
    CollectResponse,
    RetrieveRequest,
    RetrieveResponse,
)
import config


class MemorySystem:
    """
    Unified facade for the 3-layer memory system.

    Provides:
    - collect(): Store a memory
    - retrieve(): Get context for response generation
    - Background processing (forgetting, compression, promotion)

    Usage:
        ms = MemorySystem()
        await ms.initialize()

        # Collect
        await ms.collect(user_id="u1", content="今天加班好累")

        # Retrieve
        context = await ms.retrieve(user_id="u1", query="工作")

        # Cleanup
        await ms.close()
    """

    def __init__(self, db_path: str = "./soulmate.db"):
        self.db_path = db_path

        # Layers
        self.short: Optional[ShortLayer] = None
        self.recent: Optional[RecentLayer] = None
        self.soul: Optional[SoulLayer] = None

        # Processors
        self.collector: Optional[Collector] = None
        self.forgetting: Optional[ForgettingScheduler] = None
        self.compressor: Optional[Compressor] = None
        self.promoter: Optional[Promoter] = None

        # Retriever
        self.retriever: Optional[Retriever] = None

        # Background tasks
        self._background_tasks: list = []

    async def initialize(self):
        """Initialize all connections and components"""
        # Initialize layers with SQLite paths
        db_path = config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else "./soulmate.db"

        self.short = ShortLayer(persistence_path="./short_term_data.json")
        self.recent = RecentLayer(db_path=db_path)
        self.soul = SoulLayer(db_path=db_path)

        # Initialize processors
        self.collector = Collector(self.short, self.recent, self.soul)
        self.forgetting = ForgettingScheduler(self.recent, self.soul)
        self.compressor = Compressor()
        self.promoter = Promoter(self.recent, self.soul)

        # Initialize retriever
        self.retriever = Retriever(self.short, self.recent, self.soul)

        # Create tables
        await self._create_tables()

        # Start background tasks
        await self.forgetting.start_background_tasks()

    async def close(self):
        """Close all connections and stop background tasks"""
        await self.forgetting.stop()

    async def _create_tables(self):
        """Create database tables if not exist"""
        import aiosqlite

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                -- Recent memory table
                CREATE TABLE IF NOT EXISTS recent_memory (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    summary TEXT,
                    emotion TEXT,
                    topics TEXT DEFAULT '[]',
                    importance_score REAL DEFAULT 0.5,
                    emotional_weight REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    created_at TEXT
                )
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recent_user_date
                    ON recent_memory(user_id, date)
            """)

            await conn.execute("""
                -- Soul memory table
                CREATE TABLE IF NOT EXISTS soul_memory (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    importance_score REAL DEFAULT 0.5,
                    emotional_weight REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    gene_id TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_soul_user
                    ON soul_memory(user_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_soul_type
                    ON soul_memory(memory_type)
            """)

            await conn.commit()

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────

    async def collect(
        self,
        user_id: str,
        content: str,
        session_id: Optional[str] = None,
        event_type: str = "user_said",
        emotion: Optional[str] = None,
        topics: list[str] = [],
        metadata: dict = {}
    ) -> CollectResponse:
        """
        Collect a memory.

        Args:
            user_id: User identifier
            content: Memory content
            session_id: Optional session ID for short-term storage
            event_type: Type of event
            emotion: Optional emotion label
            topics: Topic tags
            metadata: Additional metadata

        Returns:
            CollectResponse with storage info
        """
        # Use session_id or user_id as default
        if not session_id:
            session_id = f"default_{user_id}"

        result = await self.collector.collect(
            user_id=user_id,
            session_id=session_id,
            content=content,
            event_type=event_type,
            emotion=emotion,
            topics=topics,
            metadata=metadata
        )

        return CollectResponse(
            success=result.get("stored", True),
            memory_id=result.get("memory_id"),
            layer=result.get("layer", "unknown"),
            message="Memory collected"
        )

    async def retrieve(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None
    ) -> RetrieveResponse:
        """
        Retrieve context for response generation.

        Args:
            user_id: User identifier
            query: Current query/context request
            session_id: Optional session ID

        Returns:
            RetrieveResponse with formatted context
        """
        context = await self.retriever.retrieve(
            user_id=user_id,
            query=query,
            session_id=session_id
        )

        context_text = self.retriever.format_context_text(context)

        return RetrieveResponse(
            user_id=user_id,
            soul_memories=[m.model_dump() for m in context.soul_memories],
            recent_memories=[m.model_dump() for m in context.recent_memories],
            short_context=context.short_context.model_dump() if context.short_context else None,
            context_text=context_text
        )

    async def process_user_memories(self, user_id: str) -> dict:
        """
        Run promotion/demotion processing for a user.

        Returns:
            dict with processing stats
        """
        # Check for promotions
        promotion_stats = self.promoter.process_user_memories(user_id)

        # Demote low importance
        demoted = self.promoter.demote_low_importance(user_id)

        return {
            **promotion_stats,
            "demoted": demoted
        }

    # ─────────────────────────────────────────────────────────────────
    # Layer Access (for advanced usage)
    # ─────────────────────────────────────────────────────────────────

    def get_short_layer(self) -> ShortLayer:
        """Get short-term layer instance"""
        return self.short

    def get_recent_layer(self) -> RecentLayer:
        """Get recent layer instance"""
        return self.recent

    def get_soul_layer(self) -> SoulLayer:
        """Get soul layer instance"""
        return self.soul

    def get_retriever(self) -> Retriever:
        """Get retriever instance"""
        return self.retriever
