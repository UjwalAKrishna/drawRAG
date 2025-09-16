"""
API - Ultra-flexible API using the framework
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path

# Import routes
from backend.api.routes import plugins, capabilities, pipeline, rag
from backend.api.dependencies import initialize_manager, shutdown_manager

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Builder API",
    description="Ultra-flexible API powered by plugin framework",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
try:
    app.include_router(plugins.router)
    app.include_router(capabilities.router)
    app.include_router(pipeline.router)
    app.include_router(rag.router)
    logger.info("All routers included successfully")
except Exception as e:
    logger.error(f"Failed to include routers: {e}")
    import traceback
    traceback.print_exc()

@app.on_event("startup")
async def startup_event():
    """Initialize the framework"""
    try:
        manager = await initialize_manager()
        logger.info(f"API started with manager: {manager}")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup"""
    await shutdown_manager()
    logger.info("API shutdown complete")

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from backend.api.dependencies import get_manager
    manager = get_manager()
    status = manager.get_system_status()
    return {"status": "healthy", **status}

# System information
@app.get("/api/system/info")
async def get_system_info():
    """Get complete system information"""
    from backend.api.dependencies import get_manager
    manager = get_manager()
    return {
        "version": "3.0.0",
        "framework": "Plugin Framework",
        "system_status": manager.get_system_status(),
        "capabilities": {
            "dynamic_loading": True,
            "hot_reload": True,
            "auto_discovery": True,
            "zero_config": True,
            "capability_routing": True,
            "event_system": True,
            "middleware": True,
            "extensions": True
        }
    }

# Serve frontend static files
if Path("frontend").exists():
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)