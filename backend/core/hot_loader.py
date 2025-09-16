"""
Hot Plugin Loader - Dynamically load/unload plugins at runtime
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, Type, List
import logging
import asyncio
from .plugin_framework import PluginFramework, PluginInterface

logger = logging.getLogger(__name__)


class PluginManifest:
    """Plugin manifest data structure"""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "Unknown")
        self.plugin_type = data.get("type", "unknown")
        self.version = data.get("version", "1.0.0")
        self.entrypoint = data.get("entrypoint", "plugin.py")
        self.main_class = data.get("main_class", "Plugin")
        self.dependencies = data.get("dependencies", [])
        self.capabilities = data.get("capabilities", [])
        self.config_schema = data.get("config_schema", {})
        self.raw_data = data


class HotPluginLoader:
    """Dynamically load and unload plugins at runtime"""
    
    def __init__(self, plugin_framework: PluginFramework, plugins_dir: str = "plugins"):
        self.plugin_framework = plugin_framework
        self.plugins_dir = Path(plugins_dir)
        self.loaded_modules: Dict[str, Any] = {}
        self.plugin_paths: Dict[str, Path] = {}
        self.watchers: Dict[str, Any] = {}  # File watchers for auto-reload
    
    async def scan_and_load_plugins(self) -> Dict[str, bool]:
        """Scan plugins directory and load all valid plugins"""
        results = {}
        
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory: {self.plugins_dir}")
            return results
        
        # Scan for plugin directories (including nested ones)
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                # Check if this directory has a manifest directly
                if self._has_manifest(plugin_dir):
                    try:
                        success = await self.load_plugin_from_directory(plugin_dir)
                        results[plugin_dir.name] = success
                    except Exception as e:
                        logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
                        results[plugin_dir.name] = False
                else:
                    # Check subdirectories for plugins
                    for sub_dir in plugin_dir.iterdir():
                        if sub_dir.is_dir() and not sub_dir.name.startswith('.') and self._has_manifest(sub_dir):
                            try:
                                success = await self.load_plugin_from_directory(sub_dir)
                                plugin_key = f"{plugin_dir.name}_{sub_dir.name}"
                                results[plugin_key] = success
                            except Exception as e:
                                logger.error(f"Failed to load plugin from {sub_dir}: {e}")
                                results[f"{plugin_dir.name}_{sub_dir.name}"] = False
        
        return results
    
    async def load_plugin_from_directory(self, plugin_dir: Path) -> bool:
        """Load a plugin from a directory"""
        try:
            # Find and load manifest
            manifest = self._load_manifest(plugin_dir)
            if not manifest:
                logger.error(f"No valid manifest found in {plugin_dir}")
                return False
            
            # Load plugin module
            plugin_class = await self._load_plugin_module(plugin_dir, manifest)
            if not plugin_class:
                return False
            
            # Register plugin type with framework
            plugin_type_key = f"{manifest.plugin_type}_{plugin_dir.name}"
            self.plugin_framework.register_plugin_type(
                plugin_type_key, 
                plugin_class, 
                manifest.raw_data
            )
            
            # Track the plugin
            self.plugin_paths[plugin_type_key] = plugin_dir
            
            logger.info(f"Loaded plugin: {manifest.name} ({plugin_type_key})")
            return True
            
        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_dir}: {e}")
            return False
    
    def _has_manifest(self, plugin_dir: Path) -> bool:
        """Check if directory has a plugin manifest"""
        manifest_files = [
            plugin_dir / "plugin.yaml",
            plugin_dir / "plugin.yml", 
            plugin_dir / "plugin.json"
        ]
        return any(f.exists() for f in manifest_files)
    
    def _load_manifest(self, plugin_dir: Path) -> Optional[PluginManifest]:
        """Load plugin manifest from directory"""
        import json
        import yaml
        
        # Look for manifest files
        manifest_files = [
            plugin_dir / "plugin.yaml",
            plugin_dir / "plugin.yml", 
            plugin_dir / "plugin.json"
        ]
        
        for manifest_file in manifest_files:
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        if manifest_file.suffix in ['.yaml', '.yml']:
                            data = yaml.safe_load(f)
                        else:
                            data = json.load(f)
                    
                    return PluginManifest(data)
                    
                except Exception as e:
                    logger.error(f"Failed to parse manifest {manifest_file}: {e}")
        
        return None
    
    async def _load_plugin_module(self, plugin_dir: Path, manifest: PluginManifest) -> Optional[Type[PluginInterface]]:
        """Load plugin module and extract plugin class"""
        try:
            entrypoint_path = plugin_dir / manifest.entrypoint
            if not entrypoint_path.exists():
                logger.error(f"Entrypoint not found: {entrypoint_path}")
                return None
            
            # Create unique module name
            module_name = f"plugin_{plugin_dir.name}_{manifest.version.replace('.', '_')}"
            
            # Load module
            spec = importlib.util.spec_from_file_location(module_name, entrypoint_path)
            if not spec or not spec.loader:
                logger.error(f"Failed to create module spec for {entrypoint_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules for proper import resolution
            sys.modules[module_name] = module
            
            # Execute module
            spec.loader.exec_module(module)
            
            # Get plugin class
            plugin_class = getattr(module, manifest.main_class, None)
            if not plugin_class:
                logger.error(f"Plugin class '{manifest.main_class}' not found in {entrypoint_path}")
                return None
            
            # Validate plugin class
            if not self._validate_plugin_class(plugin_class):
                logger.error(f"Plugin class validation failed for {manifest.main_class}")
                return None
            
            # Store module reference for potential reloading
            self.loaded_modules[f"{plugin_dir.name}_{manifest.version}"] = module
            
            return plugin_class
            
        except Exception as e:
            logger.error(f"Failed to load plugin module: {e}")
            return None
    
    def _validate_plugin_class(self, plugin_class: Type) -> bool:
        """Validate that plugin class implements required interface"""
        required_methods = ['initialize', 'cleanup', 'get_capabilities']
        
        for method in required_methods:
            if not hasattr(plugin_class, method):
                logger.error(f"Plugin class missing required method: {method}")
                return False
        
        return True
    
    async def reload_plugin(self, plugin_type_key: str) -> bool:
        """Reload a plugin at runtime"""
        try:
            if plugin_type_key not in self.plugin_paths:
                logger.error(f"Plugin not found for reloading: {plugin_type_key}")
                return False
            
            plugin_dir = self.plugin_paths[plugin_type_key]
            
            # Unload existing instances (this would need more sophisticated handling)
            # For now, we'll just reload the module
            
            success = await self.load_plugin_from_directory(plugin_dir)
            if success:
                logger.info(f"Reloaded plugin: {plugin_type_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_type_key}: {e}")
            return False
    
    async def unload_plugin(self, plugin_type_key: str) -> bool:
        """Unload a plugin from the system"""
        try:
            # Remove from framework registry (this would need to be implemented)
            # For now, we'll clean up our tracking
            
            if plugin_type_key in self.plugin_paths:
                del self.plugin_paths[plugin_type_key]
            
            # Remove from loaded modules
            module_keys_to_remove = [k for k in self.loaded_modules.keys() if plugin_type_key in k]
            for key in module_keys_to_remove:
                module = self.loaded_modules[key]
                if hasattr(module, '__name__') and module.__name__ in sys.modules:
                    del sys.modules[module.__name__]
                del self.loaded_modules[key]
            
            logger.info(f"Unloaded plugin: {plugin_type_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_type_key}: {e}")
            return False
    
    async def install_plugin_package(self, package_path: str) -> bool:
        """Install a plugin package"""
        try:
            # This would handle plugin package installation
            # For now, it's a placeholder
            logger.info(f"Plugin package installation requested: {package_path}")
            
            # TODO: Implement package extraction, validation, and installation
            # 1. Extract package to temporary location
            # 2. Validate plugin structure and manifest
            # 3. Check dependencies
            # 4. Move to plugins directory
            # 5. Load plugin
            
            return True
            
        except Exception as e:
            logger.error(f"Plugin package installation failed: {e}")
            return False
    
    def list_available_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins in the plugins directory"""
        plugins = []
        
        if not self.plugins_dir.exists():
            return plugins
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                manifest = self._load_manifest(plugin_dir)
                if manifest:
                    plugins.append({
                        "directory": plugin_dir.name,
                        "name": manifest.name,
                        "type": manifest.plugin_type,
                        "version": manifest.version,
                        "capabilities": manifest.capabilities,
                        "loaded": plugin_dir.name in self.plugin_paths.values()
                    })
        
        return plugins
    
    def get_plugin_info(self, plugin_type_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin"""
        if plugin_type_key not in self.plugin_paths:
            return None
        
        plugin_dir = self.plugin_paths[plugin_type_key]
        manifest = self._load_manifest(plugin_dir)
        
        if manifest:
            return {
                "plugin_type_key": plugin_type_key,
                "directory": str(plugin_dir),
                "manifest": manifest.raw_data,
                "loaded": True
            }
        
        return None