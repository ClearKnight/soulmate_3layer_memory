"""
EvoMap Integration Module

Provides EvoMap A2A protocol integration for the Soulmate Memory System.
"""
from evomap.gep_adapter import GEPAdapter
from evomap.gene_publisher import GenePublisher, SOULMATE_MEMORY_GENE
from evomap.capsule_publisher import CapsulePublisher

__all__ = [
    "GEPAdapter",
    "GenePublisher",
    "CapsulePublisher",
    "SOULMATE_MEMORY_GENE"
]
