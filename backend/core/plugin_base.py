"""
Plugin Base - Super easy plugin development
"""

from .framework import Plugin
from typing import Dict, Any, List


class BasePlugin(Plugin):
    """Ultra-simple base class for plugin development"""
    
    def __init__(self, plugin_id: str = None, config: Dict[str, Any] = None):
        # Auto-generate plugin_id if not provided
        if not plugin_id:
            plugin_id = self.__class__.__name__.lower().replace('plugin', '')
        
        super().__init__(plugin_id, config)
        self._auto_register_methods()
    
    def _auto_register_methods(self):
        """Automatically register methods as capabilities"""
        for method_name in dir(self):
            if not method_name.startswith('_') and method_name not in ['initialize', 'cleanup']:
                method = getattr(self, method_name)
                if callable(method) and not method_name in ['provide', 'hook', 'execute_capability', 'trigger_hooks', 'get_capability_info']:
                    # Auto-register as capability
                    self.capabilities[method_name] = self._create_capability(method_name, method)
    
    def _create_capability(self, name: str, method):
        """Create capability from method"""
        from .framework import Capability
        
        # Extract metadata from docstring
        metadata = {}
        if hasattr(method, '__doc__') and method.__doc__:
            metadata['description'] = method.__doc__.strip()
        
        return Capability(name, method, metadata)


# Convenience decorators for super easy development
def capability(description: str = None, **metadata):
    """Decorator to mark a method as a capability with metadata"""
    def decorator(func):
        func._capability_metadata = metadata
        if description:
            func._capability_metadata['description'] = description
        return func
    return decorator


def event_handler(event_name: str):
    """Decorator to mark a method as an event handler"""
    def decorator(func):
        func._event_handler = event_name
        return func
    return decorator


def requires(*capabilities):
    """Decorator to specify that a capability requires other capabilities"""
    def decorator(func):
        func._requires = capabilities
        return func
    return decorator


def provides_schema(schema: Dict[str, Any]):
    """Decorator to specify input/output schema for a capability"""
    def decorator(func):
        func._schema = schema
        return func
    return decorator


class QuickPlugin(BasePlugin):
    """Even simpler - just inherit and define methods"""
    
    def __init__(self, plugin_id: str = None, config: dict = None):
        super().__init__(plugin_id, config or {})
    
    # Framework will auto-discover all public methods as capabilities


class DataSourcePlugin(BasePlugin):
    """Specialized base for data source plugins"""
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get documents from this data source"""
        raise NotImplementedError
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents with query"""
        # Default implementation
        return self.get_documents()


class VectorDBPlugin(BasePlugin):
    """Specialized base for vector database plugins"""
    
    def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store vectors in the database"""
        raise NotImplementedError
    
    def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors"""
        raise NotImplementedError


class LLMPlugin(BasePlugin):
    """Specialized base for LLM plugins"""
    
    def generate_text(self, prompt: str, **options) -> str:
        """Generate text from prompt"""
        raise NotImplementedError
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        # Optional - not all LLMs support this
        raise NotImplementedError("This LLM doesn't support embeddings")


# Factory function for super quick plugin creation
def create_plugin(plugin_id: str, capabilities: Dict[str, Any]) -> Plugin:
    """Create a plugin from a simple dictionary of capabilities"""
    
    class QuickCreatedPlugin(QuickPlugin):
        def __init__(self):
            super().__init__()
            self.plugin_id = plugin_id
    
    plugin = QuickCreatedPlugin()
    
    # Add capabilities
    for name, func in capabilities.items():
        if callable(func):
            plugin.capabilities[name] = plugin._create_capability(name, func)
    
    return plugin


# Example usage patterns:
"""
# Pattern 1: Minimal plugin
class MyPlugin(QuickPlugin):
    def process_data(self, data):
        return f"Processed: {data}"

# Pattern 2: With decorators
class MyAdvancedPlugin(BasePlugin):
    @capability("Processes documents")
    @provides_schema({"input": "text", "output": "dict"})
    def process_documents(self, text: str) -> dict:
        return {"processed": text, "word_count": len(text.split())}
    
    @event_handler("document_uploaded")
    def on_document_upload(self, event_data):
        print(f"Document uploaded: {event_data}")

# Pattern 3: Quick creation
my_plugin = create_plugin("math", {
    "add": lambda x, y: x + y,
    "multiply": lambda x, y: x * y
})
"""