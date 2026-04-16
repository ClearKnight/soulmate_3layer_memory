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
        "personal", "context", "agent"
    ],
    "summary": "3-layer memory system with human-like forgetting curve simulation",
    "preconditions": [
        "User has provided conversation history",
        "Memory system is initialized"
    ],
    "postconditions": [
        "Memory is stored in appropriate layer",
        "Context is updated for future retrieval"
    ],
    "strategy": [
        "1. SHORT: Store current session (100 messages, in-memory + file persistence)",
        "2. RECENT: Store 3-day summaries (SQLite)",
        "3. SOUL: Store permanent core memories (SQLite)",
        "4. PROCESS: Ebbinghaus decay, compression, promotion",
        "5. RETRIEVE: Parallel search, weighted fusion"
    ],
    "constraints": {
        "max_files": 10,
        "forbidden_paths": []
    },
    "validation": [
        "Test memory retrieval accuracy",
        "Verify emotional weight affects recall",
        "Verify forgetting curve simulation"
    ],
    "metadata": {
        "author": "Soulmate Team",
        "tags": ["memory", "personal", "agent", "forgetting", "evolution"],
        "description": "A 3-layer memory system that simulates human memory patterns",
        "version": "0.1.0",
        "license": "MIT"
    },
    "domain": "memory_management"
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

            self.published_genes.append(gene["id"])
            logger.info(f"Published gene: {gene['id']}")

            return result

        except Exception as e:
            logger.error(f"Failed to publish gene: {e}")
            raise


# Import datetime for the payload
from datetime import datetime
