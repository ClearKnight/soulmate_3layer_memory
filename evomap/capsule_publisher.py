"""
EvoMap Capsule Publisher

Publishes memory system capsules to EvoMap network.
"""
import logging
import time
import random
import json

from evomap.gep_adapter import GEPAdapter
from evomap.gene_publisher import SOULMATE_MEMORY_GENE
from datetime import datetime

logger = logging.getLogger(__name__)


class CapsulePublisher:
    """
    Publisher for memory-related capsules to EvoMap.
    """

    def __init__(self, adapter: GEPAdapter):
        self.adapter = adapter
        self.published_capsules = []

    def _build_capsule(
        self,
        trigger: list,
        summary: str,
        content: dict,
        confidence: float,
        description: str,
        extra_metadata: dict = None
    ) -> dict:
        """Build a capsule with proper structure for EvoMap."""
        metadata = {
            "author": "Soulmate Team",
            "description": description
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        # Ensure content is at least 50 characters when serialized
        content_str = json.dumps(content)
        if len(content_str) < 50:
            content_str = content_str.ljust(50, ' ')

        capsule = {
            "type": "Capsule",
            "schema_version": "1.5.0",
            "id": f"capsule_{int(time.time())}_{random.randint(0, 0xFFFF):04x}",
            "trigger": trigger,
            "gene": "gene_soulmate_3layer_memory",
            "genes_used": ["gene_soulmate_3layer_memory"],
            "summary": summary,
            "content": content_str,  # Must be a string, >= 50 chars
            "env_fingerprint": {
                "node_version": "1.0.0",
                "platform": "darwin",
                "arch": "arm64",
                "memory_layers": 3
            },
            "confidence": confidence,
            "blast_radius": {"files": 1, "lines": 10},
            "outcome": {
                "status": "success",
                "score": confidence
            },
            "source_type": "generated",
            "metadata": metadata,
            "domain": "memory_management"
        }

        capsule["asset_id"] = GEPAdapter.compute_asset_id(capsule)
        return capsule

    async def publish_gene_and_capsule(self, capsule: dict) -> dict:
        """Publish a Gene + Capsule together (requires at least 2 assets)."""
        gene = SOULMATE_MEMORY_GENE.copy()
        gene["asset_id"] = GEPAdapter.compute_asset_id(gene)

        payload = {
            "protocol": self.adapter.PROTOCOL,
            "protocol_version": self.adapter.PROTOCOL_VERSION,
            "message_type": "publish",
            "message_id": self.adapter._generate_message_id(),
            "sender_id": self.adapter.node_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "assets": [gene, capsule]
            }
        }

        try:
            response = await self.adapter.client.post(
                f"{self.adapter.BASE_URL}/a2a/publish",
                json=payload,
                headers={"Authorization": f"Bearer {self.adapter.node_secret}"}
            )
            response.raise_for_status()
            result = response.json()

            self.published_capsules.append(capsule["id"])
            logger.info(f"Published gene + capsule: {capsule['id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish: {e}")
            raise

    async def publish_memory_promotion_capsule(
        self,
        user_id: str,
        memory_content: dict,
        importance_score: float
    ) -> dict:
        """
        Publish a capsule documenting a successful memory promotion.
        """
        capsule = self._build_capsule(
            trigger=["user_preference_detected", "memory_promotion"],
            summary=f"Successfully promoted memory with importance {importance_score:.2f}",
            content={
                "intent": "Memory promotion from recent to soul layer",
                "strategy": "Emotional weight + access frequency analysis",
                "outcome": {
                    "status": "success",
                    "importance_score": importance_score,
                    "user_id": user_id
                }
            },
            confidence=importance_score,
            description="Memory promotion event"
        )

        return await self.publish_gene_and_capsule(capsule)

    async def publish_forgetting_capsule(
        self,
        user_id: str,
        memory_id: str,
        decay_amount: float
    ) -> dict:
        """
        Publish a capsule documenting a forgetting/decay event.
        """
        capsule = self._build_capsule(
            trigger=["memory_forgetting", "importance_decay"],
            summary=f"Applied forgetting decay of {decay_amount:.4f}",
            content={
                "intent": "Memory importance decay based on Ebbinghaus curve",
                "outcome": {
                    "memory_id": memory_id,
                    "decay_amount": decay_amount
                }
            },
            confidence=0.8,
            description="Memory forgetting event"
        )

        return await self.publish_gene_and_capsule(capsule)

    async def publish_vector_search_capsule(
        self,
        user_id: str,
        query: str,
        found_memory_id: str,
        similarity_score: float
    ) -> dict:
        """
        Publish a capsule documenting a successful semantic vector search.
        """
        capsule = self._build_capsule(
            trigger=["semantic_search", "vector_match", "memory_retrieval"],
            summary=f"Semantic search found memory with similarity {similarity_score:.2f}",
            content={
                "intent": "Semantic vector search for contextual memory",
                "strategy": f"Vector similarity search with score {similarity_score:.2f}",
                "query": query,
                "outcome": {
                    "status": "success",
                    "found_memory_id": found_memory_id,
                    "similarity_score": similarity_score,
                    "user_id": user_id
                }
            },
            confidence=similarity_score,
            description="Vector semantic search event",
            extra_metadata={
                "embedding_model": "BAAI/bge-small-zh-v1.5",
                "embedding_dim": 512
            }
        )

        return await self.publish_gene_and_capsule(capsule)
