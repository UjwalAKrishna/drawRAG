"""
Example: Super Simple Math Plugin - Shows how easy plugin development is
"""

from backend.core import QuickPlugin, capability


class SimpleMathPlugin(QuickPlugin):
    """Math operations plugin - demonstrates minimal plugin development"""
    
    def __init__(self, plugin_id: str = "simple_math", config: dict = None):
        super().__init__(plugin_id, config)
    
    @capability("Add two numbers")
    def add(self, x: float, y: float) -> float:
        """Add two numbers together"""
        return x + y
    
    @capability("Multiply two numbers")
    def multiply(self, x: float, y: float) -> float:
        """Multiply two numbers"""
        return x * y
    
    @capability("Calculate power")
    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to exponent"""
        return base ** exponent
    
    def get_pi(self) -> float:
        """Get value of PI - auto-registered as capability"""
        return 3.14159265359