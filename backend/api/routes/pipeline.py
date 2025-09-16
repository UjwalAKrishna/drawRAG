"""
Pipeline Management API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json
from pathlib import Path
import uuid
from datetime import datetime

from backend.api.dependencies import get_manager

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/validate")
async def validate_pipeline(pipeline_config: Dict[str, Any]):
    """Validate a pipeline configuration"""
    manager = get_manager()
    
    try:
        # Check if all required components exist
        components = pipeline_config.get("components", [])
        connections = pipeline_config.get("connections", [])
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "component_count": len(components),
            "connection_count": len(connections)
        }
        
        # Validate each component
        for component in components:
            component_type = component.get("type")
            plugin_id = component.get("plugin_id")
            
            # Check if plugin exists
            plugin_info = manager.get_plugin_info(plugin_id)
            if not plugin_info:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Plugin '{plugin_id}' not found")
                continue
            
            # Check if plugin provides required capabilities
            required_capabilities = component.get("capabilities", [])
            available_capabilities = list(plugin_info.get("capabilities", {}).keys())
            
            for capability in required_capabilities:
                if capability not in available_capabilities:
                    validation_result["warnings"].append(
                        f"Plugin '{plugin_id}' may not provide capability '{capability}'"
                    )
        
        # Validate connections
        component_ids = {comp["id"] for comp in components}
        for connection in connections:
            source = connection.get("source")
            target = connection.get("target")
            
            if source not in component_ids:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Connection source '{source}' not found")
            
            if target not in component_ids:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Connection target '{target}' not found")
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")


@router.post("/execute")
async def execute_pipeline(request: Dict[str, Any]):
    """Execute a pipeline with given input"""
    manager = get_manager()
    
    try:
        pipeline_config = request.get("pipeline_config", {})
        input_data = request.get("input_data", {})
        
        # For now, execute components in sequence
        # TODO: Implement proper graph execution based on connections
        components = pipeline_config.get("components", [])
        current_data = input_data
        
        execution_log = []
        
        for component in components:
            plugin_id = component.get("plugin_id")
            capabilities = component.get("capabilities", [])
            config = component.get("config", {})
            
            for capability in capabilities:
                try:
                    result = await manager.call(
                        capability, 
                        current_data, 
                        plugin_id=plugin_id,
                        **config
                    )
                    current_data = result
                    execution_log.append({
                        "component_id": component["id"],
                        "plugin_id": plugin_id,
                        "capability": capability,
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    execution_log.append({
                        "component_id": component["id"],
                        "plugin_id": plugin_id,
                        "capability": capability,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    raise
        
        return {
            "success": True,
            "result": current_data,
            "execution_log": execution_log
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pipeline execution error: {str(e)}")


@router.post("/save")
async def save_pipeline(pipeline_data: Dict[str, Any]):
    """Save a pipeline configuration"""
    try:
        pipelines_dir = Path("pipelines")
        pipelines_dir.mkdir(exist_ok=True)
        
        pipeline_id = pipeline_data.get("id") or str(uuid.uuid4())
        pipeline_name = pipeline_data.get("name", "Untitled Pipeline")
        
        pipeline_file = pipelines_dir / f"{pipeline_id}.json"
        
        # Add metadata
        pipeline_data.update({
            "id": pipeline_id,
            "name": pipeline_name,
            "saved_at": datetime.now().isoformat(),
            "version": "1.0"
        })
        
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline_data, f, indent=2)
        
        return {
            "success": True,
            "pipeline_id": pipeline_id,
            "message": "Pipeline saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save pipeline: {str(e)}")


@router.get("/load/{pipeline_id}")
async def load_pipeline(pipeline_id: str):
    """Load a saved pipeline configuration"""
    try:
        pipeline_file = Path("pipelines") / f"{pipeline_id}.json"
        
        if not pipeline_file.exists():
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        with open(pipeline_file, 'r') as f:
            pipeline_data = json.load(f)
        
        return pipeline_data
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load pipeline: {str(e)}")


@router.get("/list")
async def list_pipelines():
    """List all saved pipelines"""
    try:
        pipelines_dir = Path("pipelines")
        if not pipelines_dir.exists():
            return {"pipelines": []}
        
        pipelines = []
        for pipeline_file in pipelines_dir.glob("*.json"):
            try:
                with open(pipeline_file, 'r') as f:
                    pipeline_data = json.load(f)
                
                pipelines.append({
                    "id": pipeline_data.get("id"),
                    "name": pipeline_data.get("name"),
                    "saved_at": pipeline_data.get("saved_at"),
                    "component_count": len(pipeline_data.get("components", [])),
                    "connection_count": len(pipeline_data.get("connections", []))
                })
            except Exception as e:
                continue  # Skip corrupted files
        
        return {"pipelines": pipelines}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list pipelines: {str(e)}")