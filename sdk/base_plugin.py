"""
Base Plugin Classes for RAG Builder SDK
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all RAG Builder plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
        self.plugin_type = "base"
        self.version = "1.0.0"
    
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    async def cleanup(self):
        """Clean up plugin resources"""
        self.initialized = False
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            "type": self.plugin_type,
            "version": self.version,
            "initialized": self.initialized,
            "config_keys": list(self.config.keys()) if self.config else []
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get plugin health status"""
        return {
            "healthy": self.initialized,
            "status": "ready" if self.initialized else "not_initialized",
            "last_error": None
        }
    
    async def test_connection(self) -> bool:
        """Test plugin connection/functionality"""
        return self.initialized