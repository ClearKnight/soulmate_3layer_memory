"""
Soulmate Memory System

A 3-layer human-like memory system for AI agents.
"""
from memory_system.models import (
    MemoryType,
    EventType,
    EmotionalState,
    ShortTermContext,
    RecentMemory,
    SoulMemory,
    MemoryInput,
    MemoryStrength,
    PromotionDecision,
    CompressionResult,
    RetrievedMemory,
    RetrievedContext,
    CollectRequest,
    CollectResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from memory_system.layers import ShortLayer, RecentLayer, SoulLayer
from memory_system.memory_system import MemorySystem
from memory_system.retriever import Retriever
from memory_system.processor import Collector, ForgettingScheduler, Compressor, Promoter

__all__ = [
    # Models
    "MemoryType",
    "EventType",
    "EmotionalState",
    "ShortTermContext",
    "RecentMemory",
    "SoulMemory",
    "MemoryInput",
    "MemoryStrength",
    "PromotionDecision",
    "CompressionResult",
    "RetrievedMemory",
    "RetrievedContext",
    "CollectRequest",
    "CollectResponse",
    "RetrieveRequest",
    "RetrieveResponse",
    # Layers
    "ShortLayer",
    "RecentLayer",
    "SoulLayer",
    # Core
    "MemorySystem",
    "Retriever",
    # Processors
    "Collector",
    "ForgettingScheduler",
    "Compressor",
    "Promoter",
]
