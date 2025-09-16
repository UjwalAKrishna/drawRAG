"""
Pipeline Executor - Handles RAG query execution through pipelines
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from models import ComponentType, QueryResponse

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Executes queries through RAG pipelines"""
    
    def __init__(self):
        pass
    
    async def execute_query(self, active_pipeline: Dict[str, Any], query: str, options: Dict[str, Any] = None) -> QueryResponse:
        """Execute a query through the RAG pipeline"""
        start_time = datetime.now()
        
        try:
            # Step 1: Process query through data source (if needed)
            processed_query = await self._process_query_datasource(active_pipeline, query)
            
            # Step 2: Retrieve relevant vectors from vector database
            retrieved_context = await self._retrieve_context(active_pipeline, processed_query)
            
            # Step 3: Generate response using LLM
            response = await self._generate_response(active_pipeline, query, retrieved_context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            pipeline_config = active_pipeline["config"]
            return QueryResponse(
                answer=response["answer"],
                sources=response["sources"],
                metadata={
                    "query": query,
                    "processing_steps": response.get("steps", []),
                    "pipeline_id": pipeline_config.id,
                    **(options or {})
                },
                pipeline_used=f"{pipeline_config.name} ({pipeline_config.id})",
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def _process_query_datasource(self, active_pipeline: Dict[str, Any], query: str) -> str:
        """Process query through data source component"""
        datasource_component = self._find_component_by_type(active_pipeline, ComponentType.DATASOURCE)
        
        if not datasource_component:
            return query
        
        # For MVP, return the query as-is
        # In full implementation, this would preprocess the query
        return query
    
    async def _retrieve_context(self, active_pipeline: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector database"""
        vectordb_component = self._find_component_by_type(active_pipeline, ComponentType.VECTORDB)
        
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
                return self._get_mock_context(query)
                
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return self._get_mock_context(query)
    
    async def _generate_response(self, active_pipeline: Dict[str, Any], query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using LLM"""
        llm_component = self._find_component_by_type(active_pipeline, ComponentType.LLM)
        
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
                "sources": self._format_sources(context),
                "steps": [
                    "Query processed",
                    f"Retrieved {len(context)} relevant documents",
                    f"Generated response using {llm_component['config'].name}"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(query, context, llm_component)
    
    async def _generate_query_embedding(self, active_pipeline: Dict[str, Any], query: str) -> Optional[List[float]]:
        """Generate embedding for query using LLM"""
        llm_component = self._find_component_by_type(active_pipeline, ComponentType.LLM)
        
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
    
    def _find_component_by_type(self, active_pipeline: Dict[str, Any], component_type: ComponentType) -> Optional[Dict[str, Any]]:
        """Find component by type in active pipeline"""
        for comp_data in active_pipeline["components"].values():
            if comp_data["config"].type == component_type:
                return comp_data
        return None
    
    def _get_mock_context(self, query: str) -> List[Dict[str, Any]]:
        """Get mock context for fallback"""
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
    
    def _format_sources(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format context sources for response"""
        return [
            {
                "title": ctx.get("metadata", {}).get("source", ctx.get("source", f"Document {i+1}")),
                "content": ctx["content"][:200] + "..." if len(ctx["content"]) > 200 else ctx["content"],
                "score": ctx.get("score", 0.0)
            }
            for i, ctx in enumerate(context)
        ]
    
    def _get_fallback_response(self, query: str, context: List[Dict[str, Any]], llm_component: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback response when LLM fails"""
        return {
            "answer": f"Based on the provided context, here's the answer to '{query}': This is a fallback response due to an error in the LLM component.",
            "sources": self._format_sources(context),
            "steps": [
                "Query processed",
                f"Retrieved {len(context)} relevant documents",
                "Generated fallback response due to LLM error"
            ]
        }