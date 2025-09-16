"""
FastAPI Backend for RAG Builder
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

from models import PipelineConfig, QueryRequest, QueryResponse, ComponentConfig
from services.pipeline_manager import PipelineManager
from services.plugin_manager import PluginManager

# Initialize FastAPI app
app = FastAPI(
    title="RAG Builder API",
    description="Backend API for the Plug-and-Play RAG Builder",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize managers
pipeline_manager = PipelineManager()
plugin_manager = PluginManager()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    await plugin_manager.load_plugins()
    print("🚀 RAG Builder API started successfully!")

@app.get("/")
async def root():
    """Root endpoint - redirect to frontend"""
    return {"message": "RAG Builder API", "version": "1.0.0", "frontend": "/static/index.html"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "plugins_loaded": len(plugin_manager.get_available_plugins())
    }

# Plugin Management Endpoints
@app.get("/api/plugins")
async def get_plugins():
    """Get all available plugins"""
    return {
        "plugins": plugin_manager.get_available_plugins(),
        "categories": {
            "datasource": plugin_manager.get_plugins_by_type("datasource"),
            "vectordb": plugin_manager.get_plugins_by_type("vectordb"),
            "llm": plugin_manager.get_plugins_by_type("llm")
        }
    }

@app.get("/api/plugins/{plugin_type}")
async def get_plugins_by_type(plugin_type: str):
    """Get plugins by type (datasource, vectordb, llm)"""
    plugins = plugin_manager.get_plugins_by_type(plugin_type)
    if not plugins:
        raise HTTPException(status_code=404, detail=f"No plugins found for type: {plugin_type}")
    return {"plugins": plugins}

# Pipeline Management Endpoints
@app.post("/api/pipeline/create")
async def create_pipeline(config: PipelineConfig):
    """Create a new RAG pipeline"""
    try:
        pipeline_id = await pipeline_manager.create_pipeline(config)
        return {
            "pipeline_id": pipeline_id,
            "status": "created",
            "message": "Pipeline created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pipeline/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """Get pipeline configuration"""
    pipeline = await pipeline_manager.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

@app.put("/api/pipeline/{pipeline_id}")
async def update_pipeline(pipeline_id: str, config: PipelineConfig):
    """Update pipeline configuration"""
    try:
        await pipeline_manager.update_pipeline(pipeline_id, config)
        return {"status": "updated", "message": "Pipeline updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/pipeline/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    """Delete a pipeline"""
    try:
        await pipeline_manager.delete_pipeline(pipeline_id)
        return {"status": "deleted", "message": "Pipeline deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pipelines")
async def list_pipelines():
    """List all pipelines"""
    pipelines = await pipeline_manager.list_pipelines()
    return {"pipelines": pipelines}

# Query Endpoints
@app.post("/api/query")
async def query_pipeline(request: QueryRequest):
    """Execute a query through the RAG pipeline"""
    try:
        response = await pipeline_manager.execute_query(
            pipeline_id=request.pipeline_id,
            query=request.query,
            options=request.options
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query/test")
async def test_query(request: QueryRequest):
    """Test a query with a temporary pipeline configuration"""
    try:
        # Create temporary pipeline for testing
        temp_pipeline_id = await pipeline_manager.create_temp_pipeline(request.pipeline_config)
        
        response = await pipeline_manager.execute_query(
            pipeline_id=temp_pipeline_id,
            query=request.query,
            options=request.options
        )
        
        # Clean up temporary pipeline
        await pipeline_manager.delete_pipeline(temp_pipeline_id)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Component Configuration Endpoints
@app.post("/api/component/validate")
async def validate_component_config(config: ComponentConfig):
    """Validate component configuration"""
    try:
        is_valid = await pipeline_manager.validate_component_config(config)
        return {
            "valid": is_valid,
            "message": "Configuration is valid" if is_valid else "Configuration is invalid"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e)
        }

@app.get("/api/component/{component_type}/schema")
async def get_component_schema(component_type: str, subtype: str):
    """Get configuration schema for a component type"""
    try:
        schema = plugin_manager.get_component_schema(component_type, subtype)
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# Data Management Endpoints
@app.post("/api/data/upload")
async def upload_data(file_data: Dict[str, Any]):
    """Upload and process data files"""
    try:
        result = await pipeline_manager.process_uploaded_data(file_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/data/upload/batch")
async def batch_upload_data(files_data: List[Dict[str, Any]]):
    """Batch upload and process multiple data files"""
    try:
        result = await pipeline_manager.process_uploaded_data(files_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/data/sources")
async def list_data_sources():
    """List available data sources"""
    sources = await pipeline_manager.list_data_sources()
    return {"sources": sources}

@app.get("/api/data/documents")
async def list_documents():
    """List processed documents"""
    documents = pipeline_manager.document_processor.list_documents()
    return {"documents": documents}

@app.get("/api/data/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get processed document by ID"""
    document = pipeline_manager.document_processor.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.delete("/api/data/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a processed document"""
    success = pipeline_manager.document_processor.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "message": "Document deleted successfully"}

@app.get("/api/data/stats")
async def get_document_stats():
    """Get document processing statistics"""
    stats = pipeline_manager.document_processor.get_document_stats()
    return {"stats": stats}

# System Information Endpoints
@app.get("/api/system/info")
async def get_system_info():
    """Get system information and capabilities"""
    return {
        "version": "1.0.0",
        "plugins": {
            "total": len(plugin_manager.get_available_plugins()),
            "by_type": {
                "datasource": len(plugin_manager.get_plugins_by_type("datasource")),
                "vectordb": len(plugin_manager.get_plugins_by_type("vectordb")),
                "llm": len(plugin_manager.get_plugins_by_type("llm"))
            }
        },
        "pipelines": {
            "active": len(await pipeline_manager.list_pipelines())
        },
        "capabilities": {
            "file_upload": True,
            "batch_processing": True,
            "database_connection": True,
            "custom_plugins": True,
            "real_time_query": True,
            "document_processing": True,
            "embedding_generation": True,
            "similarity_search": True
        }
    }

@app.get("/api/system/health")
async def get_system_health():
    """Get system health overview"""
    health = await pipeline_manager.get_system_health()
    return {"health": health}

@app.get("/api/system/stats")
async def get_system_stats():
    """Get comprehensive system statistics"""
    stats = await pipeline_manager.get_pipeline_stats()
    embedding_stats = pipeline_manager.embedding_manager.get_embedding_stats()
    return {
        "pipeline_stats": stats,
        "embedding_stats": embedding_stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)