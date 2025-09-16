"""
Plugin Management API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List
import logging
import tempfile
import os
from pathlib import Path

from backend.api.dependencies import get_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("/")
async def list_plugins():
    """List all loaded plugins with their capabilities"""
    manager = get_manager()
    plugins = manager.list_plugins()
    return {"plugins": plugins}


@router.get("/{plugin_id}")
async def get_plugin_info(plugin_id: str):
    """Get detailed plugin information"""
    manager = get_manager()
    info = manager.get_plugin_info(plugin_id)
    if not info:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return info


@router.post("/upload")
async def upload_plugin(file: UploadFile = File(...)):
    """Upload and install a new plugin"""
    manager = get_manager()
    
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files are allowed")
    
    try:
        # Save uploaded file to plugins directory
        plugins_dir = Path("plugins")
        plugins_dir.mkdir(exist_ok=True)
        
        file_path = plugins_dir / file.filename
        
        # Read and save file content
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Try to load the plugin
        success = await manager.discover_and_load_plugins(str(plugins_dir))
        
        if success:
            return {
                "success": True, 
                "message": f"Plugin {file.filename} uploaded and loaded successfully",
                "filename": file.filename
            }
        else:
            # Remove file if loading failed
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Failed to load plugin")
            
    except Exception as e:
        logger.error(f"Error uploading plugin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/reload")
async def reload_plugin(plugin_id: str):
    """Hot reload a specific plugin"""
    manager = get_manager()
    success = await manager.reload_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found or reload failed")
    return {"success": True, "plugin_id": plugin_id, "message": "Plugin reloaded successfully"}


@router.delete("/{plugin_id}")
async def unload_plugin(plugin_id: str):
    """Unload a plugin"""
    manager = get_manager()
    success = await manager.unload_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"success": True, "plugin_id": plugin_id, "message": "Plugin unloaded successfully"}


@router.post("/reload_all")
async def reload_all_plugins():
    """Reload all plugins"""
    manager = get_manager()
    results = await manager.reload_all()
    return {"results": results, "message": "All plugins reloaded"}