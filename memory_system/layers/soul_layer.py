"""
Soul Layer (语义记忆/灵魂) - SQLite Version

- Permanent core memories
- Storage: SQLite
- Lifecycle: Permanent (may be demoted)
"""
import json
import math
import sqlite3
from typing import Optional
from datetime import datetime
from pathlib import Path

from memory_system.models import SoulMemory, MemoryType
import config


class SoulLayer:
    """
    Soul memory layer using SQLite.

    Features:
    - Permanent storage of core memories
    - Importance and emotional weight tracking
    - Vector search with cosine similarity
    """

    def __init__(self, db_path: str = "./soulmate.db"):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def save(self, memory: SoulMemory) -> SoulMemory:
        """Save a soul memory (without embedding)"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO soul_memory
                (id, user_id, memory_type, content, embedding,
                 importance_score, emotional_weight, access_count, gene_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.user_id,
                memory.memory_type.value if isinstance(memory.memory_type, MemoryType) else memory.memory_type,
                json.dumps(memory.content),
                None,  # embedding - not used in SQLite
                memory.importance_score,
                memory.emotional_weight,
                memory.access_count,
                memory.gene_id,
                memory.created_at.isoformat() if memory.created_at else None,
                memory.updated_at.isoformat() if memory.updated_at else None
            ))
            conn.commit()
        return memory

    def save_with_embedding(self, memory: SoulMemory, embedding: list[float]) -> SoulMemory:
        """Save a soul memory with its embedding vector"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO soul_memory
                (id, user_id, memory_type, content, embedding,
                 importance_score, emotional_weight, access_count, gene_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.user_id,
                memory.memory_type.value if isinstance(memory.memory_type, MemoryType) else memory.memory_type,
                json.dumps(memory.content),
                json.dumps(embedding),
                memory.importance_score,
                memory.emotional_weight,
                memory.access_count,
                memory.gene_id,
                memory.created_at.isoformat() if memory.created_at else None,
                memory.updated_at.isoformat() if memory.updated_at else None
            ))
            conn.commit()
        return memory

    def get(self, memory_id: str) -> Optional[SoulMemory]:
        """Get a specific soul memory by ID"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM soul_memory WHERE id = ?",
                (memory_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_memory(row)
        return None

    def get_by_type(
        self,
        user_id: str,
        memory_type: MemoryType,
        top_k: int = 10
    ) -> list[SoulMemory]:
        """Get soul memories by type"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM soul_memory
                WHERE user_id = ? AND memory_type = ?
                ORDER BY importance_score DESC
                LIMIT ?
            """, (user_id, memory_type.value, top_k))
            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    def get_all(self, user_id: str) -> list[SoulMemory]:
        """Get all soul memories for a user"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM soul_memory
                WHERE user_id = ?
                ORDER BY importance_score DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 10
    ) -> list[SoulMemory]:
        """
        Search soul memories by text match (fallback when vector search unavailable).
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM soul_memory
                WHERE user_id = ?
                AND content LIKE ?
                ORDER BY importance_score DESC
                LIMIT ?
            """, (user_id, f"%{query}%", top_k))
            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    def search_with_vector(
        self,
        user_id: str,
        query_embedding: list[float],
        top_k: int = 10,
        min_similarity: float = 0.05
    ) -> list[tuple[SoulMemory, float]]:
        """
        Search soul memories by vector similarity.

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
                SELECT * FROM soul_memory
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
                UPDATE soul_memory
                SET access_count = access_count + 1,
                    last_accessed = ?,
                    importance_score = MIN(1.0, importance_score * 1.02)
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
                UPDATE soul_memory
                SET importance_score = ?, updated_at = ?
                WHERE id = ?
            """, (importance_score, datetime.utcnow().isoformat(), memory_id))
            conn.commit()

    def demote(self, memory_id: str) -> None:
        """Demote a soul memory (mark as dormant)"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE soul_memory
                SET importance_score = importance_score * 0.5,
                    updated_at = ?
                WHERE id = ?
                AND importance_score > 0.2
            """, (datetime.utcnow().isoformat(), memory_id))
            conn.commit()

    def delete(self, memory_id: str) -> bool:
        """Delete a soul memory"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM soul_memory WHERE id = ?",
                (memory_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def count(self, user_id: str) -> int:
        """Count soul memories for a user"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM soul_memory WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def _row_to_memory(self, row) -> SoulMemory:
        """Convert database row to SoulMemory model"""
        memory_type = row["memory_type"]
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)

        content = row["content"]
        if isinstance(content, str):
            content = json.loads(content)

        embedding = row["embedding"]
        if embedding:
            if isinstance(embedding, str):
                embedding = json.loads(embedding)
        else:
            embedding = None

        return SoulMemory(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            importance_score=row["importance_score"],
            emotional_weight=row["emotional_weight"],
            access_count=row["access_count"],
            last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
            gene_id=row["gene_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )