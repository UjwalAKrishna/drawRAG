"""
Plugin Manager - Handles loading and managing plugins
"""

import os
import json
import yaml
import importlib.util
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from models import PluginManifest, ComponentType
from .base_plugin import BasePlugin, PluginFactory, PluginRegistry

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin loading, validation, and access"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.plugin_instances: Dict[str, Any] = {}
        
    async def load_plugins(self):
        """Load all plugins from the plugins directory"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory: {self.plugins_dir}")
        
        # Load built-in plugins first
        await self._load_builtin_plugins()
        
        # Load external plugins
        await self._load_external_plugins()
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
    
    def get_available_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available plugins organized by type"""
        result = {}
        for plugin_key, plugin_data in self.plugins.items():
            plugin_type = plugin_data["manifest"].type
            if plugin_type not in result:
                result[plugin_type] = []
            
            result[plugin_type].append({
                "key": plugin_key,
                "name": plugin_data["manifest"].name,
                "version": plugin_data["manifest"].version,
                "description": plugin_data["manifest"].description,
                "subtype": plugin_data.get("subtype", "default")
            })
        
        return result
    
    def get_plugins_by_type(self, plugin_type: str) -> List[Dict[str, Any]]:
        """Get plugins of a specific type"""
        result = []
        for plugin_key, plugin_data in self.plugins.items():
            if plugin_data["manifest"].type == plugin_type:
                result.append({
                    "key": plugin_key,
                    "name": plugin_data["manifest"].name,
                    "version": plugin_data["manifest"].version,
                    "description": plugin_data["manifest"].description,
                    "subtype": plugin_data.get("subtype", "default"),
                    "config_schema": plugin_data["manifest"].config_schema
                })
        
        return result
    
    def get_plugin(self, plugin_type: str, subtype: str) -> Optional[Any]:
        """Get a specific plugin by type and subtype"""
        plugin_key = f"{plugin_type}_{subtype}"
        plugin_data = self.plugins.get(plugin_key)
        
        if plugin_data:
            return plugin_data.get("class")
        
        return None
    
    def get_component_schema(self, component_type: str, subtype: str) -> Dict[str, Any]:
        """Get configuration schema for a component"""
        plugin_key = f"{component_type}_{subtype}"
        plugin_data = self.plugins.get(plugin_key)
        
        if plugin_data:
            return plugin_data["manifest"].config_schema
        
        raise ValueError(f"Plugin not found: {component_type}:{subtype}")
    
    async def _load_builtin_plugins(self):
        """Load built-in plugins"""
        builtin_plugins = [
            # Data Source plugins
            {
                "key": "datasource_sqlite",
                "manifest": PluginManifest(
                    name="SQLite Database",
                    type=ComponentType.DATASOURCE,
                    version="1.0.0",
                    description="Connect to SQLite databases",
                    entrypoint="builtin",
                    config_schema={
                        "database_path": {"type": "string", "required": True, "description": "Path to SQLite database file"},
                        "table_name": {"type": "string", "required": True, "description": "Table name to query"},
                        "text_column": {"type": "string", "required": True, "description": "Column containing text data"}
                    }
                ),
                "subtype": "sqlite",
                "class": SQLiteDataSource
            },
            {
                "key": "datasource_upload",
                "manifest": PluginManifest(
                    name="File Upload",
                    type=ComponentType.DATASOURCE,
                    version="1.0.0",
                    description="Upload and process documents",
                    entrypoint="builtin",
                    config_schema={
                        "file_types": {"type": "array", "items": {"type": "string"}, "description": "Allowed file types"},
                        "max_size": {"type": "string", "description": "Maximum file size"}
                    }
                ),
                "subtype": "upload",
                "class": FileUploadDataSource
            },
            
            # Vector Database plugins
            {
                "key": "vectordb_chroma",
                "manifest": PluginManifest(
                    name="ChromaDB",
                    type=ComponentType.VECTORDB,
                    version="1.0.0",
                    description="ChromaDB vector database",
                    entrypoint="builtin",
                    config_schema={
                        "collection_name": {"type": "string", "required": True, "description": "Collection name"},
                        "persist_directory": {"type": "string", "description": "Directory to persist data"}
                    }
                ),
                "subtype": "chroma",
                "class": ChromaVectorDBPlugin if REAL_PLUGINS_AVAILABLE else ChromaVectorDB
            },
            {
                "key": "vectordb_faiss",
                "manifest": PluginManifest(
                    name="FAISS",
                    type=ComponentType.VECTORDB,
                    version="1.0.0",
                    description="Facebook AI Similarity Search",
                    entrypoint="builtin",
                    config_schema={
                        "index_type": {"type": "string", "enum": ["flat", "ivf"], "description": "FAISS index type"},
                        "dimension": {"type": "integer", "required": True, "description": "Vector dimension"}
                    }
                ),
                "subtype": "faiss",
                "class": FAISSVectorDBPlugin if REAL_PLUGINS_AVAILABLE else FAISSVectorDB
            },
            
            # LLM plugins
            {
                "key": "llm_openai",
                "manifest": PluginManifest(
                    name="OpenAI GPT",
                    type=ComponentType.LLM,
                    version="1.0.0",
                    description="OpenAI GPT models",
                    entrypoint="builtin",
                    config_schema={
                        "api_key": {"type": "string", "required": True, "description": "OpenAI API key"},
                        "model": {"type": "string", "enum": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], "description": "Model to use"},
                        "temperature": {"type": "number", "minimum": 0, "maximum": 2, "description": "Sampling temperature"},
                        "max_tokens": {"type": "integer", "minimum": 1, "description": "Maximum tokens to generate"}
                    }
                ),
                "subtype": "openai",
                "class": OpenAILLMPlugin if REAL_PLUGINS_AVAILABLE else OpenAILLM
            },
            {
                "key": "llm_ollama",
                "manifest": PluginManifest(
                    name="Ollama",
                    type=ComponentType.LLM,
                    version="1.0.0",
                    description="Local Ollama models",
                    entrypoint="builtin",
                    config_schema={
                        "base_url": {"type": "string", "description": "Ollama server URL"},
                        "model": {"type": "string", "required": True, "description": "Model name"},
                        "temperature": {"type": "number", "minimum": 0, "maximum": 2, "description": "Sampling temperature"}
                    }
                ),
                "subtype": "ollama",
                "class": OllamaLLMPlugin if REAL_PLUGINS_AVAILABLE else OllamaLLM
            },
            {
                "key": "llm_anthropic",
                "manifest": PluginManifest(
                    name="Anthropic Claude",
                    type=ComponentType.LLM,
                    version="1.0.0",
                    description="Anthropic Claude models",
                    entrypoint="builtin",
                    config_schema={
                        "api_key": {"type": "string", "required": True, "description": "Anthropic API key"},
                        "model": {"type": "string", "enum": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], "description": "Model to use"},
                        "temperature": {"type": "number", "minimum": 0, "maximum": 2, "description": "Sampling temperature"},
                        "max_tokens": {"type": "integer", "minimum": 1, "description": "Maximum tokens to generate"}
                    }
                ),
                "subtype": "anthropic",
                "class": AnthropicLLMPlugin if REAL_PLUGINS_AVAILABLE else AnthropicLLM
            },
            {
                "key": "datasource_postgres",
                "manifest": PluginManifest(
                    name="PostgreSQL",
                    type=ComponentType.DATASOURCE,
                    version="1.0.0",
                    description="Connect to PostgreSQL databases",
                    entrypoint="builtin",
                    config_schema={
                        "host": {"type": "string", "required": True, "description": "PostgreSQL host"},
                        "port": {"type": "integer", "required": True, "description": "PostgreSQL port"},
                        "database": {"type": "string", "required": True, "description": "Database name"},
                        "username": {"type": "string", "required": True, "description": "Username"},
                        "password": {"type": "string", "required": True, "description": "Password"},
                        "table_name": {"type": "string", "required": True, "description": "Table name to query"},
                        "text_column": {"type": "string", "required": True, "description": "Column containing text data"}
                    }
                ),
                "subtype": "postgres",
                "class": PostgreSQLDataSourcePlugin if REAL_PLUGINS_AVAILABLE else PostgreSQLDataSource
            },
            {
                "key": "vectordb_pinecone",
                "manifest": PluginManifest(
                    name="Pinecone",
                    type=ComponentType.VECTORDB,
                    version="1.0.0",
                    description="Pinecone cloud vector database",
                    entrypoint="builtin",
                    config_schema={
                        "api_key": {"type": "string", "required": True, "description": "Pinecone API key"},
                        "environment": {"type": "string", "required": True, "description": "Pinecone environment"},
                        "index_name": {"type": "string", "required": True, "description": "Index name"},
                        "dimension": {"type": "integer", "description": "Vector dimension"},
                        "metric": {"type": "string", "enum": ["cosine", "euclidean", "dotproduct"], "description": "Distance metric"}
                    }
                ),
                "subtype": "pinecone",
                "class": PineconeVectorDBPlugin if REAL_PLUGINS_AVAILABLE else PineconeVectorDB
            }
        ]
        
        for plugin in builtin_plugins:
            self.plugins[plugin["key"]] = plugin
            logger.info(f"Loaded built-in plugin: {plugin['manifest'].name}")
    
    async def _load_external_plugins(self):
        """Load external plugins from the plugins directory"""
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                await self._load_plugin_from_directory(plugin_dir)
    
    async def _load_plugin_from_directory(self, plugin_dir: Path):
        """Load a plugin from a directory"""
        try:
            # Look for plugin manifest
            manifest_file = None
            for filename in ["plugin.yaml", "plugin.yml", "plugin.json"]:
                manifest_path = plugin_dir / filename
                if manifest_path.exists():
                    manifest_file = manifest_path
                    break
            
            if not manifest_file:
                logger.warning(f"No manifest found in plugin directory: {plugin_dir}")
                return
            
            # Load manifest
            with open(manifest_file, 'r') as f:
                if manifest_file.suffix in ['.yaml', '.yml']:
                    manifest_data = yaml.safe_load(f)
                else:
                    manifest_data = json.load(f)
            
            manifest = PluginManifest(**manifest_data)
            
            # Load plugin module
            entrypoint_path = plugin_dir / manifest.entrypoint
            if not entrypoint_path.exists():
                logger.error(f"Entrypoint not found: {entrypoint_path}")
                return
            
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_dir.name}",
                entrypoint_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get plugin class (assume it's the main class in the module)
            plugin_class = getattr(module, 'Plugin', None)
            if not plugin_class:
                logger.error(f"No Plugin class found in {entrypoint_path}")
                return
            
            plugin_key = f"{manifest.type}_{plugin_dir.name}"
            self.plugins[plugin_key] = {
                "manifest": manifest,
                "class": plugin_class,
                "subtype": plugin_dir.name,
                "directory": plugin_dir
            }
            
            logger.info(f"Loaded external plugin: {manifest.name}")
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {str(e)}")


# Import real plugin implementations
try:
    import sys
    from pathlib import Path
    
    # Add plugins directory to Python path
    plugins_path = Path(__file__).parent.parent.parent / "plugins"
    if str(plugins_path) not in sys.path:
        sys.path.insert(0, str(plugins_path))
    
    from llm.openai_plugin import OpenAILLMPlugin
    from llm.ollama_plugin import OllamaLLMPlugin
    from llm.anthropic_plugin import AnthropicLLMPlugin
    from vectordb.chroma_plugin import ChromaVectorDBPlugin
    from vectordb.faiss_plugin import FAISSVectorDBPlugin
    from vectordb.pinecone_plugin import PineconeVectorDBPlugin
    from datasource.postgresql_plugin import PostgreSQLDataSourcePlugin
    REAL_PLUGINS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Real plugins not available, using mock implementations: {e}")
    REAL_PLUGINS_AVAILABLE = False

# Built-in Plugin Classes


class SQLiteDataSource(BasePlugin):
    """SQLite data source plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["database_path", "table_name", "text_column"]
        return all(field in config and config[field] for field in required_fields)
    
    async def get_documents(self) -> List[Dict[str, Any]]:
        """Get documents from SQLite database"""
        # Mock implementation
        return [
            {"id": "1", "content": "Sample document 1", "metadata": {"source": "sqlite"}},
            {"id": "2", "content": "Sample document 2", "metadata": {"source": "sqlite"}}
        ]


class FileUploadDataSource(BasePlugin):
    """File upload data source plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True  # Basic validation for MVP
    
    async def process_files(self, files: List[Any]) -> List[Dict[str, Any]]:
        """Process uploaded files"""
        # Mock implementation
        return [
            {"id": f"file_{i}", "content": f"Content from file {i}", "metadata": {"source": "upload"}}
            for i in range(len(files))
        ]


class ChromaVectorDB(BasePlugin):
    """ChromaDB vector database plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "collection_name" in config and config["collection_name"]
    
    async def store_vectors(self, documents: List[Dict[str, Any]]):
        """Store document vectors"""
        # Mock implementation
        pass
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors"""
        # Mock implementation
        return [
            {"id": "1", "content": "Similar document 1", "score": 0.95},
            {"id": "2", "content": "Similar document 2", "score": 0.87}
        ]


class FAISSVectorDB(BasePlugin):
    """FAISS vector database plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "dimension" in config and isinstance(config["dimension"], int)


class OpenAILLM(BasePlugin):
    """OpenAI LLM plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "api_key" in config and config["api_key"]
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using OpenAI"""
        # Mock implementation
        return f"Mock OpenAI response to: {prompt[:50]}..."


class OllamaLLM(BasePlugin):
    """Ollama LLM plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "model" in config and config["model"]
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Ollama"""
        # Mock implementation
        return f"Mock Ollama response to: {prompt[:50]}..."


class AnthropicLLM(BasePlugin):
    """Anthropic LLM plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return "api_key" in config and config["api_key"]
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Anthropic"""
        # Mock implementation
        return f"Mock Anthropic response to: {prompt[:50]}..."


class PostgreSQLDataSource(BasePlugin):
    """PostgreSQL data source plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["host", "database", "username", "password", "table_name", "text_column"]
        return all(field in config and config[field] for field in required_fields)


class PineconeVectorDB(BasePlugin):
    """Pinecone vector database plugin"""
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["api_key", "environment", "index_name"]
        return all(field in config and config[field] for field in required_fields)