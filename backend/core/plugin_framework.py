"""
Core Plugin Framework - The heart of the plugin system
"""

import logging
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class PluginInterface(ABC):
    """Core plugin interface that all plugins must implement"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
        self.plugin_id = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get plugin capabilities"""
        pass
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin metadata"""
        return {
            "id": self.plugin_id,
            "initialized": self.initialized,
            "capabilities": self.get_capabilities()
        }


class PluginRegistry:
    """Core plugin registry for managing plugin types and instances"""
    
    def __init__(self):
        self.plugin_types: Dict[str, Type[PluginInterface]] = {}
        self.plugin_instances: Dict[str, PluginInterface] = {}
        self.plugin_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_plugin_type(self, plugin_type: str, plugin_class: Type[PluginInterface], 
                           metadata: Dict[str, Any]):
        """Register a new plugin type"""
        self.plugin_types[plugin_type] = plugin_class
        self.plugin_metadata[plugin_type] = metadata
        logger.info(f"Registered plugin type: {plugin_type}")
    
    def create_plugin_instance(self, plugin_type: str, plugin_id: str, 
                             config: Dict[str, Any]) -> Optional[PluginInterface]:
        """Create a plugin instance"""
        if plugin_type not in self.plugin_types:
            logger.error(f"Unknown plugin type: {plugin_type}")
            return None
        
        try:
            plugin_class = self.plugin_types[plugin_type]
            instance = plugin_class(config)
            instance.plugin_id = plugin_id
            self.plugin_instances[plugin_id] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create plugin instance {plugin_id}: {e}")
            return None
    
    def get_plugin_instance(self, plugin_id: str) -> Optional[PluginInterface]:
        """Get plugin instance by ID"""
        return self.plugin_instances.get(plugin_id)
    
    def remove_plugin_instance(self, plugin_id: str) -> bool:
        """Remove plugin instance"""
        if plugin_id in self.plugin_instances:
            del self.plugin_instances[plugin_id]
            return True
        return False
    
    def list_plugin_types(self) -> List[str]:
        """List all registered plugin types"""
        return list(self.plugin_types.keys())
    
    def list_plugin_instances(self) -> List[str]:
        """List all plugin instances"""
        return list(self.plugin_instances.keys())


class PluginFramework:
    """Core framework for plugin management"""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self.event_bus = EventBus()
        self.running = False
    
    async def start(self):
        """Start the plugin framework"""
        self.running = True
        await self.event_bus.start()
        logger.info("Plugin framework started")
    
    async def stop(self):
        """Stop the plugin framework"""
        self.running = False
        
        # Cleanup all plugin instances
        for plugin_id in list(self.registry.plugin_instances.keys()):
            await self.cleanup_plugin(plugin_id)
        
        await self.event_bus.stop()
        logger.info("Plugin framework stopped")
    
    def register_plugin_type(self, plugin_type: str, plugin_class: Type[PluginInterface], 
                           metadata: Dict[str, Any] = None):
        """Register a plugin type with the framework"""
        metadata = metadata or {}
        self.registry.register_plugin_type(plugin_type, plugin_class, metadata)
        
        # Emit event
        self.event_bus.emit("plugin_type_registered", {
            "plugin_type": plugin_type,
            "metadata": metadata
        })
    
    async def load_plugin(self, plugin_type: str, plugin_id: str, 
                         config: Dict[str, Any]) -> bool:
        """Load and initialize a plugin"""
        try:
            # Create instance
            instance = self.registry.create_plugin_instance(plugin_type, plugin_id, config)
            if not instance:
                return False
            
            # Initialize
            success = await instance.initialize()
            if success:
                self.event_bus.emit("plugin_loaded", {
                    "plugin_id": plugin_id,
                    "plugin_type": plugin_type
                })
                logger.info(f"Plugin loaded: {plugin_id}")
            else:
                self.registry.remove_plugin_instance(plugin_id)
                logger.error(f"Plugin initialization failed: {plugin_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        try:
            instance = self.registry.get_plugin_instance(plugin_id)
            if instance:
                await instance.cleanup()
            
            removed = self.registry.remove_plugin_instance(plugin_id)
            if removed:
                self.event_bus.emit("plugin_unloaded", {"plugin_id": plugin_id})
                logger.info(f"Plugin unloaded: {plugin_id}")
            
            return removed
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    async def cleanup_plugin(self, plugin_id: str):
        """Cleanup plugin resources"""
        instance = self.registry.get_plugin_instance(plugin_id)
        if instance:
            try:
                await instance.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_id}: {e}")
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """Get plugin instance"""
        return self.registry.get_plugin_instance(plugin_id)
    
    def list_plugins(self) -> Dict[str, Any]:
        """List all plugins and their status"""
        return {
            "plugin_types": self.registry.list_plugin_types(),
            "plugin_instances": [
                self.registry.get_plugin_instance(pid).get_plugin_info()
                for pid in self.registry.list_plugin_instances()
            ]
        }


class EventBus:
    """Simple event bus for plugin communication"""
    
    def __init__(self):
        self.listeners: Dict[str, List[callable]] = {}
        self.running = False
    
    async def start(self):
        """Start event bus"""
        self.running = True
    
    async def stop(self):
        """Stop event bus"""
        self.running = False
        self.listeners.clear()
    
    def on(self, event_name: str, callback: callable):
        """Register event listener"""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
    
    def off(self, event_name: str, callback: callable):
        """Remove event listener"""
        if event_name in self.listeners:
            self.listeners[event_name].remove(callback)
    
    def emit(self, event_name: str, data: Any = None):
        """Emit event to listeners"""
        if not self.running:
            return
        
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(data))
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_name}: {e}")