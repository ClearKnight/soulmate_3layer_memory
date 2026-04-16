"""
Recent Layer (情景记忆) - SQLite Version

- Stores 3-day conversation summaries
- Storage: SQLite
- Lifecycle: 3 days → compress/promote/forget
"""
import json
import math
import sqlite3
from typing import Optional
from datetime import datetime, date
from pathlib import Path

from memory_system.models import RecentMemory
import config


class RecentLayer:
    """
    Recent memory layer using SQLite.

    Features:
    - 3-day conversation summaries
    - Emotional state tracking
    - Importance scoring
    """

    def __init__(self, db_path: str = "./soulmate.db"):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def save(self, memory: RecentMemory) -> RecentMemory:
        """Save a recent memory (without embedding)"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO recent_memory
                (id, user_id, date, summary, emotion, topics, importance_score, emotional_weight, access_count, last_accessed, created_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.user_id,
                memory.date,
                memory.summary,
                memory.emotion,
                json.dumps(memory.topics),
                memory.importance_score,
                memory.emotional_weight,
                memory.access_count,
                memory.last_accessed.isoformat() if memory.last_accessed else None,
                memory.created_at.isoformat(),
                None  # embedding
            ))
            conn.commit()
        return memory

    def save_with_embedding(self, memory: RecentMemory, embedding: list[float]) -> RecentMemory:
        """Save a recent memory with its embedding vector"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO recent_memory
                (id, user_id, date, summary, emotion, topics, importance_score, emotional_weight, access_count, last_accessed, created_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.user_id,
                memory.date,
                memory.summary,
                memory.emotion,
                json.dumps(memory.topics),
                memory.importance_score,
                memory.emotional_weight,
                memory.access_count,
                memory.last_accessed.isoformat() if memory.last_accessed else None,
                memory.created_at.isoformat(),
                json.dumps(embedding)
            ))
            conn.commit()
        return memory

    def get(self, memory_id: str) -> Optional[RecentMemory]:
        """Get a specific recent memory by ID"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM recent_memory WHERE id = ?",
                (memory_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_memory(row)
        return None

    def get_by_user(
        self,
        user_id: str,
        days: int = 3
    ) -> list[RecentMemory]:
        """Get recent memories for a user within N days"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM recent_memory
                WHERE user_id = ?
                AND date >= date('now', ?)
                ORDER BY date DESC
            """, (user_id, f"-{days} days"))
            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    def get_today(self, user_id: str) -> Optional[RecentMemory]:
        """Get today's summary if exists"""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM recent_memory
                WHERE user_id = ? AND date = ?
            """, (user_id, today))
            row = cursor.fetchone()
            if row:
                return self._row_to_memory(row)
        return None

    def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> list[RecentMemory]:
        """Search recent memories by text match"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM recent_memory
                WHERE user_id = ?
                AND summary LIKE ?
                ORDER BY importance_score DESC
                LIMIT ?
            """, (user_id, f"%{query}%", top_k))
            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    def search_with_vector(
        self,
        user_id: str,
        query_embedding: list[float],
        top_k: int = 5,
        min_similarity: float = 0.05
    ) -> list[tuple[RecentMemory, float]]:
        """
        Search recent memories by vector similarity.

        Args:
            user_id: User ID
            query_embedding: Query vector
            top_k: Maximum results to return
            min_similarity: Minimum cosine similarity threshold

        Returns:
            List of (memory, similarity_score) tuples
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM recent_memory
                WHERE user_id = ? AND embedding IS NOT NULL
            """, (user_id,))
            rows = cursor.fetchall()

        results = []
        for row in rows:
            memory = self._row_to_memory(row)
            if memory.embedding:
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                if similarity >= min_similarity:
                    results.append((memory, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0

        dot_prod = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_prod / (norm_a * norm_b)

    def increment_access(self, memory_id: str) -> None:
        """Increment access count and update last_accessed"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE recent_memory
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), memory_id))
            conn.commit()

    def update_importance(
        self,
        memory_id: str,
        importance_score: float
    ) -> None:
        """Update importance score"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE recent_memory
                SET importance_score = ?
                WHERE id = ?
            """, (importance_score, memory_id))
            conn.commit()

    def delete_old(self, days: int = 90) -> int:
        """Delete memories older than N days"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM recent_memory
                WHERE date < date('now', ?)
            """, (f"-{days} days",))
            conn.commit()
            return cursor.rowcount

    def count(self, user_id: str) -> int:
        """Count recent memories for a user"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM recent_memory WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def _row_to_memory(self, row) -> RecentMemory:
        """Convert database row to RecentMemory model"""
        topics = row["topics"]
        if isinstance(topics, str):
            topics = json.loads(topics)

        embedding = row["embedding"]
        if embedding:
            if isinstance(embedding, str):
                embedding = json.loads(embedding)
        else:
            embedding = None

        # Get memory with all fields including embedding if present
        memory = RecentMemory(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            date=str(row["date"]),
            summary=row["summary"],
            emotion=row["emotion"],
            topics=topics or [],
            importance_score=row["importance_score"],
            emotional_weight=row["emotional_weight"],
            access_count=row["access_count"],
            last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )
        # Manually set embedding since RecentMemory doesn't have it by default
        memory.embedding = embedding
        return memory