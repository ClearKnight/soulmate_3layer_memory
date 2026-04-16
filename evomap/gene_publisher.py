"""
EvoMap Gene Publisher

Publishes memory system genes to EvoMap network.
"""
import logging

from evomap.gep_adapter import GEPAdapter

logger = logging.getLogger(__name__)


# The Soulmate Memory Gene
SOULMATE_MEMORY_GENE = {
    "type": "Gene",
    "schema_version": "1.5.0",
    "id": "gene_soulmate_3layer_memory",
    "category": "innovate",
    "signals_match": [
        "memory", "remember", "forget", "soulmate",
        "personal", "context", "agent", "vector", "embedding",
        "semantic", "search", "recall"
    ],
    "summary": "3-layer memory system with vector semantic search and human-like forgetting curve",
    "preconditions": [
        "User has provided conversation history",
        "Memory system is initialized"
    ],
    "postconditions": [
        "Memory is stored in appropriate layer with vector embedding",
        "Context is retrieved via semantic similarity search"
    ],
    "strategy": [
        "1. SHORT: Store current session (100 messages, in-memory + file persistence)",
        "2. RECENT: Store 3-day summaries with embeddings (SQLite)",
        "3. SOUL: Store permanent core memories with embeddings (SQLite)",
        "4. EMBEDDING: BAAI/bge-small-zh-v1.5 for semantic vectorization",
        "5. PROCESS: Ebbinghaus decay, compression, promotion",
        "6. RETRIEVE: Vector similarity search + text fallback"
    ],
    "constraints": {
        "max_files": 10,
        "forbidden_paths": []
    },
    "validation": [
        "Test semantic retrieval (e.g., query 'food' finds 'hot pot')",
        "Verify emotional weight affects recall",
        "Verify forgetting curve simulation",
        "Test vector similarity scoring"
    ],
    "metadata": {
        "author": "Soulmate Team",
        "tags": ["memory", "personal", "agent", "forgetting", "evolution", "vector", "embedding", "semantic-search"],
        "description": "A 3-layer memory system with vector semantic search that simulates human memory patterns",
        "version": "0.2.0",
        "license": "MIT",
        "embedding_model": "BAAI/bge-small-zh-v1.5",
        "embedding_dim": 512
    },
    "domain": "memory_management",
    "asset_id": "sha256:a55e032e299d9248c331dddaf1e21a258c19c13514b4c0591157235aa0f2e041"
}


class GenePublisher:
    """
    Publisher for memory-related genes to EvoMap.
    """

    def __init__(self, adapter: GEPAdapter):
        self.adapter = adapter
        self.published_genes = []

    async def publish_memory_gene(self) -> dict:
        """Publish the Soulmate 3-layer memory gene."""
        gene = SOULMATE_MEMORY_GENE.copy()
        # Use predefined asset_id for content-addressable iteration
        gene["asset_id"] = gene.get("asset_id") or GEPAdapter.compute_asset_id(gene)

        payload = {
            "protocol": self.adapter.PROTOCOL,
            "protocol_version": self.adapter.PROTOCOL_VERSION,
            "message_type": "publish",
            "message_id": self.adapter._generate_message_id(),
            "sender_id": self.adapter.node_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "assets": [gene]
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

            self.published_genes.append(gene["id"])
            logger.info(f"Published gene: {gene['id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish gene: {e}")
            raise


# Import datetime for the payload
from datetime import datetime
