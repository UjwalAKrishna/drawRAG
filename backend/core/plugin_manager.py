"""
Core Plugin Manager - Minimal core functionality for plugin management
"""

import logging
from typing import Dict, Any, List, Optional
from .plugin_framework import PluginFramework
from .pipeline_engine import PipelineEngine
from .hot_loader import HotPluginLoader

logger = logging.getLogger(__name__)


class CorePluginManager:
    """Core plugin manager - only framework essentials"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.framework = PluginFramework()
        self.pipeline_engine = PipelineEngine(self.framework)
        self.hot_loader = HotPluginLoader(self.framework, plugins_dir)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the core plugin system"""
        try:
            # Start framework
            await self.framework.start()
            
            # Load all available plugins
            results = await self.hot_loader.scan_and_load_plugins()
            
            self.initialized = True
            logger.info(f"Core plugin manager initialized. Loaded {len(results)} plugin types.")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to initialize core plugin manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the plugin system"""
        await self.framework.stop()
        self.initialized = False
        logger.info("Core plugin manager shutdown complete")
    
    # Plugin Management
    async def load_plugin_instance(self, plugin_type: str, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Load a plugin instance"""
        return await self.framework.load_plugin(plugin_type, plugin_id, config)
    
    async def unload_plugin_instance(self, plugin_id: str) -> bool:
        """Unload a plugin instance"""
        return await self.framework.unload_plugin(plugin_id)
    
    def get_plugin_instance(self, plugin_id: str):
        """Get plugin instance"""
        return self.framework.get_plugin(plugin_id)
    
    # Pipeline Management
    def create_pipeline(self, name: str = None) -> str:
        """Create a new pipeline"""
        return self.pipeline_engine.create_pipeline(name)
    
    def add_pipeline_node(self, pipeline_id: str, node_id: str, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Add node to pipeline"""
        return self.pipeline_engine.add_pipeline_node(pipeline_id, node_id, plugin_id, config)
    
    def connect_pipeline_nodes(self, pipeline_id: str, source: str, target: str) -> bool:
        """Connect pipeline nodes"""
        return self.pipeline_engine.connect_pipeline_nodes(pipeline_id, source, target)
    
    async def execute_pipeline(self, pipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pipeline"""
        return await self.pipeline_engine.execute_pipeline(pipeline_id, input_data)
    
    # Hot Loading
    async def install_plugin(self, package_path: str) -> bool:
        """Install a plugin package"""
        return await self.hot_loader.install_plugin_package(package_path)
    
    async def reload_plugin(self, plugin_type: str) -> bool:
        """Reload a plugin"""
        return await self.hot_loader.reload_plugin(plugin_type)
    
    # Information
    def list_plugin_types(self) -> List[str]:
        """List available plugin types"""
        return self.framework.registry.list_plugin_types()
    
    def list_plugin_instances(self) -> List[str]:
        """List active plugin instances"""
        return self.framework.registry.list_plugin_instances()
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines"""
        return self.pipeline_engine.list_pipelines()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "initialized": self.initialized,
            "framework_running": self.framework.running,
            "plugin_types": len(self.list_plugin_types()),
            "plugin_instances": len(self.list_plugin_instances()),
            "pipelines": len(self.list_pipelines())
        }