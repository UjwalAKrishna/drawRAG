"""
Pydantic models for the RAG Builder API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

class ComponentType(str, Enum):
    DATASOURCE = "datasource"
    VECTORDB = "vectordb"
    LLM = "llm"

class ComponentStatus(str, Enum):
    UNCONFIGURED = "unconfigured"
    CONFIGURED = "configured"
    ERROR = "error"
    ACTIVE = "active"

class ComponentConfig(BaseModel):
    """Configuration for a pipeline component"""
    id: str
    type: ComponentType
    subtype: str
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    status: ComponentStatus = ComponentStatus.UNCONFIGURED
    position: Optional[Dict[str, float]] = None
    
    class Config:
        use_enum_values = True

class ConnectionConfig(BaseModel):
    """Configuration for connections between components"""
    from_component: str
    to_component: str
    connection_type: str = "default"

class PipelineConfig(BaseModel):
    """Complete pipeline configuration"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    components: List[ComponentConfig]
    connections: List[ConnectionConfig]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class QueryRequest(BaseModel):
    """Request model for querying the RAG pipeline"""
    query: str
    pipeline_id: Optional[str] = None
    pipeline_config: Optional[PipelineConfig] = None
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    pipeline_used: str
    processing_time: float
    timestamp: datetime

class PluginManifest(BaseModel):
    """Plugin manifest structure"""
    name: str
    type: ComponentType
    version: str
    description: Optional[str] = None
    entrypoint: str
    dependencies: List[str] = Field(default_factory=list)
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    author: Optional[str] = None
    
    class Config:
        use_enum_values = True

class DataSourceInfo(BaseModel):
    """Information about a data source"""
    id: str
    name: str
    type: str
    status: str
    document_count: int
    last_updated: Optional[datetime] = None

class VectorStoreInfo(BaseModel):
    """Information about a vector store"""
    id: str
    name: str
    type: str
    collection_name: str
    vector_count: int
    dimension: int

class LLMInfo(BaseModel):
    """Information about an LLM"""
    id: str
    name: str
    type: str
    model: str
    provider: str
    capabilities: List[str]

class SystemInfo(BaseModel):
    """System information response"""
    version: str
    plugins: Dict[str, Any]
    pipelines: Dict[str, Any]
    capabilities: Dict[str, bool]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime