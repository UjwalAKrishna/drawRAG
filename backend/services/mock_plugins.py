"""
Mock Plugin Implementations - For development and fallback
"""

import logging
from typing import Dict, List, Any
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class MockDataSourcePlugin(BasePlugin):
    """Mock data source plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True
    
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def get_documents(self) -> List[Dict[str, Any]]:
        return [
            {"id": "1", "content": "Sample document 1", "metadata": {"source": "mock"}},
            {"id": "2", "content": "Sample document 2", "metadata": {"source": "mock"}}
        ]


class MockVectorDBPlugin(BasePlugin):
    """Mock vector database plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True
    
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        return True
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        return [
            {"id": "1", "content": "Similar document 1", "score": 0.95},
            {"id": "2", "content": "Similar document 2", "score": 0.87}
        ]


class MockLLMPlugin(BasePlugin):
    """Mock LLM plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True
    
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        return f"Mock response to: {prompt[:50]}..."
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Return mock embeddings
        import random
        return [[random.random() for _ in range(384)] for _ in texts]


# Specific mock implementations
class SQLiteDataSource(MockDataSourcePlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["database_path", "table_name", "text_column"]
        return all(field in config and config[field] for field in required_fields)


class FileUploadDataSource(MockDataSourcePlugin):
    async def process_files(self, files: List[Any]) -> List[Dict[str, Any]]:
        return [
            {"id": f"file_{i}", "content": f"Content from file {i}", "metadata": {"source": "upload"}}
            for i in range(len(files))
        ]


class PostgreSQLDataSource(MockDataSourcePlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["host", "database", "username", "password", "table_name", "text_column"]
        return all(field in config and config[field] for field in required_fields)


class ChromaVectorDB(MockVectorDBPlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "collection_name" in config and config["collection_name"]


class FAISSVectorDB(MockVectorDBPlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "dimension" in config and isinstance(config["dimension"], int)


class PineconeVectorDB(MockVectorDBPlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["api_key", "environment", "index_name"]
        return all(field in config and config[field] for field in required_fields)


class OpenAILLM(MockLLMPlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "api_key" in config and config["api_key"]
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        return f"Mock OpenAI response to: {prompt[:50]}..."


class OllamaLLM(MockLLMPlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "model" in config and config["model"]
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        return f"Mock Ollama response to: {prompt[:50]}..."


class AnthropicLLM(MockLLMPlugin):
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "api_key" in config and config["api_key"]
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        return f"Mock Anthropic response to: {prompt[:50]}..."


def get_mock_plugin_class(plugin_type: str, subtype: str):
    """Get mock plugin class by type and subtype"""
    mock_classes = {
        "datasource": {
            "sqlite": SQLiteDataSource,
            "upload": FileUploadDataSource,
            "postgres": PostgreSQLDataSource
        },
        "vectordb": {
            "chroma": ChromaVectorDB,
            "faiss": FAISSVectorDB,
            "pinecone": PineconeVectorDB
        },
        "llm": {
            "openai": OpenAILLM,
            "ollama": OllamaLLM,
            "anthropic": AnthropicLLM
        }
    }
    
    return mock_classes.get(plugin_type, {}).get(subtype, MockDataSourcePlugin)