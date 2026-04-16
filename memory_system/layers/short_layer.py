"""
Short-Term Layer (工作记忆) - In-Memory Version

- Capacity: 100 messages per session
- Storage: In-memory dict (with file persistence)
- Lifecycle: Session duration (24h TTL)
"""
import json
import os
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

from memory_system.models import ShortTermContext
import config


class ShortLayer:
    """
    Short-term memory layer using in-memory storage.

    For production with Redis, replace this with Redis-based implementation.
    For now, we use a simple in-memory dict with optional file persistence.

    Features:
    - Session-based storage
    - Auto-expiring (24h TTL)
    - Message history with max 100 items
    """

    def __init__(self, persistence_path: str = "./short_term_data.json"):
        self.persistence_path = persistence_path
        self._storage: dict[str, ShortTermContext] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load data from disk if exists"""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self._storage[key] = ShortTermContext.model_validate(value)
            except Exception:
                pass

    def _save_to_disk(self):
        """Save data to disk"""
        try:
            data = {k: v.model_dump() for k, v in self._storage.items()}
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _make_key(self, user_id: str, session_id: str) -> str:
        return f"short:{user_id}:{session_id}"

    async def save_context(self, context: ShortTermContext) -> None:
        """Save short-term context"""
        # Enforce max messages limit
        if len(context.messages) > config.SHORT_TERM_MAX_MESSAGES:
            context.messages = context.messages[-config.SHORT_TERM_MAX_MESSAGES:]

        key = self._make_key(context.user_id, context.session_id)
        self._storage[key] = context
        self._save_to_disk()

    async def get_context(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[ShortTermContext]:
        """Get short-term context"""
        key = self._make_key(user_id, session_id)
        context = self._storage.get(key)

        if context:
            # Check TTL
            if context.created_at:
                age = datetime.utcnow() - context.created_at
                if age.total_seconds() > config.SHORT_TERM_TTL_SECONDS:
                    # Expired
                    del self._storage[key]
                    self._save_to_disk()
                    return None
        return context

    async def get_or_create_context(
        self,
        user_id: str,
        session_id: str
    ) -> ShortTermContext:
        """Get existing context or create new one"""
        context = await self.get_context(user_id, session_id)
        if context is None:
            context = ShortTermContext(
                session_id=session_id,
                user_id=user_id
            )
            await self.save_context(context)
        return context

    async def append_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        emotion: Optional[str] = None,
        topic: Optional[str] = None
    ) -> ShortTermContext:
        """Append a message to the session"""
        context = await self.get_or_create_context(user_id, session_id)

        context.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update emotion if provided
        if emotion:
            context.current_emotion = emotion

        # Update topic if provided
        if topic and topic not in (context.current_topic or ""):
            context.current_topic = topic
            if topic not in context.pending_matters:
                context.pending_matters.append(topic)

        await self.save_context(context)
        return context

    async def set_emotion(
        self,
        user_id: str,
        session_id: str,
        emotion: str
    ) -> ShortTermContext:
        """Set current emotional state"""
        context = await self.get_or_create_context(user_id, session_id)
        context.current_emotion = emotion
        await self.save_context(context)
        return context

    async def add_pending_matter(
        self,
        user_id: str,
        session_id: str,
        matter: str
    ) -> ShortTermContext:
        """Add a pending matter"""
        context = await self.get_or_create_context(user_id, session_id)
        if matter not in context.pending_matters:
            context.pending_matters.append(matter)
        await self.save_context(context)
        return context

    async def clear_pending_matter(
        self,
        user_id: str,
        session_id: str,
        matter: str
    ) -> ShortTermContext:
        """Remove a pending matter"""
        context = await self.get_context(user_id, session_id)
        if context and matter in context.pending_matters:
            context.pending_matters.remove(matter)
            await self.save_context(context)
        return context

    async def get_recent_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 10
    ) -> list[dict]:
        """Get the N most recent messages"""
        context = await self.get_context(user_id, session_id)
        if not context:
            return []
        return context.messages[-limit:] if limit > 0 else context.messages

    async def delete_context(self, user_id: str, session_id: str) -> None:
        """Delete a session context"""
        key = self._make_key(user_id, session_id)
        if key in self._storage:
            del self._storage[key]
            self._save_to_disk()
