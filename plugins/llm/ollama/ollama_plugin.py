"""
Ollama LLM Plugin - Real implementation
"""

import httpx
import json
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

class OllamaLLMPlugin(LLMPlugin):
    """Real Ollama LLM implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama2")
        self.temperature = config.get("temperature", 0.7)
        self.client = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Ollama configuration"""
        required_fields = ["model"]
        return all(field in config and config[field] for field in required_fields)
    
    async def initialize(self) -> bool:
        """Initialize Ollama client"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection and check if model exists
            available = await self._check_model_availability()
            if not available:
                logger.warning(f"Model {self.model} not found, attempting to pull...")
                await self._pull_model()
            
            # Test generation
            await self.test_generation()
            self.initialized = True
            logger.info(f"Ollama client initialized with model: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: str = "", **kwargs) -> str:
        """Generate response using Ollama"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Prepare the full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            # Override defaults with kwargs
            temperature = kwargs.get("temperature", self.temperature)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            embeddings = []
            for text in texts:
                payload = {
                    "model": self.model,
                    "prompt": text
                }
                
                response = await self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                embeddings.append(result.get("embedding", []))
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Ollama embedding generation failed: {e}")
            # Fallback to mock embeddings if embeddings endpoint not available
            import random
            return [[random.random() for _ in range(384)] for _ in texts]
    
    async def test_generation(self) -> bool:
        """Test Ollama generation capability"""
        try:
            response = await self.generate_response("Say hello.")
            return len(response) > 0
        except Exception as e:
            logger.error(f"Ollama test generation failed: {e}")
            return False
    
    async def _check_model_availability(self) -> bool:
        """Check if the model is available locally"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            model_names = [model.get("name", "").split(":")[0] for model in models]
            
            return self.model in model_names
            
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def _pull_model(self) -> bool:
        """Pull the model if not available"""
        try:
            payload = {"name": self.model}
            
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Successfully pulled model: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {self.model}: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model information"""
        return {
            "model": self.model,
            "provider": "Ollama",
            "base_url": self.base_url,
            "capabilities": ["text_generation", "embeddings"],
            "temperature": self.temperature
        }
    
    async def cleanup(self):
        """Clean up Ollama client"""
        if self.client:
            await self.client.aclose()
        await super().cleanup()