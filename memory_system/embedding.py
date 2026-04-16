"""
Embedding Service - Vector representation for text

Priority:
1. MiniMax API (if available with balance)
2. Sentence-Transformers (open source, free)
"""
import math
from typing import Optional

import httpx

import config

# Try to import sentence-transformers
try:
    import os
    # Use HuggingFace mirror if set
    if os.getenv("HF_ENDPOINT"):
        os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT")
    elif os.getenv("HF_MIRROR"):
        os.environ["HF_ENDPOINT"] = os.getenv("HF_MIRROR")

    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class EmbeddingService:
    """
    Generates embeddings for text using sentence-transformers or MiniMax API.

    Features:
    - Sentence-Transformers (primary, free & open source)
    - MiniMax API (fallback if available)
    - Cosine similarity computation
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self._model = None
        self._model_name = "BAAI/bge-small-zh-v1.5"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (list of floats)
        """
        if not texts:
            return []

        # Try sentence-transformers first
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                return await self._embed_sentence_transformers(texts)
            except Exception as e:
                print(f"Sentence-transformers failed: {e}, trying MiniMax")

        # Try MiniMax API
        if config.MINIMAX_API_KEY and config.MINIMAX_GROUP_ID:
            try:
                return await self._embed_minimax(texts)
            except Exception as e:
                print(f"MiniMax embedding failed: {e}")

        # Fallback to basic TF-IDF
        print("Falling back to basic TF-IDF embedding")
        return self._embed_tfidf(texts)

    def _get_model(self):
        """Lazy load the sentence-transformers model"""
        if self._model is None:
            print(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def _embed_sentence_transformers(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using sentence-transformers"""
        import asyncio

        # Run model inference in thread pool to avoid blocking
        def _embed():
            model = self._get_model()
            embeddings = model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, _embed)
        return embeddings

    async def _embed_minimax(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using MiniMax API"""
        group_id = config.MINIMAX_GROUP_ID
        if not group_id:
            raise ValueError("MINIMAX_GROUP_ID environment variable is required")

        response = await self.client.post(
            f"{config.MINIMAX_BASE_URL}/embeddings",
            params={"GroupId": group_id},
            headers={
                "Authorization": f"Bearer {config.MINIMAX_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "embo-01",
                "texts": texts,
                "type": "db"
            }
        )
        response.raise_for_status()
        data = response.json()

        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code", 0) != 0:
            raise ValueError(f"MiniMax API error: {base_resp}")

        embeddings = data.get("vectors", [])
        if not embeddings:
            raise ValueError(f"No vectors returned: {data}")

        return embeddings

    def _embed_tfidf(self, texts: list[str]) -> list[list[float]]:
        """Basic TF-IDF fallback (limited semantic capability)"""
        import re

        # Collect all Chinese characters
        all_chars = set()
        for text in texts:
            chinese = re.findall(r'[\u4e00-\u9fff]+', text)
            for chars in chinese:
                all_chars.update(chars)

        if not all_chars:
            return [[0.0] * 128 for _ in texts]

        char_list = sorted(all_chars)
        vocab = {c: i for i, c in enumerate(char_list)}
        dim = len(vocab)

        vectors = []
        for text in texts:
            vec = [0.0] * dim
            chinese = re.findall(r'[\u4e00-\u9fff]+', text)
            for chars in chinese:
                for char in chars:
                    if char in vocab:
                        vec[vocab[char]] += 1

            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            vectors.append(vec)

        return vectors

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0

        dot_prod = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(v * v for v in a))
        norm_b = math.sqrt(sum(v * v for v in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_prod / (norm_a * norm_b)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
