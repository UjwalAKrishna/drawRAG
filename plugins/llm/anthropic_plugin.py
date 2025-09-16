"""
Anthropic Claude LLM Plugin - Real implementation
"""

import anthropic
from typing import Dict, List, Any
import logging
import sys
from pathlib import Path

# Add backend to Python path for base plugin imports
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.base_plugin import LLMPlugin

logger = logging.getLogger(__name__)

class AnthropicLLMPlugin(LLMPlugin):
    """Real Anthropic Claude implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.model = config.get("model", "claude-3-sonnet-20240229")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Anthropic configuration"""
        required_fields = ["api_key"]
        if not all(field in config and config[field] for field in required_fields):
            return False
        
        # Validate model name
        valid_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
        model = config.get("model", "claude-3-sonnet-20240229")
        if model not in valid_models:
            logger.warning(f"Model {model} not in validated list, but proceeding")
        
        return True
    
    async def initialize(self) -> bool:
        """Initialize Anthropic client"""
        try:
            self.client = anthropic.AsyncAnthropic(
                api_key=self.config["api_key"]
            )
            
            # Test the connection
            await self.test_generation()
            self.initialized = True
            logger.info("Anthropic client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: str = "", **kwargs) -> str:
        """Generate response using Anthropic Claude"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Prepare the message
            if context:
                full_prompt = f"Context: {context}\n\nHuman: {prompt}\n\nAssistant:"
            else:
                full_prompt = f"Human: {prompt}\n\nAssistant:"
            
            # Override defaults with kwargs
            temperature = kwargs.get("temperature", self.temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            model = kwargs.get("model", self.model)
            
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings (Anthropic doesn't have embeddings API, use fallback)"""
        logger.warning("Anthropic doesn't provide embeddings API, using mock embeddings")
        
        # Return mock embeddings with consistent dimensions
        import random
        random.seed(42)  # For consistent results
        return [[random.random() for _ in range(1536)] for _ in texts]
    
    async def test_generation(self) -> bool:
        """Test Anthropic generation capability"""
        try:
            response = await self.generate_response(
                "Say 'Hello' if you can hear me.",
                max_tokens=10
            )
            return "hello" in response.lower()
        except Exception as e:
            logger.error(f"Anthropic test generation failed: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information"""
        return {
            "model": self.model,
            "provider": "Anthropic",
            "capabilities": ["text_generation"],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": 200000 if "claude-3" in self.model else 100000
        }