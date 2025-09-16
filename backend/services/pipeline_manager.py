"""
Pipeline Manager - Manages RAG pipeline creation, configuration, and execution
"""

import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models import PipelineConfig, ComponentConfig, QueryResponse
from .plugin_manager import PluginManager
from .pipeline_validator import PipelineValidator
from .pipeline_executor import PipelineExecutor
from .pipeline_storage import PipelineStorage
from .document_processor import DocumentProcessor
from .embedding_manager import EmbeddingManager
from .pipeline_stats import PipelineStatsManager

logger = logging.getLogger(__name__)


class PipelineManager:
    """Manages RAG pipeline creation, configuration, and execution"""
    
    def __init__(self):
        self.storage = PipelineStorage()
        self.plugin_manager = PluginManager()
        self.validator = PipelineValidator(self.plugin_manager)
        self.executor = PipelineExecutor()
        self.document_processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager()
        self.stats_manager = PipelineStatsManager(self.storage, self.validator)
        
    async def create_pipeline(self, config: PipelineConfig) -> str:
        """Create a new RAG pipeline"""
        # Validate pipeline configuration
        if not await self.validator.validate_pipeline_config(config):
            raise ValueError("Invalid pipeline configuration")
        
        # Store pipeline configuration
        pipeline_id = self.storage.store_pipeline(config)
        
        # Initialize pipeline components
        await self._initialize_pipeline(pipeline_id)
        
        logger.info(f"Created pipeline: {pipeline_id}")
        return pipeline_id
    
    async def create_temp_pipeline(self, config: PipelineConfig) -> str:
        """Create a temporary pipeline for testing"""
        temp_id = f"temp_{uuid.uuid4()}"
        config.id = temp_id
        
        if not await self.validator.validate_pipeline_config(config):
            raise ValueError("Invalid pipeline configuration")
            
        self.storage.store_pipeline(config)
        await self._initialize_pipeline(temp_id)
        
        return temp_id
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration"""
        return self.storage.get_pipeline(pipeline_id)
    
    async def update_pipeline(self, pipeline_id: str, config: PipelineConfig):
        """Update pipeline configuration"""
        if not self.storage.pipeline_exists(pipeline_id):
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        if not await self.validator.validate_pipeline_config(config):
            raise ValueError("Invalid pipeline configuration")
            
        self.storage.update_pipeline(pipeline_id, config)
        
        # Reinitialize pipeline with new config
        await self._initialize_pipeline(pipeline_id)
        
        logger.info(f"Updated pipeline: {pipeline_id}")
    
    async def delete_pipeline(self, pipeline_id: str):
        """Delete a pipeline"""
        if self.storage.pipeline_exists(pipeline_id):
            # Clean up active pipeline resources
            if self.storage.is_pipeline_active(pipeline_id):
                await self._cleanup_pipeline(pipeline_id)
            
            self.storage.delete_pipeline(pipeline_id)
            logger.info(f"Deleted pipeline: {pipeline_id}")
    
    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines"""
        pipelines = []
        for pipeline in self.storage.list_pipelines():
            summary = self.storage.get_pipeline_summary(pipeline.id)
            if summary:
                summary["health_score"] = self.validator.get_pipeline_health_score(pipeline)
                pipelines.append(summary)
        return pipelines
    
    async def execute_query(self, pipeline_id: str, query: str, options: Dict[str, Any] = None) -> QueryResponse:
        """Execute a query through the RAG pipeline"""
        if not self.storage.pipeline_exists(pipeline_id):
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        if not self.storage.is_pipeline_active(pipeline_id):
            raise ValueError(f"Pipeline {pipeline_id} is not active")
        
        active_pipeline = self.storage.get_active_pipeline(pipeline_id)
        return await self.executor.execute_query(active_pipeline, query, options)
    
    async def validate_component_config(self, config: ComponentConfig) -> bool:
        """Validate component configuration"""
        return await self.validator.validate_component_config(config)
    
    async def get_pipeline_validation_errors(self, pipeline_id: str) -> List[str]:
        """Get validation errors for a pipeline"""
        config = self.storage.get_pipeline(pipeline_id)
        if not config:
            return ["Pipeline not found"]
        
        return self.validator.get_validation_errors(config)
    
    async def process_uploaded_data(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded data files"""
        if isinstance(file_data, list):
            # Batch processing
            return await self.document_processor.batch_process_documents(file_data)
        else:
            # Single file processing
            return await self.document_processor.process_file_upload(file_data)
    
    async def list_data_sources(self) -> List[Dict[str, Any]]:
        """List available data sources"""
        return [
            {
                "id": "sample_db",
                "name": "Sample Database",
                "type": "sqlite",
                "status": "available",
                "document_count": 100
            }
        ]
    
    async def _initialize_pipeline(self, pipeline_id: str):
        """Initialize pipeline components"""
        config = self.storage.get_pipeline(pipeline_id)
        if not config:
            raise ValueError(f"Pipeline {pipeline_id} not found")
            
        active_pipeline = {
            "config": config,
            "components": {},
            "initialized_at": datetime.now()
        }
        
        # Initialize each component
        for component in config.components:
            try:
                plugin = self.plugin_manager.get_plugin(component.type, component.subtype)
                if plugin:
                    instance = plugin(component.config)
                    await instance.initialize()
                    active_pipeline["components"][component.id] = {
                        "instance": instance,
                        "plugin": plugin,
                        "config": component
                    }
                    logger.info(f"Initialized component {component.id} ({component.type}:{component.subtype})")
            except Exception as e:
                logger.error(f"Failed to initialize component {component.id}: {str(e)}")
                raise
        
        self.storage.store_active_pipeline(pipeline_id, active_pipeline)
        logger.info(f"Pipeline {pipeline_id} initialized successfully")
    
    async def _cleanup_pipeline(self, pipeline_id: str):
        """Clean up pipeline resources"""
        active_pipeline = self.storage.get_active_pipeline(pipeline_id)
        if active_pipeline:
            # Clean up component instances
            for component_id, component_data in active_pipeline["components"].items():
                try:
                    instance = component_data["instance"]
                    if hasattr(instance, "cleanup"):
                        await instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up component {component_id}: {str(e)}")
            
            self.storage.remove_active_pipeline(pipeline_id)
            logger.info(f"Cleaned up pipeline {pipeline_id}")
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return self.stats_manager.get_comprehensive_stats()
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health overview"""
        return self.stats_manager.get_system_health_overview()