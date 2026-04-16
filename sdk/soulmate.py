"""
SDK - Agent SDK for Soulmate Memory

Provides a simple interface for agents to use the memory system.
"""
from typing import Optional
import requests


class SoulmateMemory:
    """
    Simple SDK for agents to use Soulmate Memory.

    Usage:
        memory = SoulmateMemory(user_id="user_123")

        # Collect a memory
        memory.collect(
            content="今天加班好累",
            emotion="negative",
            topics=["工作"]
        )

        # Get context for response
        context = memory.retrieve(query="工作")

    """

    def __init__(
        self,
        user_id: str,
        api_url: str = "http://localhost:8000",
        session_id: Optional[str] = None
    ):
        """
        Initialize the SDK.

        Args:
            user_id: Unique user identifier
            api_url: Base URL of the memory service
            session_id: Optional session ID for short-term context
        """
        self.user_id = user_id
        self.api_url = api_url.rstrip("/")
        self.session_id = session_id or f"session_{user_id}"

    def collect(
        self,
        content: str,
        emotion: Optional[str] = None,
        topics: list[str] = [],
        metadata: dict = {}
    ) -> dict:
        """
        Collect a memory.

        Args:
            content: Memory content
            emotion: Optional emotion (positive/negative/neutral)
            topics: Topic tags
            metadata: Additional metadata

        Returns:
            dict with collection result
        """
        try:
            response = requests.post(
                f"{self.api_url}/memory/collect",
                json={
                    "user_id": self.user_id,
                    "content": content,
                    "emotion": emotion,
                    "topics": topics,
                    "metadata": metadata
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def retrieve(self, query: str) -> dict:
        """
        Retrieve context for response generation.

        Args:
            query: Current query or message

        Returns:
            dict with context including soul_memories, recent_memories, short_context
        """
        try:
            response = requests.get(
                f"{self.api_url}/memory/retrieve",
                params={
                    "user_id": self.user_id,
                    "query": query,
                    "session_id": self.session_id
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def process(self) -> dict:
        """
        Trigger memory processing (promotion/demotion).

        Returns:
            dict with processing stats
        """
        try:
            response = requests.post(
                f"{self.api_url}/memory/process",
                json={"user_id": self.user_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> dict:
        """
        Get memory statistics for the user.

        Returns:
            dict with memory counts
        """
        try:
            response = requests.get(
                f"{self.api_url}/memory/user/{self.user_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────
    # Context manager for easy cleanup
    # ─────────────────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed for HTTP-based SDK
        pass


# ─────────────────────────────────────────────────────────────────
# Example usage
# ─────────────────────────────────────────────────────────────────

"""
Example: Using SoulmateMemory in an Agent

from soulmate_memory import SoulmateMemory

memory = SoulmateMemory(user_id="user_123")

def on_user_message(message: str):
    # 1. Collect the user message as memory
    memory.collect(
        content=message,
        emotion=detect_emotion(message),
        topics=extract_topics(message)
    )

    # 2. Retrieve context for response generation
    context = memory.retrieve(query=message)

    # 3. Generate response using LLM with context
    response = llm.generate(
        context=context["context_text"],
        message=message
    )

    # 4. Collect the agent response
    memory.collect(
        content=response,
        event_type="agent_response"
    )

    return response
"""
