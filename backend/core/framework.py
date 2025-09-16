"""
Core Plugin Framework - Zero hardcoded concepts, maximum flexibility
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from abc import ABC, abstractmethod
import inspect
from datetime import datetime

logger = logging.getLogger(__name__)


class Capability:
    """Represents a capability that a plugin can provide"""
    
    def __init__(self, name: str, handler: Callable, metadata: Dict[str, Any] = None):
        self.name = name
        self.handler = handler
        self.metadata = metadata or {}
        self.signature = inspect.signature(handler)
    
    async def execute(self, *args, **kwargs):
        """Execute the capability"""
        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(*args, **kwargs)
        else:
            return self.handler(*args, **kwargs)


class Plugin:
    """Base plugin class - minimal and flexible"""
    
    def __init__(self, plugin_id: str, config: Dict[str, Any] = None):
        self.plugin_id = plugin_id
        self.config = config or {}
        self.capabilities: Dict[str, Capability] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.state = {}
        self.initialized = False
    
    def provide(self, capability_name: str, metadata: Dict[str, Any] = None):
        """Decorator to register a capability"""
        def decorator(func):
            self.capabilities[capability_name] = Capability(capability_name, func, metadata)
            return func
        return decorator
    
    def hook(self, event_name: str):
        """Decorator to register event hooks"""
        def decorator(func):
            if event_name not in self.hooks:
                self.hooks[event_name] = []
            self.hooks[event_name].append(func)
            return func
        return decorator
    
    async def execute_capability(self, capability_name: str, *args, **kwargs):
        """Execute a capability by name"""
        if capability_name not in self.capabilities:
            raise ValueError(f"Capability '{capability_name}' not found in plugin {self.plugin_id}")
        
        capability = self.capabilities[capability_name]
        return await capability.execute(*args, **kwargs)
    
    async def trigger_hooks(self, event_name: str, data: Any = None):
        """Trigger all hooks for an event"""
        if event_name in self.hooks:
            for hook in self.hooks[event_name]:
                try:
                    if asyncio.iscoroutinefunction(hook):
                        await hook(data)
                    else:
                        hook(data)
                except Exception as e:
                    logger.error(f"Hook error in {self.plugin_id}: {e}")
    
    def get_capability_info(self) -> Dict[str, Any]:
        """Get information about plugin capabilities"""
        return {
            name: {
                "metadata": cap.metadata,
                "parameters": [p.name for p in cap.signature.parameters.values()]
            }
            for name, cap in self.capabilities.items()
        }
    
    async def initialize(self) -> bool:
        """Initialize the plugin - override in subclass"""
        self.initialized = True
        return True
    
    async def cleanup(self):
        """Cleanup the plugin - override in subclass"""
        self.initialized = False


class Framework:
    """Core framework - completely dynamic and flexible"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.global_capabilities: Dict[str, List[str]] = {}  # capability_name -> plugin_ids
        self.event_bus = {}
        self.middleware_stack: List[Callable] = []
        self.running = False
        self.extensions: Dict[str, Any] = {}  # For framework extensions
        
        # Advanced features
        self.plugin_dependencies: Dict[str, List[str]] = {}  # plugin_id -> dependencies
        self.capability_cache: Dict[str, Any] = {}  # Performance caching
        self.error_handlers: Dict[str, Callable] = {}  # Error recovery
        self.metrics: Dict[str, Any] = {"calls": 0, "errors": 0, "cache_hits": 0}
        self.validators: List[Callable] = []  # Plugin validators
        self.config_store: Dict[str, Any] = {}  # Global configuration
    
    async def start(self):
        """Start the dynamic framework"""
        self.running = True
        await self.emit_event("framework_started", {"timestamp": datetime.now()})
        logger.info("Dynamic framework started")
    
    async def stop(self):
        """Stop the framework"""
        # Cleanup all plugins
        for plugin in list(self.plugins.values()):
            await self.unload_plugin(plugin.plugin_id)
        
        self.running = False
        await self.emit_event("framework_stopped", {"timestamp": datetime.now()})
        logger.info("Dynamic framework stopped")
    
    def register_plugin(self, plugin: Plugin):
        """Register a plugin with the framework"""
        if plugin.plugin_id in self.plugins:
            raise ValueError(f"Plugin {plugin.plugin_id} already registered")
        
        self.plugins[plugin.plugin_id] = plugin
        
        # Index capabilities
        for capability_name in plugin.capabilities:
            if capability_name not in self.global_capabilities:
                self.global_capabilities[capability_name] = []
            self.global_capabilities[capability_name].append(plugin.plugin_id)
        
        logger.info(f"Registered plugin: {plugin.plugin_id}")
    
    async def load_plugin(self, plugin: Plugin) -> bool:
        """Load and initialize a plugin with validation and dependency resolution"""
        try:
            # Validate plugin
            if not await self._validate_plugin(plugin):
                logger.error(f"Plugin validation failed: {plugin.plugin_id}")
                return False
            
            # Check and resolve dependencies
            if not await self._resolve_dependencies(plugin):
                logger.error(f"Dependency resolution failed: {plugin.plugin_id}")
                return False
            
            self.register_plugin(plugin)
            success = await plugin.initialize()
            
            if success:
                await self.emit_event("plugin_loaded", {
                    "plugin_id": plugin.plugin_id,
                    "capabilities": list(plugin.capabilities.keys())
                })
                logger.info(f"Loaded plugin: {plugin.plugin_id}")
                self.metrics["plugins_loaded"] = self.metrics.get("plugins_loaded", 0) + 1
            else:
                await self.unload_plugin(plugin.plugin_id)
                logger.error(f"Failed to initialize plugin: {plugin.plugin_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error loading plugin {plugin.plugin_id}: {e}")
            await self._handle_error("plugin_load_error", e, {"plugin_id": plugin.plugin_id})
            return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        
        try:
            await plugin.cleanup()
            
            # Remove from capability index
            for capability_name in list(plugin.capabilities.keys()):
                if capability_name in self.global_capabilities:
                    if plugin_id in self.global_capabilities[capability_name]:
                        self.global_capabilities[capability_name].remove(plugin_id)
                    if not self.global_capabilities[capability_name]:
                        del self.global_capabilities[capability_name]
            
            del self.plugins[plugin_id]
            
            await self.emit_event("plugin_unloaded", {"plugin_id": plugin_id})
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
    
    async def call_capability(self, capability_name: str, *args, 
                            plugin_id: str = None, use_cache: bool = True, **kwargs) -> Any:
        """Call a capability with caching, error handling, and performance monitoring"""
        self.metrics["calls"] += 1
        
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(capability_name, args, kwargs, plugin_id)
            if cache_key in self.capability_cache:
                self.metrics["cache_hits"] += 1
                return self.capability_cache[cache_key]
        
        try:
            if capability_name not in self.global_capabilities:
                raise ValueError(f"Capability '{capability_name}' not available")
            
            available_plugins = self.global_capabilities[capability_name]
            
            # Use specific plugin if requested
            if plugin_id:
                if plugin_id not in available_plugins:
                    raise ValueError(f"Plugin {plugin_id} doesn't provide capability '{capability_name}'")
                target_plugin = plugin_id
            else:
                # Load balancing - use least used plugin
                target_plugin = self._select_best_plugin(available_plugins)
            
            plugin = self.plugins[target_plugin]
            
            # Apply middleware
            for middleware in self.middleware_stack:
                args, kwargs = await self._apply_middleware(middleware, capability_name, args, kwargs)
            
            # Execute capability
            result = await plugin.execute_capability(capability_name, *args, **kwargs)
            
            # Cache result if appropriate
            if use_cache and self._should_cache(capability_name, result):
                cache_key = self._generate_cache_key(capability_name, args, kwargs, plugin_id)
                self.capability_cache[cache_key] = result
                # Limit cache size
                if len(self.capability_cache) > 1000:
                    self._cleanup_cache()
            
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            await self._handle_error("capability_call_error", e, {
                "capability": capability_name, 
                "plugin_id": plugin_id,
                "args": str(args)[:100]
            })
            raise
    
    async def call_multiple(self, capability_name: str, *args, **kwargs) -> List[Any]:
        """Call capability on all plugins that provide it"""
        if capability_name not in self.global_capabilities:
            return []
        
        results = []
        for plugin_id in self.global_capabilities[capability_name]:
            try:
                result = await self.call_capability(capability_name, *args, plugin_id=plugin_id, **kwargs)
                results.append({"plugin_id": plugin_id, "result": result, "success": True})
            except Exception as e:
                results.append({"plugin_id": plugin_id, "error": str(e), "success": False})
        
        return results
    
    async def emit_event(self, event_name: str, data: Any = None):
        """Emit event to all interested plugins"""
        for plugin in self.plugins.values():
            await plugin.trigger_hooks(event_name, data)
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to the capability call stack"""
        self.middleware_stack.append(middleware)
    
    async def _apply_middleware(self, middleware: Callable, capability_name: str, 
                              args: tuple, kwargs: dict) -> tuple:
        """Apply middleware function"""
        if asyncio.iscoroutinefunction(middleware):
            return await middleware(capability_name, args, kwargs)
        else:
            return middleware(capability_name, args, kwargs)
    
    def extend_framework(self, extension_name: str, extension: Any):
        """Add extension to framework"""
        self.extensions[extension_name] = extension
        logger.info(f"Added framework extension: {extension_name}")
    
    def get_extension(self, extension_name: str) -> Any:
        """Get framework extension"""
        return self.extensions.get(extension_name)
    
    # Discovery and introspection
    def list_capabilities(self) -> Dict[str, List[str]]:
        """List all available capabilities and which plugins provide them"""
        return self.global_capabilities.copy()
    
    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed plugin information"""
        if plugin_id not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_id]
        return {
            "plugin_id": plugin_id,
            "initialized": plugin.initialized,
            "capabilities": plugin.get_capability_info(),
            "hooks": list(plugin.hooks.keys()),
            "config": plugin.config
        }
    
    def discover_capability_providers(self, capability_name: str) -> List[Dict[str, Any]]:
        """Find all plugins that can provide a capability"""
        if capability_name not in self.global_capabilities:
            return []
        
        providers = []
        for plugin_id in self.global_capabilities[capability_name]:
            plugin = self.plugins[plugin_id]
            capability = plugin.capabilities[capability_name]
            providers.append({
                "plugin_id": plugin_id,
                "metadata": capability.metadata,
                "parameters": [p.name for p in capability.signature.parameters.values()]
            })
        
        return providers
    
    def get_framework_stats(self) -> Dict[str, Any]:
        """Get comprehensive framework statistics"""
        return {
            "running": self.running,
            "total_plugins": len(self.plugins),
            "total_capabilities": len(self.global_capabilities),
            "middleware_count": len(self.middleware_stack),
            "extensions": list(self.extensions.keys()),
            "metrics": self.metrics.copy(),
            "cache_size": len(self.capability_cache),
            "dependencies": len(self.plugin_dependencies),
            "validators": len(self.validators),
            "error_handlers": len(self.error_handlers)
        }
    
    # Advanced framework methods
    async def _validate_plugin(self, plugin: Plugin) -> bool:
        """Validate plugin before loading"""
        # Basic validation
        if not plugin.plugin_id or not plugin.capabilities:
            return False
        
        # Run custom validators
        for validator in self.validators:
            try:
                if not await validator(plugin):
                    return False
            except Exception as e:
                logger.error(f"Validator error: {e}")
                return False
        
        return True
    
    async def _resolve_dependencies(self, plugin: Plugin) -> bool:
        """Resolve and load plugin dependencies"""
        # Check if plugin declares dependencies
        dependencies = getattr(plugin, 'dependencies', [])
        if not dependencies:
            return True
        
        # Store dependencies
        self.plugin_dependencies[plugin.plugin_id] = dependencies
        
        # Check if all dependencies are loaded
        for dep in dependencies:
            if dep not in self.plugins:
                logger.error(f"Missing dependency '{dep}' for plugin '{plugin.plugin_id}'")
                return False
        
        return True
    
    def _select_best_plugin(self, available_plugins: List[str]) -> str:
        """Select best plugin for load balancing"""
        # Simple round-robin for now
        plugin_usage = {pid: self.metrics.get(f"plugin_calls_{pid}", 0) for pid in available_plugins}
        return min(plugin_usage.items(), key=lambda x: x[1])[0]
    
    def _generate_cache_key(self, capability: str, args: tuple, kwargs: dict, plugin_id: str = None) -> str:
        """Generate cache key for capability call"""
        import hashlib
        key_data = f"{capability}:{plugin_id}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _should_cache(self, capability: str, result: Any) -> bool:
        """Determine if result should be cached"""
        # Don't cache large results or certain types
        if isinstance(result, (dict, list)) and len(str(result)) > 10000:
            return False
        # Cache pure functions and data retrievals
        return capability in ['get_', 'fetch_', 'load_', 'read_'] or True
    
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        # Simple LRU - remove oldest 100 entries
        if len(self.capability_cache) > 1000:
            keys_to_remove = list(self.capability_cache.keys())[:100]
            for key in keys_to_remove:
                del self.capability_cache[key]
    
    async def _handle_error(self, error_type: str, error: Exception, context: Dict[str, Any]):
        """Handle errors with recovery strategies"""
        if error_type in self.error_handlers:
            try:
                await self.error_handlers[error_type](error, context)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
        
        # Emit error event
        await self.emit_event("error", {
            "type": error_type,
            "error": str(error),
            "context": context
        })
    
    def add_validator(self, validator: Callable):
        """Add plugin validator"""
        self.validators.append(validator)
    
    def add_error_handler(self, error_type: str, handler: Callable):
        """Add error handler for specific error types"""
        self.error_handlers[error_type] = handler
    
    def set_config(self, key: str, value: Any):
        """Set global configuration"""
        self.config_store[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get global configuration"""
        return self.config_store.get(key, default)
    
    def clear_cache(self):
        """Clear capability cache"""
        self.capability_cache.clear()
        logger.info("Capability cache cleared")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics"""
        return {
            **self.metrics,
            "cache_hit_rate": self.metrics.get("cache_hits", 0) / max(self.metrics.get("calls", 1), 1),
            "error_rate": self.metrics.get("errors", 0) / max(self.metrics.get("calls", 1), 1),
            "plugins_per_capability": {
                cap: len(plugins) for cap, plugins in self.global_capabilities.items()
            }
        }