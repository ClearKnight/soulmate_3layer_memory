"""
API - FastAPI Entry Point
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from memory_system.memory_system import MemorySystem
from api.routes import router as memory_router


# Global memory system instance
memory_system: MemorySystem = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global memory_system

    # Startup
    memory_system = MemorySystem()
    await memory_system.initialize()

    # Store in app state
    app.state.memory_system = memory_system

    yield

    # Shutdown
    await memory_system.close()


app = FastAPI(
    title="Soulmate Memory System",
    description="A 3-layer human-like memory system for AI agents",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(memory_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "alive",
        "service": "soulmate-memory",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Soulmate Memory System",
        "version": "0.1.0",
        "description": "A 3-layer human-like memory system for AI agents"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
