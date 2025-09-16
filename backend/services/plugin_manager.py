"""
Plugin Manager - Handles loading and managing plugins
"""

import logging
from typing import Dict, List, Any, Optional

from models import ComponentType
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin loading, validation, and access"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.plugin_instances: Dict[str, Any] = {}
        self.plugin_loader = PluginLoader(plugins_dir)
        self.plugin_registry = PluginRegistry()
        
    async def load_plugins(self):
        """Load all plugins from the plugins directory"""
        # Load built-in plugins first
        builtin_plugins = self.plugin_registry.get_builtin_plugins()
        self.plugins.update(builtin_plugins)
        
        # Load external plugins
        external_plugins = await self.plugin_loader.load_external_plugins()
        self.plugins.update(external_plugins)
        
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
    
    def validate_plugin_config(self, plugin_type: str, subtype: str, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration against schema"""
        try:
            plugin = self.get_plugin(plugin_type, subtype)
            if not plugin:
                return False
            
            # Create temporary instance for validation
            temp_instance = plugin(config)
            return temp_instance.validate_config(config)
        except Exception as e:
            logger.error(f"Plugin validation failed: {str(e)}")
            return False
    
    async def install_plugin(self, plugin_path: str) -> bool:
        """Install a new plugin"""
        return await self.plugin_loader.install_plugin(plugin_path)
    
    async def uninstall_plugin(self, plugin_key: str) -> bool:
        """Uninstall a plugin"""
        if plugin_key in self.plugins:
            del self.plugins[plugin_key]
        return await self.plugin_loader.uninstall_plugin(plugin_key)
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        stats = {
            "total": len(self.plugins),
            "by_type": {}
        }
        
        for plugin_data in self.plugins.values():
            plugin_type = plugin_data["manifest"].type
            if plugin_type not in stats["by_type"]:
                stats["by_type"][plugin_type] = 0
            stats["by_type"][plugin_type] += 1
        
        return stats
    
    def list_plugin_capabilities(self) -> Dict[str, List[str]]:
        """List capabilities by plugin type"""
        capabilities = {}
        
        for plugin_key, plugin_data in self.plugins.items():
            plugin_type = plugin_data["manifest"].type
            plugin_name = plugin_data["manifest"].name
            
            if plugin_type not in capabilities:
                capabilities[plugin_type] = []
            
            capabilities[plugin_type].append({
                "name": plugin_name,
                "subtype": plugin_data.get("subtype", "default"),
                "version": plugin_data["manifest"].version
            })
        
        return capabilities
    
    async def enable_plugin(self, plugin_key: str) -> bool:
        """Enable a plugin"""
        if plugin_key in self.plugins:
            self.plugins[plugin_key]["enabled"] = True
            logger.info(f"Enabled plugin: {plugin_key}")
            return True
        return False
    
    async def disable_plugin(self, plugin_key: str) -> bool:
        """Disable a plugin"""
        if plugin_key in self.plugins:
            self.plugins[plugin_key]["enabled"] = False
            logger.info(f"Disabled plugin: {plugin_key}")
            return True
        return False
    
    def is_plugin_enabled(self, plugin_key: str) -> bool:
        """Check if a plugin is enabled"""
        if plugin_key in self.plugins:
            return self.plugins[plugin_key].get("enabled", True)
        return False
    
    async def reload_plugins(self):
        """Reload all plugins"""
        self.plugins.clear()
        self.plugin_instances.clear()
        await self.load_plugins()
        logger.info("Plugins reloaded successfully")