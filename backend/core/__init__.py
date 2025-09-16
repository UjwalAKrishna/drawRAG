"""
RAG Builder Core Framework
"""

# Core framework components
from .framework import Framework, Plugin
from .manager import Manager
from .loader import Loader
from .plugin_base import (
    BasePlugin, QuickPlugin, DataSourcePlugin, 
    VectorDBPlugin, LLMPlugin, create_plugin,
    capability, event_handler, requires, provides_schema
)

__all__ = [
    # Core framework
    "Framework",
    "Plugin", 
    "Manager",
    "Loader",
    
    # Plugin development
    "BasePlugin",
    "QuickPlugin", 
    "DataSourcePlugin",
    "VectorDBPlugin",
    "LLMPlugin",
    "create_plugin",
    
    # Decorators
    "capability",
    "event_handler", 
    "requires",
    "provides_schema"
]