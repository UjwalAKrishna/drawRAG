"""
Loader - Loads plugins with zero configuration
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
import logging
import yaml
import json
import inspect

from .framework import Framework, Plugin
from .plugin_base import BasePlugin, QuickPlugin

logger = logging.getLogger(__name__)


class Loader:
    """Loads plugins with maximum flexibility and minimum configuration"""
    
    def __init__(self, framework: Framework, plugins_dir: str = "plugins"):
        self.framework = framework
        self.plugins_dir = Path(plugins_dir)
        self.loaded_modules = {}
    
    async def discover_and_load_all(self) -> Dict[str, bool]:
        """Discover and load all plugins with zero configuration needed"""
        results = {}
        
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory: {self.plugins_dir}")
            return results
        
        # Scan for any Python files or directories
        for item in self.plugins_dir.rglob("*"):
            if self._is_plugin_candidate(item):
                try:
                    plugin_id = self._generate_plugin_id(item)
                    plugin = await self._load_plugin_from_path(item, plugin_id)
                    
                    if plugin:
                        success = await self.framework.load_plugin(plugin)
                        results[plugin_id] = success
                        if success:
                            logger.info(f"✅ Loaded plugin: {plugin_id}")
                        else:
                            logger.warning(f"⚠️ Failed to initialize: {plugin_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Error loading {item}: {e}")
                    results[str(item)] = False
        
        return results
    
    def _is_plugin_candidate(self, path: Path) -> bool:
        """Check if path could be a plugin"""
        if path.is_file():
            # Python files that aren't __init__.py or start with _
            return (path.suffix == '.py' and 
                   path.name != '__init__.py' and 
                   not path.name.startswith('_'))
        elif path.is_dir():
            # Directories with Python files or manifests
            return (not path.name.startswith('.') and 
                   not path.name.startswith('_') and
                   (list(path.glob('*.py')) or list(path.glob('plugin.*'))))
        return False
    
    def _generate_plugin_id(self, path: Path) -> str:
        """Generate a unique plugin ID from path"""
        if path.is_file():
            # For files: parent_filename
            parent = path.parent.name if path.parent.name != 'plugins' else ''
            name = path.stem
            return f"{parent}_{name}" if parent else name
        else:
            # For directories: full_path_as_id
            relative = path.relative_to(self.plugins_dir)
            return str(relative).replace('/', '_').replace('\\', '_')
    
    async def _load_plugin_from_path(self, path: Path, plugin_id: str) -> Optional[Plugin]:
        """Load plugin from file or directory with automatic detection"""
        
        if path.is_file():
            return await self._load_from_file(path, plugin_id)
        elif path.is_dir():
            return await self._load_from_directory(path, plugin_id)
        
        return None
    
    async def _load_from_file(self, file_path: Path, plugin_id: str) -> Optional[Plugin]:
        """Load plugin directly from Python file"""
        try:
            # Load the module
            module = await self._import_module(file_path, plugin_id)
            if not module:
                return None
            
            # Try different discovery methods
            plugin = (self._find_plugin_class(module, plugin_id) or
                     self._find_plugin_function(module, plugin_id) or
                     self._create_from_module_functions(module, plugin_id))
            
            return plugin
            
        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {e}")
            return None
    
    async def _load_from_directory(self, dir_path: Path, plugin_id: str) -> Optional[Plugin]:
        """Load plugin from directory with optional manifest"""
        try:
            # Check for manifest first
            manifest = self._load_manifest(dir_path)
            
            if manifest:
                return await self._load_with_manifest(dir_path, plugin_id, manifest)
            else:
                return await self._load_without_manifest(dir_path, plugin_id)
                
        except Exception as e:
            logger.error(f"Error loading plugin from {dir_path}: {e}")
            return None
    
    def _load_manifest(self, dir_path: Path) -> Optional[Dict[str, Any]]:
        """Load plugin manifest if it exists"""
        for manifest_file in ['plugin.yaml', 'plugin.yml', 'plugin.json']:
            manifest_path = dir_path / manifest_file
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        if manifest_file.endswith('.json'):
                            return json.load(f)
                        else:
                            return yaml.safe_load(f)
                except Exception as e:
                    logger.warning(f"Failed to load manifest {manifest_path}: {e}")
        return None
    
    async def _load_with_manifest(self, dir_path: Path, plugin_id: str, manifest: Dict[str, Any]) -> Optional[Plugin]:
        """Load plugin using manifest configuration"""
        entrypoint = manifest.get('entrypoint', 'plugin.py')
        main_class = manifest.get('main_class', 'Plugin')
        
        entrypoint_path = dir_path / entrypoint
        if not entrypoint_path.exists():
            logger.error(f"Entrypoint {entrypoint} not found in {dir_path}")
            return None
        
        module = await self._import_module(entrypoint_path, plugin_id)
        if not module:
            return None
        
        # Get the specified class
        plugin_class = getattr(module, main_class, None)
        if not plugin_class:
            logger.error(f"Class {main_class} not found in {entrypoint_path}")
            return None
        
        # Create plugin instance
        config = manifest.get('config', {})
        
        # Handle different plugin base classes
        if issubclass(plugin_class, Plugin):
            return plugin_class(plugin_id, config)
        else:
            # Wrap regular class in Plugin
            return self._wrap_class_as_plugin(plugin_class, plugin_id, config)
    
    async def _load_without_manifest(self, dir_path: Path, plugin_id: str) -> Optional[Plugin]:
        """Load plugin without manifest - auto-discover"""
        # Look for common entry points
        for entry_file in ['plugin.py', 'main.py', f'{dir_path.name}.py']:
            entry_path = dir_path / entry_file
            if entry_path.exists():
                return await self._load_from_file(entry_path, plugin_id)
        
        # If no obvious entry point, try to load all Python files
        python_files = list(dir_path.glob('*.py'))
        if python_files:
            return await self._load_from_file(python_files[0], plugin_id)
        
        return None
    
    async def _import_module(self, file_path: Path, module_name: str):
        """Import Python module from file"""
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            self.loaded_modules[module_name] = module
            return module
            
        except Exception as e:
            logger.error(f"Failed to import {file_path}: {e}")
            return None
    
    def _find_plugin_class(self, module, plugin_id: str) -> Optional[Plugin]:
        """Find plugin class in module"""
        # Look for classes that inherit from Plugin or BasePlugin
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (obj.__module__ == module.__name__ and 
                issubclass(obj, Plugin) and 
                obj != Plugin):
                
                try:
                    return obj(plugin_id)
                except Exception as e:
                    logger.error(f"Error instantiating {name}: {e}")
        
        return None
    
    def _find_plugin_function(self, module, plugin_id: str) -> Optional[Plugin]:
        """Find plugin factory function"""
        # Look for functions named create_plugin, plugin, etc.
        for func_name in ['create_plugin', 'plugin', 'main', 'get_plugin']:
            func = getattr(module, func_name, None)
            if callable(func):
                try:
                    result = func()
                    if isinstance(result, Plugin):
                        result.plugin_id = plugin_id
                        return result
                except Exception as e:
                    logger.error(f"Error calling {func_name}: {e}")
        
        return None
    
    def _create_from_module_functions(self, module, plugin_id: str) -> Optional[Plugin]:
        """Create plugin from module functions automatically"""
        # Find all public functions in the module
        functions = {}
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if (obj.__module__ == module.__name__ and 
                not name.startswith('_')):
                functions[name] = obj
        
        if not functions:
            return None
        
        # Create a QuickPlugin with these functions
        class AutoGeneratedPlugin(QuickPlugin):
            def __init__(self):
                super().__init__()
                self.plugin_id = plugin_id
                
                # Add all functions as capabilities
                for func_name, func in functions.items():
                    setattr(self, func_name, func)
                    self.capabilities[func_name] = self._create_capability(func_name, func)
        
        return AutoGeneratedPlugin()
    
    def _wrap_class_as_plugin(self, cls: Type, plugin_id: str, config: Dict[str, Any]) -> Plugin:
        """Wrap a regular class as a DynamicPlugin"""
        
        class WrappedPlugin(Plugin):
            def __init__(self):
                super().__init__(plugin_id, config)
                self.wrapped_instance = cls(**config) if config else cls()
                
                # Auto-register public methods as capabilities
                for method_name in dir(self.wrapped_instance):
                    if (not method_name.startswith('_') and 
                        callable(getattr(self.wrapped_instance, method_name))):
                        method = getattr(self.wrapped_instance, method_name)
                        self.capabilities[method_name] = self._create_capability_from_method(method_name, method)
            
            def _create_capability_from_method(self, name: str, method):
                from .framework import Capability
                metadata = {}
                if hasattr(method, '__doc__') and method.__doc__:
                    metadata['description'] = method.__doc__.strip()
                return Capability(name, method, metadata)
            
            async def initialize(self) -> bool:
                # Call initialize on wrapped instance if it exists
                if hasattr(self.wrapped_instance, 'initialize'):
                    if asyncio.iscoroutinefunction(self.wrapped_instance.initialize):
                        return await self.wrapped_instance.initialize()
                    else:
                        return self.wrapped_instance.initialize()
                return True
            
            async def cleanup(self):
                if hasattr(self.wrapped_instance, 'cleanup'):
                    if asyncio.iscoroutinefunction(self.wrapped_instance.cleanup):
                        await self.wrapped_instance.cleanup()
                    else:
                        self.wrapped_instance.cleanup()
                await super().cleanup()
        
        return WrappedPlugin()
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """Hot reload a plugin"""
        try:
            # Unload existing plugin
            await self.framework.unload_plugin(plugin_id)
            
            # Remove from module cache
            module_name = plugin_id
            if module_name in sys.modules:
                del sys.modules[module_name]
            if module_name in self.loaded_modules:
                del self.loaded_modules[module_name]
            
            # Reload
            results = await self.discover_and_load_all()
            return results.get(plugin_id, False)
            
        except Exception as e:
            logger.error(f"Error reloading plugin {plugin_id}: {e}")
            return False