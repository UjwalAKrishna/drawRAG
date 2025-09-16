"""
API Dependencies - Shared resources and dependency injection
"""

from functools import lru_cache
from backend.core import Manager

# Global manager instance
_manager = None


def get_manager() -> Manager:
    """Get the global manager instance"""
    global _manager
    if _manager is None:
        _manager = Manager("plugins")
    return _manager


async def initialize_manager():
    """Initialize the manager on startup"""
    manager = get_manager()
    await manager.start()
    return manager


async def shutdown_manager():
    """Shutdown the manager on app shutdown"""
    manager = get_manager()
    await manager.stop()