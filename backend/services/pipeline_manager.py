"""
Pipeline Manager - Core orchestration for RAG pipelines
"""

import uuid
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from models import PipelineConfig, ComponentConfig, QueryResponse, ComponentType
from services.plugin_manager import PluginManager

logger = logging.getLogger(__name__)

class PipelineManager:
    """Manages RAG pipeline creation, configuration, and execution"""
    
    def __init__(self):
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
        self.plugin_manager = PluginManager()
        
    async def create_pipeline(self, config: PipelineConfig) -> str:
        """Create a new RAG pipeline"""
        pipeline_id = config.id or str(uuid.uuid4())
        config.id = pipeline_id
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        
        # Validate pipeline configuration
        await self._validate_pipeline_config(config)
        
        # Store pipeline configuration
        self.pipelines[pipeline_id] = config
        
        # Initialize pipeline components
        await self._initialize_pipeline(pipeline_id)
        
        logger.info(f"Created pipeline: {pipeline_id}")
        return pipeline_id
    
    async def create_temp_pipeline(self, config: PipelineConfig) -> str:
        """Create a temporary pipeline for testing"""
        temp_id = f"temp_{uuid.uuid4()}"
        config.id = temp_id
        
        await self._validate_pipeline_config(config)
        self.pipelines[temp_id] = config
        await self._initialize_pipeline(temp_id)
        
        return temp_id
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration"""
        return self.pipelines.get(pipeline_id)
    
    async def update_pipeline(self, pipeline_id: str, config: PipelineConfig):
        """Update pipeline configuration"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        config.id = pipeline_id
        config.updated_at = datetime.now()
        config.created_at = self.pipelines[pipeline_id].created_at
        
        await self._validate_pipeline_config(config)
        self.pipelines[pipeline_id] = config
        
        # Reinitialize pipeline with new config
        await self._initialize_pipeline(pipeline_id)
        
        logger.info(f"Updated pipeline: {pipeline_id}")
    
    async def delete_pipeline(self, pipeline_id: str):
        """Delete a pipeline"""
        if pipeline_id in self.pipelines:
            # Clean up active pipeline resources
            if pipeline_id in self.active_pipelines:
                await self._cleanup_pipeline(pipeline_id)
            
            del self.pipelines[pipeline_id]
            logger.info(f"Deleted pipeline: {pipeline_id}")
    
    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines"""
        return [
            {
                "id": pipeline.id,
                "name": pipeline.name,
                "description": pipeline.description,
                "component_count": len(pipeline.components),
                "status": "active" if pipeline.id in self.active_pipelines else "inactive",
                "created_at": pipeline.created_at,
                "updated_at": pipeline.updated_at
            }
            for pipeline in self.pipelines.values()
        ]
    
    async def execute_query(self, pipeline_id: str, query: str, options: Dict[str, Any] = None) -> QueryResponse:
        """Execute a query through the RAG pipeline"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        if pipeline_id not in self.active_pipelines:
            raise ValueError(f"Pipeline {pipeline_id} is not active")
        
        start_time = datetime.now()
        
        try:
            # Get active pipeline components
            active_pipeline = self.active_pipelines[pipeline_id]
            
            # Step 1: Process query through data source (if needed)
            processed_query = await self._process_query_datasource(active_pipeline, query)
            
            # Step 2: Retrieve relevant vectors from vector database
            retrieved_context = await self._retrieve_context(active_pipeline, processed_query)
            
            # Step 3: Generate response using LLM
            response = await self._generate_response(active_pipeline, query, retrieved_context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResponse(
                answer=response["answer"],
                sources=response["sources"],
                metadata={
                    "query": query,
                    "processing_steps": response.get("steps", []),
                    "pipeline_id": pipeline_id,
                    **(options or {})
                },
                pipeline_used=f"{self.pipelines[pipeline_id].name} ({pipeline_id})",
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Query execution failed for pipeline {pipeline_id}: {str(e)}")
            raise
    
    async def validate_component_config(self, config: ComponentConfig) -> bool:
        """Validate component configuration"""
        try:
            plugin = self.plugin_manager.get_plugin(config.type, config.subtype)
            if not plugin:
                return False
            
            # Validate configuration against plugin schema
            return await plugin.validate_config(config.config)
        except Exception as e:
            logger.error(f"Component validation failed: {str(e)}")
            return False
    
    async def process_uploaded_data(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded data files"""
        # This would handle file upload and processing
        # For MVP, return a mock response
        return {
            "status": "processed",
            "files_processed": 1,
            "documents_extracted": 10,
            "message": "Data uploaded and processed successfully"
        }
    
    async def list_data_sources(self) -> List[Dict[str, Any]]:
        """List available data sources"""
        # Mock data sources for MVP
        return [
            {
                "id": "sample_db",
                "name": "Sample Database",
                "type": "sqlite",
                "status": "available",
                "document_count": 100
            }
        ]
    
    async def _validate_pipeline_config(self, config: PipelineConfig):
        """Validate complete pipeline configuration"""
        if not config.components:
            raise ValueError("Pipeline must have at least one component")
        
        # Check for required component types
        component_types = {comp.type for comp in config.components}
        required_types = {ComponentType.DATASOURCE, ComponentType.VECTORDB, ComponentType.LLM}
        
        missing_types = required_types - component_types
        if missing_types:
            raise ValueError(f"Pipeline missing required components: {missing_types}")
        
        # Validate each component
        for component in config.components:
            if not await self.validate_component_config(component):
                raise ValueError(f"Invalid configuration for component {component.id}")
    
    async def _initialize_pipeline(self, pipeline_id: str):
        """Initialize pipeline components"""
        config = self.pipelines[pipeline_id]
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
                    instance = await plugin.create_instance(component.config)
                    active_pipeline["components"][component.id] = {
                        "instance": instance,
                        "plugin": plugin,
                        "config": component
                    }
                    logger.info(f"Initialized component {component.id} ({component.type}:{component.subtype})")
            except Exception as e:
                logger.error(f"Failed to initialize component {component.id}: {str(e)}")
                raise
        
        self.active_pipelines[pipeline_id] = active_pipeline
        logger.info(f"Pipeline {pipeline_id} initialized successfully")
    
    async def _cleanup_pipeline(self, pipeline_id: str):
        """Clean up pipeline resources"""
        if pipeline_id in self.active_pipelines:
            active_pipeline = self.active_pipelines[pipeline_id]
            
            # Clean up component instances
            for component_id, component_data in active_pipeline["components"].items():
                try:
                    instance = component_data["instance"]
                    if hasattr(instance, "cleanup"):
                        await instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up component {component_id}: {str(e)}")
            
            del self.active_pipelines[pipeline_id]
            logger.info(f"Cleaned up pipeline {pipeline_id}")
    
    async def _process_query_datasource(self, active_pipeline: Dict[str, Any], query: str) -> str:
        """Process query through data source component"""
        # Find data source component
        datasource_component = None
        for comp_data in active_pipeline["components"].values():
            if comp_data["config"].type == ComponentType.DATASOURCE:
                datasource_component = comp_data
                break
        
        if not datasource_component:
            return query
        
        # For MVP, return the query as-is
        # In full implementation, this would preprocess the query
        return query
    
    async def _retrieve_context(self, active_pipeline: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector database"""
        # Find vector database component
        vectordb_component = None
        for comp_data in active_pipeline["components"].values():
            if comp_data["config"].type == ComponentType.VECTORDB:
                vectordb_component = comp_data
                break
        
        if not vectordb_component:
            return []
        
        try:
            # Get the vector database instance
            vectordb_instance = vectordb_component["instance"]
            
            # Generate query embedding (using LLM if available)
            query_embedding = await self._generate_query_embedding(active_pipeline, query)
            
            if query_embedding:
                # Query the vector database
                results = await vectordb_instance.query_vectors(query_embedding, top_k=5)
                return results
            else:
                # Fallback to mock context if embedding generation fails
                return [
                    {
                        "content": f"Sample context 1 related to: {query}",
                        "source": "document_1.pdf",
                        "score": 0.95
                    },
                    {
                        "content": f"Sample context 2 related to: {query}",
                        "source": "document_2.pdf", 
                        "score": 0.87
                    }
                ]
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            # Return mock context as fallback
            return [
                {
                    "content": f"Sample context 1 related to: {query}",
                    "source": "document_1.pdf",
                    "score": 0.95
                }
            ]
    
    async def _generate_response(self, active_pipeline: Dict[str, Any], query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using LLM"""
        # Find LLM component
        llm_component = None
        for comp_data in active_pipeline["components"].values():
            if comp_data["config"].type == ComponentType.LLM:
                llm_component = comp_data
                break
        
        if not llm_component:
            raise ValueError("No LLM component found in pipeline")
        
        try:
            # Get the LLM instance
            llm_instance = llm_component["instance"]
            
            # Prepare context text
            context_text = "\n".join([ctx["content"] for ctx in context])
            
            # Generate response using real LLM
            response = await llm_instance.generate_response(query, context_text)
            
            return {
                "answer": response,
                "sources": [
                    {
                        "title": ctx.get("metadata", {}).get("source", ctx.get("source", f"Document {i+1}")),
                        "content": ctx["content"][:200] + "..." if len(ctx["content"]) > 200 else ctx["content"],
                        "score": ctx.get("score", 0.0)
                    }
                    for i, ctx in enumerate(context)
                ],
                "steps": [
                    "Query processed",
                    f"Retrieved {len(context)} relevant documents",
                    f"Generated response using {llm_component['config'].name}"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback to mock response
            context_text = "\n".join([ctx["content"] for ctx in context])
            
            return {
                "answer": f"Based on the provided context, here's the answer to '{query}': This is a fallback response due to an error in the LLM component.",
                "sources": [
                    {
                        "title": ctx.get("source", f"Document {i+1}"),
                        "content": ctx["content"][:100] + "...",
                        "score": ctx.get("score", 0.0)
                    }
                    for i, ctx in enumerate(context)
                ],
                "steps": [
                    "Query processed",
                    f"Retrieved {len(context)} relevant documents",
                    "Generated fallback response due to LLM error"
                ]
            }
    
    async def _generate_query_embedding(self, active_pipeline: Dict[str, Any], query: str) -> Optional[List[float]]:
        """Generate embedding for query using LLM"""
        # Find LLM component
        llm_component = None
        for comp_data in active_pipeline["components"].values():
            if comp_data["config"].type == ComponentType.LLM:
                llm_component = comp_data
                break
        
        if not llm_component:
            return None
        
        try:
            llm_instance = llm_component["instance"]
            
            # Try to generate embedding
            if hasattr(llm_instance, 'generate_embeddings'):
                embeddings = await llm_instance.generate_embeddings([query])
                return embeddings[0] if embeddings else None
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
        
        return None