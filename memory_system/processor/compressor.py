"""
Compressor - Memory Compression

Compresses multiple messages into concise summaries.
"""
from typing import Optional
import httpx

from memory_system.models import CompressionResult
import config


class Compressor:
    """
    Compresses conversation messages into summaries.

    Features:
    - Extracts key entities and topics
    - Identifies emotional trajectory
    - Generates concise summaries

    In MVP, uses simple extraction-based compression.
    Can be upgraded to use LLM for better summaries.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0) if config.MINIMAX_API_KEY else None

    async def compress(
        self,
        messages: list[dict],
        user_id: str = None
    ) -> CompressionResult:
        """
        Compress a list of messages into a summary.

        Args:
            messages: List of {role, content, timestamp} dicts
            user_id: Optional user ID for personalized compression

        Returns:
            CompressionResult with summary, emotion, topics, etc.
        """
        if not messages:
            return CompressionResult(
                summary="",
                emotion="neutral",
                topics=[],
                importance_score=0.0,
                emotional_weight=0.5
            )

        # Simple extraction-based compression (MVP)
        # In production, use LLM for better results
        all_text = " ".join(m.get("content", "") for m in messages if m.get("content"))

        # Extract topics (simple keyword extraction)
        topics = self._extract_topics(all_text)

        # Detect emotion
        emotion, emotional_weight = self._detect_emotion(all_text)

        # Generate summary
        summary = self._generate_summary(messages)

        # Estimate importance
        importance = self._estimate_importance(emotional_weight, topics)

        return CompressionResult(
            summary=summary,
            emotion=emotion,
            topics=topics,
            key_entities=self._extract_entities(all_text),
            importance_score=importance,
            emotional_weight=emotional_weight
        )

    async def compress_with_llm(
        self,
        messages: list[dict],
        user_id: str = None
    ) -> CompressionResult:
        """
        Compress using MiniMax LLM for better results.
        """
        if not self.client or not config.MINIMAX_API_KEY:
            # Fallback to simple compression
            return await self.compress(messages, user_id)

        # Build prompt
        conversation_text = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in messages
        )

        prompt = f"""请将以下对话压缩成简洁的摘要：

{conversation_text}

请提取：
1. 摘要（1-2句话）
2. 情绪状态（positive/negative/neutral）
3. 主要话题
4. 关键实体

格式：JSON
"""

        try:
            response = await self.client.post(
                f"{config.MINIMAX_BASE_URL}/text/chatcompletion_v2",
                headers={
                    "Authorization": f"Bearer {config.MINIMAX_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.MINIMAX_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            data = response.json()

            # Parse LLM response (simplified)
            content = data["choices"][0]["message"]["content"]

            # In production, parse JSON from content
            # For now, fallback to simple compression
            return await self.compress(messages, user_id)

        except Exception as e:
            # Fallback to simple compression
            return await self.compress(messages, user_id)

    def _extract_topics(self, text: str) -> list[str]:
        """Simple topic extraction"""
        # Very basic - in production use NLP
        important_words = {
            "工作", "健康", "感情", "家庭", "朋友",
            "学习", "旅行", "电影", "音乐", "运动",
            "食物", "睡眠", "压力", "休息", "周末"
        }

        words = text.lower().split()
        found = [w for w in words if w in important_words]

        # Return unique, limited to 5
        return list(set(found))[:5]

    def _detect_emotion(self, text: str) -> tuple[str, float]:
        """Detect emotion and return (emotion, weight)"""
        positive = {"开心", "高兴", "棒", "好", "喜欢", "哈哈", "good", "happy", "great"}
        negative = {"难过", "伤心", "累", "气", "烦", "讨厌", "sad", "angry", "tired"}

        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)

        total = pos + neg
        if total == 0:
            return "neutral", 0.5

        if pos > neg:
            return "positive", min(0.9, 0.5 + pos * 0.1)
        else:
            return "negative", max(0.1, 0.5 - neg * 0.1)

    def _generate_summary(self, messages: list[dict]) -> str:
        """Generate a simple summary"""
        if not messages:
            return ""

        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return f"对话{len(messages)}条"

        # Just use first and last message as anchor
        first = user_messages[0].get("content", "")[:50]
        last = user_messages[-1].get("content", "")[:50]

        if len(user_messages) == 1:
            return first + "..."

        return f"{first}...{last}"

    def _extract_entities(self, text: str) -> list[str]:
        """Simple entity extraction"""
        # Very basic - just look for capitalized things
        # In production, use NER
        words = text.split()
        entities = [w for w in words if w and w[0].isupper() and len(w) > 1]
        return list(set(entities))[:5]

    def _estimate_importance(
        self,
        emotional_weight: float,
        topics: list[str]
    ) -> float:
        """Estimate importance based on emotional weight and topics"""
        base = abs(emotional_weight - 0.5) * 0.4  # 0.0 to 0.2
        topic_bonus = min(0.4, len(topics) * 0.1)
        return min(0.9, base + topic_bonus + 0.3)
