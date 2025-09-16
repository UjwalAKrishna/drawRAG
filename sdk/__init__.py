"""
RAG Builder SDK - Plugin Development Kit
"""

# Import standardized framework classes
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import from core framework
from core import (
    Plugin, BasePlugin, QuickPlugin, 
    DataSourcePlugin, VectorDBPlugin, LLMPlugin,
    capability, event_handler, requires, provides_schema,
    create_plugin
)

# Legacy compatibility
BaseDataSourcePlugin = DataSourcePlugin
BaseVectorDBPlugin = VectorDBPlugin
BaseLLMPlugin = LLMPlugin

__version__ = "2.0.0"
__all__ = [
    # New standardized classes
    "Plugin",
    "BasePlugin",
    "QuickPlugin",
    "DataSourcePlugin", 
    "VectorDBPlugin",
    "LLMPlugin",
    
    # Decorators and utilities
    "capability",
    "event_handler",
    "requires", 
    "provides_schema",
    "create_plugin",
    
    # Legacy compatibility
    "BaseDataSourcePlugin",
    "BaseVectorDBPlugin", 
    "BaseLLMPlugin"
]