"""
RAG Query API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from backend.api.dependencies import get_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/query")
async def execute_rag_query(request: Dict[str, Any]):
    """Execute a RAG query using the configured pipeline"""
    manager = get_manager()
    
    try:
        query = request.get("query")
        pipeline_config = request.get("pipeline_config", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Execute RAG pipeline
        # 1. Generate embeddings for query
        # 2. Search vector database
        # 3. Generate response with context
        
        result = {
            "query": query,
            "answer": "",
            "sources": [],
            "pipeline_used": pipeline_config,
            "execution_time": 0
        }
        
        # Try to find embedding capability
        embedding_providers = manager.discover_providers("generate_embeddings")
        if not embedding_providers:
            raise HTTPException(status_code=400, detail="No embedding providers available")
        
        # Generate query embedding
        query_embedding = await manager.call("generate_embeddings", [query])
        if query_embedding:
            query_vector = query_embedding[0]  # First embedding
        else:
            raise HTTPException(status_code=400, detail="Failed to generate query embedding")
        
        # Search vector database
        vector_providers = manager.discover_providers("query_vectors")
        if vector_providers:
            search_results = await manager.call("query_vectors", query_vector, top_k=5)
            result["sources"] = search_results
            
            # Build context from search results
            context = "\n".join([doc.get("content", "") for doc in search_results])
        else:
            context = ""
            result["sources"] = []
        
        # Generate response using LLM
        llm_providers = manager.discover_providers("generate_text")
        if not llm_providers:
            raise HTTPException(status_code=400, detail="No LLM providers available")
        
        # Build RAG prompt
        if context:
            prompt = f"""Context:
{context}

Question: {query}

Please answer the question based on the provided context."""
        else:
            prompt = f"Question: {query}\n\nPlease answer this question."
        
        answer = await manager.call("generate_text", prompt)
        result["answer"] = answer
        
        return result
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def index_documents(request: Dict[str, Any]):
    """Index documents into the vector database"""
    manager = get_manager()
    
    try:
        documents = request.get("documents", [])
        vectordb_plugin = request.get("vectordb_plugin")
        embedding_plugin = request.get("embedding_plugin")
        
        if not documents:
            raise HTTPException(status_code=400, detail="Documents are required")
        
        # Extract text content from documents
        texts = []
        for doc in documents:
            if isinstance(doc, str):
                texts.append(doc)
            elif isinstance(doc, dict):
                texts.append(doc.get("content", ""))
            else:
                texts.append(str(doc))
        
        # Generate embeddings
        if embedding_plugin:
            embeddings = await manager.call("generate_embeddings", texts, plugin_id=embedding_plugin)
        else:
            embeddings = await manager.call("generate_embeddings", texts)
        
        # Store in vector database
        if vectordb_plugin:
            success = await manager.call("store_vectors", documents, embeddings, plugin_id=vectordb_plugin)
        else:
            success = await manager.call("store_vectors", documents, embeddings)
        
        return {
            "success": success,
            "indexed_count": len(documents),
            "message": f"Successfully indexed {len(documents)} documents"
        }
        
    except Exception as e:
        logger.error(f"Document indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_rag_status():
    """Get RAG system status"""
    manager = get_manager()
    
    # Check available components
    embedding_providers = manager.discover_providers("generate_embeddings")
    vector_providers = manager.discover_providers("query_vectors")
    llm_providers = manager.discover_providers("generate_text")
    
    return {
        "ready": bool(embedding_providers and vector_providers and llm_providers),
        "components": {
            "embedding_providers": len(embedding_providers),
            "vector_providers": len(vector_providers),
            "llm_providers": len(llm_providers)
        },
        "providers": {
            "embeddings": [p["plugin_id"] for p in embedding_providers],
            "vector_db": [p["plugin_id"] for p in vector_providers],
            "llm": [p["plugin_id"] for p in llm_providers]
        }
    }