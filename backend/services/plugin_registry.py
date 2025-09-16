"""
Plugin Registry - Manages built-in plugins and plugin definitions
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from models import PluginManifest, ComponentType
from .plugin_schemas import PluginSchemas

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for built-in plugins and plugin management"""
    
    def __init__(self):
        self.builtin_plugins = {}
        self._load_real_plugins()
    
    def _load_real_plugins(self):
        """Try to load real plugin implementations"""
        try:
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
            
            self.real_plugins_available = True
            self.real_plugins = {
                'openai': OpenAILLMPlugin,
                'ollama': OllamaLLMPlugin,
                'anthropic': AnthropicLLMPlugin,
                'chroma': ChromaVectorDBPlugin,
                'faiss': FAISSVectorDBPlugin,
                'pinecone': PineconeVectorDBPlugin,
                'postgres': PostgreSQLDataSourcePlugin
            }
            logger.info("Real plugins loaded successfully")
            
        except ImportError as e:
            logger.warning(f"Real plugins not available, using mock implementations: {e}")
            self.real_plugins_available = False
            self.real_plugins = {}
    
    def get_builtin_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get all built-in plugin definitions"""
        if self.builtin_plugins:
            return self.builtin_plugins
        
        self.builtin_plugins = {
            # Data Source plugins
            "datasource_sqlite": {
                "key": "datasource_sqlite",
                "manifest": PluginManifest(
                    name="SQLite Database",
                    type=ComponentType.DATASOURCE,
                    version="1.0.0",
                    description="Connect to SQLite databases",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_sqlite_schema()
                ),
                "subtype": "sqlite",
                "class": self._get_plugin_class("sqlite", "datasource")
            },
            "datasource_upload": {
                "key": "datasource_upload",
                "manifest": PluginManifest(
                    name="File Upload",
                    type=ComponentType.DATASOURCE,
                    version="1.0.0",
                    description="Upload and process documents",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_upload_schema()
                ),
                "subtype": "upload",
                "class": self._get_plugin_class("upload", "datasource")
            },
            "datasource_postgres": {
                "key": "datasource_postgres",
                "manifest": PluginManifest(
                    name="PostgreSQL",
                    type=ComponentType.DATASOURCE,
                    version="1.0.0",
                    description="Connect to PostgreSQL databases",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_postgres_schema()
                ),
                "subtype": "postgres",
                "class": self._get_plugin_class("postgres", "datasource")
            },
            
            # Vector Database plugins
            "vectordb_chroma": {
                "key": "vectordb_chroma",
                "manifest": PluginManifest(
                    name="ChromaDB",
                    type=ComponentType.VECTORDB,
                    version="1.0.0",
                    description="ChromaDB vector database",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_chroma_schema()
                ),
                "subtype": "chroma",
                "class": self._get_plugin_class("chroma", "vectordb")
            },
            "vectordb_faiss": {
                "key": "vectordb_faiss",
                "manifest": PluginManifest(
                    name="FAISS",
                    type=ComponentType.VECTORDB,
                    version="1.0.0",
                    description="Facebook AI Similarity Search",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_faiss_schema()
                ),
                "subtype": "faiss",
                "class": self._get_plugin_class("faiss", "vectordb")
            },
            "vectordb_pinecone": {
                "key": "vectordb_pinecone",
                "manifest": PluginManifest(
                    name="Pinecone",
                    type=ComponentType.VECTORDB,
                    version="1.0.0",
                    description="Pinecone cloud vector database",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_pinecone_schema()
                ),
                "subtype": "pinecone",
                "class": self._get_plugin_class("pinecone", "vectordb")
            },
            
            # LLM plugins
            "llm_openai": {
                "key": "llm_openai",
                "manifest": PluginManifest(
                    name="OpenAI GPT",
                    type=ComponentType.LLM,
                    version="1.0.0",
                    description="OpenAI GPT models",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_openai_schema()
                ),
                "subtype": "openai",
                "class": self._get_plugin_class("openai", "llm")
            },
            "llm_ollama": {
                "key": "llm_ollama",
                "manifest": PluginManifest(
                    name="Ollama",
                    type=ComponentType.LLM,
                    version="1.0.0",
                    description="Local Ollama models",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_ollama_schema()
                ),
                "subtype": "ollama",
                "class": self._get_plugin_class("ollama", "llm")
            },
            "llm_anthropic": {
                "key": "llm_anthropic",
                "manifest": PluginManifest(
                    name="Anthropic Claude",
                    type=ComponentType.LLM,
                    version="1.0.0",
                    description="Anthropic Claude models",
                    entrypoint="builtin",
                    config_schema=PluginSchemas.get_anthropic_schema()
                ),
                "subtype": "anthropic",
                "class": self._get_plugin_class("anthropic", "llm")
            }
        }
        
        return self.builtin_plugins
    
    def _get_plugin_class(self, subtype: str, plugin_type: str):
        """Get plugin class (real or mock)"""
        if self.real_plugins_available and subtype in self.real_plugins:
            return self.real_plugins[subtype]
        
        # Return mock implementation
        from .mock_plugins import get_mock_plugin_class
        return get_mock_plugin_class(plugin_type, subtype)