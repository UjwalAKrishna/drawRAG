"""
Manager - Super simple interface to the framework
"""

import logging
from typing import Dict, Any, List, Optional, Union
from .framework import Framework
from .loader import Loader

logger = logging.getLogger(__name__)


class Manager:
    """Simple, powerful interface to the dynamic plugin framework"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.framework = Framework()
        self.loader = Loader(self.framework, plugins_dir)
        self.plugins_dir = plugins_dir
    
    async def start(self):
        """Start the framework and auto-discover all plugins"""
        await self.framework.start()
        
        # Auto-discover and load all plugins
        results = await self.loader.discover_and_load_all()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"Dynamic framework started: {success_count}/{total_count} plugins loaded")
        return results
    
    async def stop(self):
        """Stop the framework"""
        await self.framework.stop()
    
    # Super simple plugin interaction
    async def call(self, capability: str, *args, plugin_id: str = None, use_cache: bool = True, **kwargs) -> Any:
        """Call any capability with advanced options"""
        return await self.framework.call_capability(capability, *args, plugin_id=plugin_id, use_cache=use_cache, **kwargs)
    
    async def call_all(self, capability: str, *args, **kwargs) -> List[Any]:
        """Call capability on all plugins that provide it"""
        return await self.framework.call_multiple(capability, *args, **kwargs)
    
    async def emit(self, event: str, data: Any = None):
        """Emit event to all plugins"""
        await self.framework.emit_event(event, data)
    
    # Plugin management
    def list_plugins(self) -> List[str]:
        """List all loaded plugin IDs"""
        return list(self.framework.plugins.keys())
    
    def list_capabilities(self) -> Dict[str, List[str]]:
        """List all available capabilities"""
        return self.framework.list_capabilities()
    
    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed plugin information"""
        return self.framework.get_plugin_info(plugin_id)
    
    def discover_providers(self, capability: str) -> List[Dict[str, Any]]:
        """Find all plugins that provide a capability"""
        return self.framework.discover_capability_providers(capability)
    
    # Hot loading
    async def reload_plugin(self, plugin_id: str) -> bool:
        """Hot reload a specific plugin"""
        return await self.loader.reload_plugin(plugin_id)
    
    async def reload_all(self) -> Dict[str, bool]:
        """Reload all plugins"""
        await self.framework.stop()
        await self.framework.start()
        return await self.loader.discover_and_load_all()
    
    # Framework extensions and advanced features
    def add_middleware(self, middleware_func):
        """Add middleware to capability calls"""
        self.framework.add_middleware(middleware_func)
    
    def add_validator(self, validator_func):
        """Add plugin validator"""
        self.framework.add_validator(validator_func)
    
    def add_error_handler(self, error_type: str, handler_func):
        """Add error handler"""
        self.framework.add_error_handler(error_type, handler_func)
    
    def set_config(self, key: str, value: Any):
        """Set global configuration"""
        self.framework.set_config(key, value)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get global configuration"""
        return self.framework.get_config(key, default)
    
    def clear_cache(self):
        """Clear performance cache"""
        self.framework.clear_cache()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        return self.framework.get_metrics()
    
    def extend(self, extension_name: str, extension: Any):
        """Add extension to framework"""
        self.framework.extend_framework(extension_name, extension)
    
    def get_extension(self, extension_name: str) -> Any:
        """Get framework extension"""
        return self.framework.get_extension(extension_name)
    
    # Convenience methods for common patterns
    async def process_data(self, data: Any, processor: str = None) -> Any:
        """Process data through any available processor"""
        if processor:
            return await self.call(processor, data)
        
        # Try common processing capabilities
        for capability in ['process', 'transform', 'handle']:
            providers = self.discover_providers(capability)
            if providers:
                return await self.call(capability, data)
        
        raise ValueError("No data processors available")
    
    async def generate_text(self, prompt: str, model: str = None) -> str:
        """Generate text using any available LLM"""
        if model:
            return await self.call('generate_text', prompt, plugin_id=model)
        else:
            return await self.call('generate_text', prompt)
    
    async def store_vectors(self, documents: List[Dict], embeddings: List[List[float]], 
                          vectordb: str = None) -> bool:
        """Store vectors in any available vector database"""
        if vectordb:
            return await self.call('store_vectors', documents, embeddings, plugin_id=vectordb)
        else:
            return await self.call('store_vectors', documents, embeddings)
    
    async def search_vectors(self, query_vector: List[float], top_k: int = 5, 
                           vectordb: str = None) -> List[Dict]:
        """Search vectors in any available vector database"""
        if vectordb:
            return await self.call('query_vectors', query_vector, top_k, plugin_id=vectordb)
        else:
            return await self.call('query_vectors', query_vector, top_k)
    
    # Pipeline-like execution
    async def pipeline(self, data: Any, *capabilities: str) -> Any:
        """Execute capabilities in sequence like a pipeline"""
        current_data = data
        
        for capability in capabilities:
            current_data = await self.call(capability, current_data)
        
        return current_data
    
    # System info
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        framework_stats = self.framework.get_framework_stats()
        
        return {
            **framework_stats,
            "plugins_dir": self.plugins_dir,
            "available_capabilities": len(self.list_capabilities()),
            "plugin_details": {
                plugin_id: self.get_plugin_info(plugin_id) 
                for plugin_id in self.list_plugins()
            }
        }
    
    # Developer helpers
    def help(self, capability: str = None) -> str:
        """Get help about capabilities"""
        if capability:
            providers = self.discover_providers(capability)
            if not providers:
                return f"Capability '{capability}' not found"
            
            help_text = f"Capability: {capability}\n"
            help_text += f"Providers: {len(providers)}\n\n"
            
            for provider in providers:
                help_text += f"Plugin: {provider['plugin_id']}\n"
                if 'description' in provider['metadata']:
                    help_text += f"Description: {provider['metadata']['description']}\n"
                help_text += f"Parameters: {', '.join(provider['parameters'])}\n\n"
            
            return help_text
        else:
            capabilities = self.list_capabilities()
            help_text = f"Available capabilities ({len(capabilities)}):\n\n"
            
            for cap, providers in capabilities.items():
                help_text += f"• {cap} (provided by: {', '.join(providers)})\n"
            
            return help_text
    
    def debug_info(self) -> Dict[str, Any]:
        """Get debug information"""
        return {
            "framework_running": self.framework.running,
            "loaded_modules": list(self.loader.loaded_modules.keys()),
            "plugin_count": len(self.framework.plugins),
            "capability_count": len(self.framework.global_capabilities),
            "middleware_count": len(self.framework.middleware_stack),
            "extensions": list(self.framework.extensions.keys())
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        framework_stats = self.framework.get_framework_stats()
        
        return {
            "framework_running": self.framework.running,
            "plugins_dir": self.plugins_dir,
            "plugin_count": len(self.list_plugins()),
            "available_capabilities": len(self.list_capabilities()),
            "total_plugins": framework_stats.get("total_plugins", 0),
            "total_capabilities": framework_stats.get("total_capabilities", 0),
            "middleware_count": framework_stats.get("middleware_count", 0),
            "extensions": framework_stats.get("extensions", [])
        }