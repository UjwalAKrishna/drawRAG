"""
Plugin Loader - Handles loading and importing external plugins
"""

import os
import json
import yaml
import importlib.util
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from models import PluginManifest

logger = logging.getLogger(__name__)


class PluginLoader:
    """Handles external plugin loading and validation"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
    
    async def load_external_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Load all external plugins from directory"""
        plugins = {}
        
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory: {self.plugins_dir}")
            return plugins
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                plugin_data = await self._load_plugin_from_directory(plugin_dir)
                if plugin_data:
                    plugins[plugin_data["key"]] = plugin_data
        
        return plugins
    
    async def _load_plugin_from_directory(self, plugin_dir: Path) -> Optional[Dict[str, Any]]:
        """Load a plugin from a directory"""
        try:
            # Look for plugin manifest
            manifest_file = self._find_manifest_file(plugin_dir)
            if not manifest_file:
                logger.warning(f"No manifest found in plugin directory: {plugin_dir}")
                return None
            
            # Load manifest
            manifest = self._load_manifest(manifest_file)
            if not manifest:
                return None
            
            # Load plugin module
            plugin_class = await self._load_plugin_module(plugin_dir, manifest)
            if not plugin_class:
                return None
            
            plugin_key = f"{manifest.type}_{plugin_dir.name}"
            return {
                "key": plugin_key,
                "manifest": manifest,
                "class": plugin_class,
                "subtype": plugin_dir.name,
                "directory": plugin_dir
            }
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {str(e)}")
            return None
    
    def _find_manifest_file(self, plugin_dir: Path) -> Optional[Path]:
        """Find manifest file in plugin directory"""
        for filename in ["plugin.yaml", "plugin.yml", "plugin.json"]:
            manifest_path = plugin_dir / filename
            if manifest_path.exists():
                return manifest_path
        return None
    
    def _load_manifest(self, manifest_file: Path) -> Optional[PluginManifest]:
        """Load and parse manifest file"""
        try:
            with open(manifest_file, 'r') as f:
                if manifest_file.suffix in ['.yaml', '.yml']:
                    manifest_data = yaml.safe_load(f)
                else:
                    manifest_data = json.load(f)
            
            return PluginManifest(**manifest_data)
        except Exception as e:
            logger.error(f"Failed to load manifest {manifest_file}: {e}")
            return None
    
    async def _load_plugin_module(self, plugin_dir: Path, manifest: PluginManifest) -> Optional[Any]:
        """Load plugin module and extract plugin class"""
        try:
            entrypoint_path = plugin_dir / manifest.entrypoint
            if not entrypoint_path.exists():
                logger.error(f"Entrypoint not found: {entrypoint_path}")
                return None
            
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
                return None
            
            logger.info(f"Loaded external plugin: {manifest.name}")
            return plugin_class
            
        except Exception as e:
            logger.error(f"Failed to load plugin module: {e}")
            return None

    async def install_plugin(self, plugin_path: str) -> bool:
        """Install a new plugin from file or URL"""
        try:
            # For MVP, just log the installation attempt
            logger.info(f"Plugin installation requested: {plugin_path}")
            return True
        except Exception as e:
            logger.error(f"Plugin installation failed: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_key: str) -> bool:
        """Uninstall a plugin"""
        try:
            # For MVP, just log the uninstall attempt
            logger.info(f"Plugin uninstall requested: {plugin_key}")
            return True
        except Exception as e:
            logger.error(f"Plugin uninstall failed: {e}")
            return False