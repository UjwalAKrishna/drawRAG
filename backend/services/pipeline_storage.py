"""
Pipeline Storage - Handles pipeline persistence and retrieval
"""

import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models import PipelineConfig

logger = logging.getLogger(__name__)


class PipelineStorage:
    """Manages pipeline storage and retrieval operations"""
    
    def __init__(self):
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
    
    def store_pipeline(self, config: PipelineConfig) -> str:
        """Store a pipeline configuration"""
        pipeline_id = config.id or str(uuid.uuid4())
        config.id = pipeline_id
        
        if not config.created_at:
            config.created_at = datetime.now()
        config.updated_at = datetime.now()
        
        self.pipelines[pipeline_id] = config
        logger.info(f"Stored pipeline: {pipeline_id}")
        return pipeline_id
    
    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration by ID"""
        return self.pipelines.get(pipeline_id)
    
    def update_pipeline(self, pipeline_id: str, config: PipelineConfig) -> bool:
        """Update existing pipeline configuration"""
        if pipeline_id not in self.pipelines:
            return False
        
        config.id = pipeline_id
        config.updated_at = datetime.now()
        config.created_at = self.pipelines[pipeline_id].created_at
        
        self.pipelines[pipeline_id] = config
        logger.info(f"Updated pipeline: {pipeline_id}")
        return True
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline configuration"""
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            logger.info(f"Deleted pipeline: {pipeline_id}")
            return True
        return False
    
    def list_pipelines(self) -> List[PipelineConfig]:
        """List all stored pipelines"""
        return list(self.pipelines.values())
    
    def pipeline_exists(self, pipeline_id: str) -> bool:
        """Check if pipeline exists"""
        return pipeline_id in self.pipelines
    
    def get_pipeline_count(self) -> int:
        """Get total number of pipelines"""
        return len(self.pipelines)
    
    def store_active_pipeline(self, pipeline_id: str, active_data: Dict[str, Any]):
        """Store active pipeline runtime data"""
        self.active_pipelines[pipeline_id] = active_data
        logger.info(f"Stored active pipeline data: {pipeline_id}")
    
    def get_active_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get active pipeline runtime data"""
        return self.active_pipelines.get(pipeline_id)
    
    def remove_active_pipeline(self, pipeline_id: str) -> bool:
        """Remove active pipeline runtime data"""
        if pipeline_id in self.active_pipelines:
            del self.active_pipelines[pipeline_id]
            logger.info(f"Removed active pipeline data: {pipeline_id}")
            return True
        return False
    
    def is_pipeline_active(self, pipeline_id: str) -> bool:
        """Check if pipeline is currently active"""
        return pipeline_id in self.active_pipelines
    
    def get_active_pipeline_count(self) -> int:
        """Get number of active pipelines"""
        return len(self.active_pipelines)
    
    def list_active_pipeline_ids(self) -> List[str]:
        """List all active pipeline IDs"""
        return list(self.active_pipelines.keys())
    
    def get_pipeline_summary(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline summary information"""
        config = self.get_pipeline(pipeline_id)
        if not config:
            return None
        
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "component_count": len(config.components),
            "connection_count": len(config.connections),
            "status": "active" if self.is_pipeline_active(pipeline_id) else "inactive",
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
    
    def search_pipelines(self, query: str) -> List[PipelineConfig]:
        """Search pipelines by name or description"""
        query_lower = query.lower()
        results = []
        
        for pipeline in self.pipelines.values():
            if (query_lower in pipeline.name.lower() or 
                (pipeline.description and query_lower in pipeline.description.lower())):
                results.append(pipeline)
        
        return results
    
    def get_pipelines_by_component_type(self, component_type: str) -> List[PipelineConfig]:
        """Get pipelines that use a specific component type"""
        results = []
        
        for pipeline in self.pipelines.values():
            for component in pipeline.components:
                if component.type == component_type:
                    results.append(pipeline)
                    break
        
        return results
    
    def clear_all_pipelines(self):
        """Clear all pipeline data (use with caution)"""
        self.pipelines.clear()
        self.active_pipelines.clear()
        logger.warning("Cleared all pipeline data")
    
    def export_pipelines(self) -> List[Dict[str, Any]]:
        """Export all pipelines as dictionaries"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "components": [c.dict() for c in p.components],
                "connections": [conn.dict() for conn in p.connections],
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in self.pipelines.values()
        ]
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "total_pipelines": len(self.pipelines),
            "active_pipelines": len(self.active_pipelines),
            "storage_size_kb": self._estimate_storage_size(),
            "oldest_pipeline": self._get_oldest_pipeline_date(),
            "newest_pipeline": self._get_newest_pipeline_date()
        }
    
    def _estimate_storage_size(self) -> float:
        """Estimate storage size in KB (rough approximation)"""
        import sys
        total_size = 0
        total_size += sys.getsizeof(self.pipelines)
        total_size += sys.getsizeof(self.active_pipelines)
        return total_size / 1024
    
    def _get_oldest_pipeline_date(self) -> Optional[str]:
        """Get creation date of oldest pipeline"""
        if not self.pipelines:
            return None
        
        oldest = min(p.created_at for p in self.pipelines.values() if p.created_at)
        return oldest.isoformat() if oldest else None
    
    def _get_newest_pipeline_date(self) -> Optional[str]:
        """Get creation date of newest pipeline"""
        if not self.pipelines:
            return None
        
        newest = max(p.created_at for p in self.pipelines.values() if p.created_at)
        return newest.isoformat() if newest else None