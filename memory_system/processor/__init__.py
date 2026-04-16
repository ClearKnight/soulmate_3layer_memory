"""
Memory System - Processors

Four processors for memory management:
- Collector: Collects and classifies memories
- ForgettingScheduler: Manages memory decay
- Compressor: Compresses conversations to summaries
- Promoter: Decides memory promotion to soul layer
"""
from memory_system.processor.collector import Collector
from memory_system.processor.forgetting import ForgettingScheduler
from memory_system.processor.compressor import Compressor
from memory_system.processor.promoter import Promoter

__all__ = ["Collector", "ForgettingScheduler", "Compressor", "Promoter"]
