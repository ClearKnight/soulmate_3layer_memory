"""
EvoMap Capsule Publisher

Publishes memory system capsules to EvoMap network.
"""
import logging
import time
import random

from evomap.gep_adapter import GEPAdapter
from datetime import datetime

logger = logging.getLogger(__name__)


class CapsulePublisher:
    """
    Publisher for memory-related capsules to EvoMap.
    """

    def __init__(self, adapter: GEPAdapter):
        self.adapter = adapter
        self.published_capsules = []

    async def publish_memory_promotion_capsule(
        self,
        user_id: str,
        memory_content: dict,
        importance_score: float
    ) -> dict:
        """
        Publish a capsule documenting a successful memory promotion.
        """
        capsule = {
            "type": "Capsule",
            "schema_version": "1.5.0",
            "id": f"capsule_{int(time.time())}_{random.hex(4)}",
            "trigger": ["user_preference_detected", "memory_promotion"],
            "gene": "gene_soulmate_3layer_memory",
            "genes_used": ["gene_soulmate_3layer_memory"],
            "summary": f"Successfully promoted memory with importance {importance_score:.2f}",
            "content": {
                "intent": "Memory promotion from recent to soul layer",
                "strategy": "Emotional weight + access frequency analysis",
                "outcome": {
                    "status": "success",
                    "importance_score": importance_score,
                    "user_id": user_id
                }
            },
            "confidence": importance_score,
            "blast_radius": {"files": 1, "lines": 10},
            "outcome": {
                "status": "success",
                "score": importance_score
            },
            "source_type": "generated",
            "metadata": {
                "author": "Soulmate Team",
                "description": "Memory promotion event"
            },
            "domain": "memory_management"
        }

        capsule["asset_id"] = GEPAdapter.compute_asset_id(capsule)

        payload = {
            "protocol": self.adapter.PROTOCOL,
            "protocol_version": self.adapter.PROTOCOL_VERSION,
            "message_type": "publish",
            "message_id": self.adapter._generate_message_id(),
            "sender_id": self.adapter.node_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "assets": [capsule]
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
            logger.info(f"Published capsule: {capsule['id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish capsule: {e}")
            raise

    async def publish_forgetting_capsule(
        self,
        user_id: str,
        memory_id: str,
        decay_amount: float
    ) -> dict:
        """
        Publish a capsule documenting a forgetting/decay event.
        """
        capsule = {
            "type": "Capsule",
            "schema_version": "1.5.0",
            "id": f"capsule_{int(time.time())}_{random.hex(4)}",
            "trigger": ["memory_forgetting", "importance_decay"],
            "gene": "gene_soulmate_3layer_memory",
            "summary": f"Applied forgetting decay of {decay_amount:.4f}",
            "content": {
                "intent": "Memory importance decay based on Ebbinghaus curve",
                "outcome": {
                    "memory_id": memory_id,
                    "decay_amount": decay_amount
                }
            },
            "confidence": 0.8,
            "blast_radius": {"files": 1, "lines": 5},
            "outcome": {
                "status": "success",
                "score": 0.8
            },
            "source_type": "generated",
            "metadata": {
                "author": "Soulmate Team",
                "description": "Memory forgetting event"
            },
            "domain": "memory_management"
        }

        capsule["asset_id"] = GEPAdapter.compute_asset_id(capsule)

        payload = {
            "protocol": self.adapter.PROTOCOL,
            "protocol_version": self.adapter.PROTOCOL_VERSION,
            "message_type": "publish",
            "message_id": self.adapter._generate_message_id(),
            "sender_id": self.adapter.node_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "assets": [capsule]
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
            logger.info(f"Published forgetting capsule: {capsule['id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish forgetting capsule: {e}")
            raise

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
        capsule = {
            "type": "Capsule",
            "schema_version": "1.5.0",
            "id": f"capsule_{int(time.time())}_{random.hex(4)}",
            "trigger": ["semantic_search", "vector_match", "memory_retrieval"],
            "gene": "gene_soulmate_3layer_memory",
            "genes_used": ["gene_soulmate_3layer_memory"],
            "summary": f"Semantic search found memory with similarity {similarity_score:.2f}",
            "content": {
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
            "confidence": similarity_score,
            "blast_radius": {"files": 1, "lines": 5},
            "outcome": {
                "status": "success",
                "score": similarity_score
            },
            "source_type": "generated",
            "metadata": {
                "author": "Soulmate Team",
                "description": "Vector semantic search event",
                "embedding_model": "BAAI/bge-small-zh-v1.5",
                "embedding_dim": 512
            },
            "domain": "memory_management"
        }

        capsule["asset_id"] = GEPAdapter.compute_asset_id(capsule)

        payload = {
            "protocol": self.adapter.PROTOCOL,
            "protocol_version": self.adapter.PROTOCOL_VERSION,
            "message_type": "publish",
            "message_id": self.adapter._generate_message_id(),
            "sender_id": self.adapter.node_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "assets": [capsule]
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
            logger.info(f"Published vector search capsule: {capsule['id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish vector search capsule: {e}")
            raise
