"""
API Routes - Memory System Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from memory_system.memory_system import MemorySystem
from memory_system.models import (
    CollectRequest,
    CollectResponse,
    RetrieveRequest,
    RetrieveResponse,
)


router = APIRouter(prefix="/memory", tags=["memory"])


def get_memory_system() -> MemorySystem:
    """Get memory system from app state"""
    from api.main import memory_system
    return memory_system


class ProcessRequest(BaseModel):
    user_id: str


@router.post("/collect", response_model=CollectResponse)
async def collect_memory(
    request: CollectRequest,
    ms: MemorySystem = Depends(get_memory_system)
):
    """
    Collect a memory.

    Stores the memory in the appropriate layer based on importance.
    """
    try:
        result = await ms.collect(
            user_id=request.user_id,
            content=request.content,
            event_type="user_said",
            emotion=request.emotion,
            topics=request.topics,
            metadata=request.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retrieve", response_model=RetrieveResponse)
async def retrieve_memory(
    user_id: str,
    query: str,
    session_id: Optional[str] = None,
    ms: MemorySystem = Depends(get_memory_system)
):
    """
    Retrieve context for response generation.

    Gets memories from all layers and formats them for LLM consumption.
    """
    try:
        result = await ms.retrieve(
            user_id=user_id,
            query=query,
            session_id=session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_memories(
    request: ProcessRequest,
    ms: MemorySystem = Depends(get_memory_system)
):
    """
    Run memory processing (promotion/demotion) for a user.
    """
    try:
        stats = await ms.process_user_memories(request.user_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_memory_stats(
    user_id: str,
    ms: MemorySystem = Depends(get_memory_system)
):
    """
    Get memory statistics for a user.
    """
    try:
        recent_count = await ms.recent.count(user_id)
        soul_count = await ms.soul.count(user_id)

        return {
            "user_id": user_id,
            "recent_memory_count": recent_count,
            "soul_memory_count": soul_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
