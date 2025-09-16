"""
LLM Plugin Base Class
"""

from abc import abstractmethod
from typing import Dict, List, Any, Optional
from .base_plugin import BasePlugin


class BaseLLMPlugin(BasePlugin):
    """Base class for LLM plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.plugin_type = "llm"
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate text response
        
        Args:
            prompt: The user prompt/question
            context: Additional context for the response
            
        Returns:
            str: Generated response text
        """
        pass
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate text embeddings (optional)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        # Default implementation - not all LLMs support embeddings
        raise NotImplementedError("This LLM does not support embedding generation")
    
    async def generate_streaming_response(self, prompt: str, context: str = "") -> Any:
        """Generate streaming response (optional)
        
        Args:
            prompt: The user prompt/question
            context: Additional context for the response
            
        Yields:
            str: Response chunks as they are generated
        """
        # Default implementation: return full response at once
        response = await self.generate_response(prompt, context)
        yield response
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information
        
        Returns:
            Dict[str, Any]: Model metadata and capabilities
        """
        return {
            "type": "llm",
            "model": self.config.get("model", "unknown"),
            "supports_embeddings": hasattr(self, 'generate_embeddings'),
            "supports_streaming": hasattr(self, 'generate_streaming_response'),
            "max_tokens": self.config.get("max_tokens", "unknown"),
            "temperature": self.config.get("temperature", "unknown")
        }
    
    async def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (optional)
        
        Args:
            text: Text to count tokens for
            
        Returns:
            int: Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def build_rag_prompt(self, question: str, context: str, system_prompt: str = None) -> str:
        """Build a RAG-style prompt with context
        
        Args:
            question: User question
            context: Retrieved context documents
            system_prompt: Optional system prompt
            
        Returns:
            str: Formatted prompt
        """
        if system_prompt:
            prompt = f"{system_prompt}\n\n"
        else:
            prompt = "You are a helpful assistant. Answer the question based on the provided context.\n\n"
        
        prompt += f"Context:\n{context}\n\n"
        prompt += f"Question: {question}\n\n"
        prompt += "Answer:"
        
        return prompt
    
    async def validate_prompt_length(self, prompt: str) -> bool:
        """Validate prompt length against model limits
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            bool: True if prompt is within limits
        """
        max_tokens = self.config.get("max_tokens", 4000)
        estimated_tokens = await self.estimate_tokens(prompt)
        
        # Leave some room for response
        return estimated_tokens < (max_tokens * 0.8)
    
    async def test_connection(self) -> bool:
        """Test LLM connection"""
        if not self.initialized:
            return False
        
        try:
            # Try a simple generation
            response = await self.generate_response("Hello", "")
            return len(response) > 0
        except Exception:
            return False