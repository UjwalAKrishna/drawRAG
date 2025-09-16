"""
Capabilities API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.api.dependencies import get_manager

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("/")
async def list_capabilities():
    """List all available capabilities"""
    manager = get_manager()
    capabilities = manager.list_capabilities()
    return {"capabilities": capabilities}


@router.get("/{capability}")
async def discover_capability_providers(capability: str):
    """Find all plugins that provide a capability"""
    manager = get_manager()
    providers = manager.discover_providers(capability)
    return {"capability": capability, "providers": providers}


@router.post("/call/{capability}")
async def call_capability(capability: str, request: Dict[str, Any]):
    """Call any capability dynamically"""
    manager = get_manager()
    
    try:
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})
        plugin_id = request.get("plugin_id")  # Optional specific plugin
        
        if plugin_id:
            result = await manager.call(capability, *args, plugin_id=plugin_id, **kwargs)
        else:
            result = await manager.call(capability, *args, **kwargs)
        
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call_all/{capability}")
async def call_all_providers(capability: str, request: Dict[str, Any]):
    """Call capability on all plugins that provide it"""
    manager = get_manager()
    
    try:
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})
        
        results = await manager.call_all(capability, *args, **kwargs)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))