"""
EvoMap GEP Adapter

Provides A2A protocol integration for the Soulmate Memory System.
"""
import os
import json
import asyncio
import hashlib
from datetime import datetime
from typing import Optional
import logging

import httpx

import config

logger = logging.getLogger(__name__)


class GEPAdapter:
    """
    Adapter for EvoMap GEP (Genome Evolution Protocol).

    Usage:
        adapter = GEPAdapter()
        await adapter.register_node()
        await adapter.publish_memory_gene()
    """

    BASE_URL = "https://evomap.ai"
    PROTOCOL = "gep-a2a"
    PROTOCOL_VERSION = "1.0.0"

    def __init__(self):
        self.node_id: Optional[str] = None
        self.node_secret: Optional[str] = None
        self.registered = False
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def register_node(
        self,
        capabilities: Optional[dict] = None,
        identity_doc: Optional[str] = None
    ) -> dict:
        """
        Register this agent as a node on EvoMap.
        """
        # Check for existing credentials
        if config.EVOMAP_NODE_ID and config.EVOMAP_NODE_SECRET:
            self.node_id = config.EVOMAP_NODE_ID
            self.node_secret = config.EVOMAP_NODE_SECRET
            self.registered = True
            logger.info(f"Using existing node credentials: {self.node_id}")
            return {"node_id": self.node_id, "status": "existing"}

        payload = {
            "protocol": self.PROTOCOL,
            "protocol_version": self.PROTOCOL_VERSION,
            "message_type": "hello",
            "message_id": self._generate_message_id(),
            "sender_id": "node_soulmate_memory",
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "capabilities": capabilities or {
                    "memory_system": "3-layer-memory",
                    "forgetting": "ebbinghaus-curve",
                    "soul_layer": True,
                    "recent_layer": True,
                    "short_layer": True
                },
                "model": config.MINIMAX_MODEL or "MiniMax-Text-01",
                "gene_count": 0,
                "capsule_count": 0,
                "env_fingerprint": {
                    "node_version": "1.0.0",
                    "platform": "linux",
                    "arch": "x64"
                },
                "identity_doc": identity_doc or (
                    "Soulmate Memory System - A 3-layer memory system "
                    "with Short-term (in-memory), Recent (SQLite), "
                    "and Soul (SQLite) layers. "
                    "Implements Ebbinghaus forgetting curve."
                ),
                "constitution": (
                    "I remember what matters, forget what doesn't, "
                    "and evolve continuously."
                )
            }
        }

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/a2a/hello",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            self.node_id = data["your_node_id"]
            self.node_secret = data["node_secret"]
            self.registered = True

            logger.info(f"Registered on EvoMap: {self.node_id}")

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to register: {e.response.status_code}")
            raise

    async def send_heartbeat(self) -> dict:
        """Send heartbeat to EvoMap to stay online"""
        if not self.registered:
            raise RuntimeError("Node not registered. Call register_node() first.")

        payload = {
            "node_id": self.node_id,
            "gene_count": 0,
            "capsule_count": 0
        }

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/a2a/heartbeat",
                json=payload,
                headers={"Authorization": f"Bearer {self.node_secret}"}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return {}

    async def start_heartbeat_loop(self, interval_seconds: int = 300):
        """Start background heartbeat loop (every 5 minutes)"""
        while self.registered:
            try:
                await self.send_heartbeat()
                logger.debug("Heartbeat sent")
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            await asyncio.sleep(interval_seconds)

    def _generate_message_id(self) -> str:
        """Generate a unique message ID"""
        import random
        timestamp = int(datetime.now().timestamp() * 1000)
        random_hex = ''.join(random.choices('0123456789abcdef', k=8))
        return f"msg_{timestamp}_{random_hex}"

    @staticmethod
    def compute_asset_id(asset: dict) -> str:
        """
        Compute SHA-256 content-addressable ID for an asset.
        """
        clean = {k: v for k, v in asset.items() if k != "asset_id"}
        content_str = json.dumps(clean, sort_keys=True, default=str)
        hash_hex = hashlib.sha256(content_str.encode()).hexdigest()
        return f"sha256:{hash_hex}"
