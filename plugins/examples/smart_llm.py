"""
Example: Smart LLM Plugin - Shows inheritance and event handling
"""

from backend.core import LLMPlugin, event_handler, capability, requires
from typing import List, Dict, Any
import hashlib
import random


class SmartLLMPlugin(LLMPlugin):
    """Example LLM plugin with smart features"""
    
    def __init__(self, plugin_id: str = "smart_llm", config: dict = None):
        super().__init__(plugin_id, config or {})
        self.response_cache = {}
        self.stats = {"requests": 0, "cache_hits": 0}
    
    @capability("Generate intelligent text responses")
    def generate_text(self, prompt: str, **options) -> str:
        """Generate text from prompt with caching"""
        self.stats["requests"] += 1
        
        # Check cache
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        if cache_key in self.response_cache:
            self.stats["cache_hits"] += 1
            return self.response_cache[cache_key]
        
        # Generate response (mock implementation)
        response = f"Smart response to: {prompt[:50]}..."
        if "creative" in options:
            response += " [Creative mode enabled]"
        
        # Cache response
        self.response_cache[cache_key] = response
        return response
    
    @capability("Generate text embeddings")
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = []
        for text in texts:
            # Mock embedding generation
            seed = abs(hash(text)) % (10**8)
            random.seed(seed)
            embedding = [random.random() for _ in range(384)]
            embeddings.append(embedding)
        return embeddings
    
    @capability("Get model statistics")
    def get_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            **self.stats,
            "cache_size": len(self.response_cache),
            "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["requests"], 1)
        }
    
    @event_handler("system_startup")
    def on_startup(self, event_data):
        """Handle system startup event"""
        print(f"🤖 Smart LLM Plugin ready! Config: {self.config}")
    
    @requires("clean_text")  # Requires text_processor plugin
    @capability("Generate clean response")
    async def generate_clean_response(self, prompt: str) -> str:
        """Generate response and clean it using text processor"""
        # This will automatically call the text processor's clean_text capability
        response = self.generate_text(prompt)
        # Framework will automatically resolve the dependency
        return response  # In real implementation, would call clean_text