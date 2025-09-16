"""
OpenAI LLM Plugin - Real implementation
"""

import openai
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

class OpenAILLMPlugin(LLMPlugin):
    """Real OpenAI LLM implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate OpenAI configuration"""
        required_fields = ["api_key"]
        if not all(field in config and config[field] for field in required_fields):
            return False
        
        # Validate model name
        valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        model = config.get("model", "gpt-4o-mini")
        if model not in valid_models:
            logger.warning(f"Model {model} not in validated list, but proceeding")
        
        return True
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            self.client = openai.AsyncOpenAI(
                api_key=self.config["api_key"]
            )
            
            # Test the connection
            await self.test_generation()
            self.initialized = True
            logger.info("OpenAI client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: str = "", **kwargs) -> str:
        """Generate response using OpenAI"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Prepare messages
            messages = []
            
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Use the following context to answer the user's question:\n\n{context}"
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # Override defaults with kwargs
            temperature = kwargs.get("temperature", self.temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            model = kwargs.get("model", self.model)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
    
    async def test_generation(self) -> bool:
        """Test OpenAI generation capability"""
        try:
            response = await self.generate_response(
                "Say 'Hello' if you can hear me.",
                max_tokens=10
            )
            return "hello" in response.lower()
        except Exception as e:
            logger.error(f"OpenAI test generation failed: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        return {
            "model": self.model,
            "provider": "OpenAI",
            "capabilities": ["text_generation", "embeddings"],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }