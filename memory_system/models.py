"""
Memory System - Data Models

Defines the core data structures for the 3-layer memory system.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid


class MemoryType(str, Enum):
    """Memory type classification"""
    PREFERENCE = "preference"
    VALUE = "value"
    HABIT = "habit"
    IMPORTANT_EVENT = "important_event"
    EMOTIONAL_STATE = "emotional_state"
    RELATIONSHIP = "relationship"


class EventType(str, Enum):
    """Event types for memory collection"""
    USER_SAID = "user_said"
    AGENT_RESPONSE = "agent_response"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_EVENT = "system_event"


class EmotionalState(str, Enum):
    """Emotional state classification"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


# ─────────────────────────────────────────────────────────────────
# Layer Data Models
# ─────────────────────────────────────────────────────────────────

class ShortTermContext(BaseModel):
    """Short-term layer - current session context (Redis)"""
    session_id: str
    user_id: str
    messages: list[dict[str, Any]] = []  # [{role, content, timestamp}]
    current_emotion: Optional[str] = None
    current_topic: Optional[str] = None
    pending_matters: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecentMemory(BaseModel):
    """Recent layer - 3-day summaries (PostgreSQL)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str  # YYYY-MM-DD
    summary: str
    emotion: Optional[str] = None
    topics: list[str] = []
    importance_score: float = 0.5
    emotional_weight: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    embedding: Optional[list[float]] = None  # Vector for semantic search


class SoulMemory(BaseModel):
    """Soul layer - permanent core memories (PostgreSQL + Vector)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    memory_type: MemoryType
    content: dict[str, Any]
    embedding: Optional[list[float]] = None
    importance_score: float = 0.5
    emotional_weight: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    gene_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# ─────────────────────────────────────────────────────────────────
# Processor Data Models
# ─────────────────────────────────────────────────────────────────

class MemoryInput(BaseModel):
    """Input for collecting a memory"""
    user_id: str
    event_type: EventType = EventType.USER_SAID
    content: str
    emotion: Optional[str] = None
    topics: list[str] = []
    metadata: dict[str, Any] = {}


class MemoryStrength(BaseModel):
    """Memory strength tracking for forgetting curve"""
    memory_id: str
    initial_strength: float = 1.0
    current_strength: float = 1.0
    stability: float  # Based on importance
    last_decay_check: datetime = Field(default_factory=datetime.utcnow)


class PromotionDecision(BaseModel):
    """Decision on whether to promote a memory to soul layer"""
    memory_id: str
    should_promote: bool
    reason: str
    confidence: float


class CompressionResult(BaseModel):
    """Result of compressing multiple messages into a summary"""
    summary: str
    emotion: str
    topics: list[str]
    key_entities: list[str] = []
    importance_score: float
    emotional_weight: float


# ─────────────────────────────────────────────────────────────────
# Retrieval Data Models
# ─────────────────────────────────────────────────────────────────

class RetrievedMemory(BaseModel):
    """A retrieved memory with relevance score"""
    memory_id: str
    memory_type: str  # "soul", "recent", "short"
    content: dict[str, Any]
    relevance_score: float
    importance_score: float
    last_accessed: Optional[datetime] = None


class RetrievedContext(BaseModel):
    """Combined context from all layers for response generation"""
    user_id: str
    query: str
    soul_memories: list[RetrievedMemory] = []
    recent_memories: list[RetrievedMemory] = []
    short_context: Optional[ShortTermContext] = None
    total_context_window: int = 4000  # Token limit


# ─────────────────────────────────────────────────────────────────
# API Data Models
# ─────────────────────────────────────────────────────────────────

class CollectRequest(BaseModel):
    """Request to collect a memory"""
    user_id: str
    content: str
    emotion: Optional[str] = None
    topics: list[str] = []
    metadata: dict[str, Any] = {}


class CollectResponse(BaseModel):
    """Response from collecting a memory"""
    success: bool
    memory_id: Optional[str] = None
    layer: str  # "short", "recent", "soul"
    message: str = ""


class RetrieveRequest(BaseModel):
    """Request to retrieve context"""
    user_id: str
    query: str
    session_id: Optional[str] = None


class RetrieveResponse(BaseModel):
    """Response with retrieved context"""
    user_id: str
    soul_memories: list[dict] = []
    recent_memories: list[dict] = []
    short_context: Optional[dict] = None
    context_text: str  # Formatted context for LLM
