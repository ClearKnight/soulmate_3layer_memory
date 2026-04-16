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
    "summary": "3-layer memory system with vector semantic search - v0.3",
    "version": "v0.3",
    "category": "innovate",
    "strategy": [
        "1. SHORT: Store current session (100 messages, in-memory + file persistence)",
        "2. RECENT: Store 3-day summaries (SQLite)",
        "3. SOUL: Store permanent core memories (SQLite)",
        "4. EMBEDDING: BAAI/bge-small-zh-v1.5 for semantic vector search (512 dim)",
        "5. PROCESS: Ebbinghaus decay, compression, promotion",
        "6. RETRIEVE: Parallel vector search, weighted fusion"
    ],
    "validation": [
        "node tests/validate_memory.js"
    ],
    "signals_match": [
        "memory",
        "remember",
        "forget",
        "soulmate",
        "personal",
        "context",
        "agent",
        "vector",
        "embedding",
        "semantic",
        "search"
    ]
}

# Asset ID is computed dynamically by GEPAdapter.compute_asset_id()


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
        gene["asset_id"] = GEPAdapter.compute_asset_id(gene)

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

            logger.info(f"Published gene: {gene['asset_id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish gene: {e}")
            raise


# Import datetime for the payload
from datetime import datetime
