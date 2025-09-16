"""
Base Plugin Classes - Core framework for all plugin types
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """Abstract base class for all plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
        self.created_at = datetime.now()
        
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin with current config"""
        pass
    
    async def cleanup(self):
        """Clean up plugin resources"""
        self.initialized = False
        logger.info(f"Cleaned up {self.__class__.__name__}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check plugin health status"""
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "initialized": self.initialized,
            "created_at": self.created_at.isoformat()
        }

class DataSourcePlugin(BasePlugin):
    """Base class for data source plugins"""
    
    @abstractmethod
    async def get_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve documents from the data source"""
        pass
    
    @abstractmethod
    async def get_document_count(self) -> int:
        """Get total number of documents"""
        pass
    
    async def test_connection(self) -> bool:
        """Test connection to data source"""
        try:
            count = await self.get_document_count()
            return count >= 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

class VectorDBPlugin(BasePlugin):
    """Base class for vector database plugins"""
    
    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection/index"""
        pass
    
    @abstractmethod
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store document vectors"""
        pass
    
    @abstractmethod
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors"""
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection/index"""
        pass
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        return {
            "vector_count": 0,
            "dimension": 0,
            "status": "unknown"
        }

class LLMPlugin(BasePlugin):
    """Base class for LLM plugins"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: str = "", **kwargs) -> str:
        """Generate response using the LLM"""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass
    
    async def test_generation(self) -> bool:
        """Test LLM generation capability"""
        try:
            response = await self.generate_response("Test prompt", max_tokens=10)
            return len(response) > 0
        except Exception as e:
            logger.error(f"Generation test failed: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "model": self.config.get("model", "unknown"),
            "provider": self.__class__.__name__,
            "capabilities": ["text_generation"]
        }

class EmbeddingPlugin(BasePlugin):
    """Base class for embedding model plugins"""
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass
    
    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query"""
        pass
    
    async def get_dimension(self) -> int:
        """Get embedding dimension"""
        try:
            test_embedding = await self.embed_query("test")
            return len(test_embedding)
        except Exception:
            return 0

# Plugin Factory for creating instances
class PluginFactory:
    """Factory for creating plugin instances"""
    
    @staticmethod
    async def create_plugin(plugin_class: type, config: Dict[str, Any]) -> BasePlugin:
        """Create and initialize a plugin instance"""
        try:
            # Validate config first
            temp_instance = plugin_class(config)
            is_valid = await temp_instance.validate_config(config)
            
            if not is_valid:
                raise ValueError(f"Invalid configuration for {plugin_class.__name__}")
            
            # Create actual instance
            instance = plugin_class(config)
            
            # Initialize the plugin
            success = await instance.initialize()
            if not success:
                raise RuntimeError(f"Failed to initialize {plugin_class.__name__}")
            
            logger.info(f"Successfully created plugin: {plugin_class.__name__}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create plugin {plugin_class.__name__}: {e}")
            raise

# Plugin Registry for managing plugin types
class PluginRegistry:
    """Registry for plugin types and their capabilities"""
    
    _registry = {
        "datasource": DataSourcePlugin,
        "vectordb": VectorDBPlugin,
        "llm": LLMPlugin,
        "embedding": EmbeddingPlugin
    }
    
    @classmethod
    def get_base_class(cls, plugin_type: str) -> type:
        """Get base class for plugin type"""
        return cls._registry.get(plugin_type, BasePlugin)
    
    @classmethod
    def register_type(cls, plugin_type: str, base_class: type):
        """Register a new plugin type"""
        cls._registry[plugin_type] = base_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported plugin types"""
        return list(cls._registry.keys())