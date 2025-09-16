"""
RAG Builder API - Thin layer over core framework
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List
import logging
from pathlib import Path

# Import core framework
from core.plugin_manager import CorePluginManager

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Builder API",
    description="Core API for RAG Builder framework",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core plugin manager
core_manager = CorePluginManager("plugins")

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    try:
        await core_manager.initialize()
        logger.info("RAG Builder API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await core_manager.shutdown()
    logger.info("RAG Builder API shutdown complete")

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    status = core_manager.get_system_status()
    return {"status": "healthy" if status["initialized"] else "unhealthy", **status}

# System Information
@app.get("/api/system/info")
async def get_system_info():
    """Get system information"""
    status = core_manager.get_system_status()
    plugin_types = core_manager.list_plugin_types()
    
    return {
        "version": "2.0.0",
        "framework": "Core Plugin Framework",
        "status": status,
        "plugin_types": plugin_types,
        "capabilities": {
            "hot_plugin_loading": True,
            "pipeline_execution": True,
            "dynamic_configuration": True,
            "plugin_marketplace": False  # Future feature
        }
    }

# Plugin Management
@app.get("/api/plugins/types")
async def list_plugin_types():
    """List available plugin types"""
    types = core_manager.list_plugin_types()
    return {"plugin_types": types}

@app.get("/api/plugins/instances")
async def list_plugin_instances():
    """List active plugin instances"""
    instances = core_manager.list_plugin_instances()
    return {"plugin_instances": instances}

@app.post("/api/plugins/load")
async def load_plugin(request: Dict[str, Any]):
    """Load a plugin instance"""
    plugin_type = request.get("plugin_type")
    plugin_id = request.get("plugin_id")
    config = request.get("config", {})
    
    if not plugin_type or not plugin_id:
        raise HTTPException(status_code=400, detail="plugin_type and plugin_id are required")
    
    success = await core_manager.load_plugin_instance(plugin_type, plugin_id, config)
    if success:
        return {"status": "success", "plugin_id": plugin_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to load plugin")

@app.post("/api/plugins/unload/{plugin_id}")
async def unload_plugin(plugin_id: str):
    """Unload a plugin instance"""
    success = await core_manager.unload_plugin_instance(plugin_id)
    if success:
        return {"status": "success", "plugin_id": plugin_id}
    else:
        raise HTTPException(status_code=404, detail="Plugin not found")

@app.post("/api/plugins/install")
async def install_plugin(request: Dict[str, Any]):
    """Install a plugin package"""
    package_path = request.get("package_path")
    if not package_path:
        raise HTTPException(status_code=400, detail="package_path is required")
    
    success = await core_manager.install_plugin(package_path)
    if success:
        return {"status": "success", "message": "Plugin installed successfully"}
    else:
        raise HTTPException(status_code=400, detail="Plugin installation failed")

# Pipeline Management
@app.get("/api/pipelines")
async def list_pipelines():
    """List all pipelines"""
    pipelines = core_manager.list_pipelines()
    return {"pipelines": pipelines}

@app.post("/api/pipelines")
async def create_pipeline(request: Dict[str, Any]):
    """Create a new pipeline"""
    name = request.get("name")
    pipeline_id = core_manager.create_pipeline(name)
    return {"pipeline_id": pipeline_id, "name": name}

@app.post("/api/pipelines/{pipeline_id}/nodes")
async def add_pipeline_node(pipeline_id: str, request: Dict[str, Any]):
    """Add a node to a pipeline"""
    node_id = request.get("node_id")
    plugin_id = request.get("plugin_id")
    config = request.get("config", {})
    
    if not node_id or not plugin_id:
        raise HTTPException(status_code=400, detail="node_id and plugin_id are required")
    
    success = core_manager.add_pipeline_node(pipeline_id, node_id, plugin_id, config)
    if success:
        return {"status": "success", "node_id": node_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to add node")

@app.post("/api/pipelines/{pipeline_id}/connections")
async def connect_pipeline_nodes(pipeline_id: str, request: Dict[str, Any]):
    """Connect two nodes in a pipeline"""
    source_node = request.get("source_node")
    target_node = request.get("target_node")
    
    if not source_node or not target_node:
        raise HTTPException(status_code=400, detail="source_node and target_node are required")
    
    success = core_manager.connect_pipeline_nodes(pipeline_id, source_node, target_node)
    if success:
        return {"status": "success", "connection": f"{source_node} -> {target_node}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to connect nodes")

@app.post("/api/pipelines/{pipeline_id}/execute")
async def execute_pipeline(pipeline_id: str, request: Dict[str, Any]):
    """Execute a pipeline"""
    input_data = request.get("input_data", {})
    
    try:
        result = await core_manager.execute_pipeline(pipeline_id, input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Plugin Interaction Endpoints
@app.post("/api/plugins/{plugin_id}/execute")
async def execute_plugin(plugin_id: str, request: Dict[str, Any]):
    """Execute a plugin directly"""
    plugin = core_manager.get_plugin_instance(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    input_data = request.get("input_data", {})
    config = request.get("config", {})
    
    try:
        if hasattr(plugin, 'execute'):
            result = await plugin.execute(input_data, config, {})
            return result
        else:
            raise HTTPException(status_code=400, detail="Plugin does not support direct execution")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Legacy compatibility - redirect to plugins
@app.post("/api/data/upload")
async def upload_data(file_data: Dict[str, Any]):
    """Legacy document upload endpoint"""
    # Try to find document processor plugin
    instances = core_manager.list_plugin_instances()
    doc_processor = None
    
    for instance_id in instances:
        plugin = core_manager.get_plugin_instance(instance_id)
        if plugin and "process_documents" in plugin.get_capabilities():
            doc_processor = plugin
            break
    
    if not doc_processor:
        # Auto-load document processor
        success = await core_manager.load_plugin_instance(
            "utility_document_processing", 
            "doc_processor_1", 
            {"upload_dir": "uploads"}
        )
        if success:
            doc_processor = core_manager.get_plugin_instance("doc_processor_1")
    
    if doc_processor:
        return await doc_processor.execute({"file": file_data}, {}, {})
    else:
        raise HTTPException(status_code=500, detail="Document processor not available")

# Serve frontend static files
if Path("frontend").exists():
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)