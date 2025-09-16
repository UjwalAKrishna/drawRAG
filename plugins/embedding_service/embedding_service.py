"""
Embedding Service Plugin - Handles embedding generation and similarity
"""

import logging
from typing import Dict, List, Any, Optional
import hashlib
import random
from pathlib import Path
import sys

# Import the core plugin interface  
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from core.plugin_framework import PluginInterface

logger = logging.getLogger(__name__)


class EmbeddingServicePlugin(PluginInterface):
    """Embedding service plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cache_size = config.get("cache_size", 10000)
        self.embedding_dimension = config.get("embedding_dimension", 384)
        self.embedding_cache: Dict[str, List[float]] = {}
        self.stats = {
            "total_embeddings": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize(self) -> bool:
        """Initialize the embedding service"""
        try:
            self.initialized = True
            logger.info("Embedding service plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        self.embedding_cache.clear()
        self.initialized = False
    
    def get_capabilities(self) -> List[str]:
        """Get plugin capabilities"""
        return ["generate_embeddings", "similarity_search", "batch_embeddings"]
    
    async def execute(self, input_data: Dict[str, Any], config: Dict[str, Any], 
                     previous_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute embedding operations"""
        operation = input_data.get("operation", "generate_embeddings")
        
        if operation == "generate_embeddings":
            texts = input_data.get("texts", [])
            embeddings = await self.generate_embeddings(texts)
            return {"embeddings": embeddings, "dimension": len(embeddings[0]) if embeddings else 0}
        
        elif operation == "similarity_search":
            query_embedding = input_data.get("query_embedding", [])
            document_embeddings = input_data.get("document_embeddings", [])
            top_k = input_data.get("top_k", 5)
            results = await self.similarity_search(query_embedding, document_embeddings, top_k)
            return {"results": results}
        
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = []
        
        for text in texts:
            # Check cache first
            text_hash = self._hash_text(text)
            if text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
                self.stats["cache_hits"] += 1
                continue
            
            # Generate new embedding
            embedding = self._generate_mock_embedding(text)
            
            # Cache with size limit
            if len(self.embedding_cache) < self.cache_size:
                self.embedding_cache[text_hash] = embedding
            
            embeddings.append(embedding)
            self.stats["cache_misses"] += 1
            self.stats["total_embeddings"] += 1
        
        return embeddings
    
    async def similarity_search(self, query_embedding: List[float], 
                               document_embeddings: List[List[float]], 
                               top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search"""
        similarities = []
        
        for i, doc_embedding in enumerate(document_embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append({
                "index": i,
                "similarity": similarity
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:top_k]
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding based on text content"""
        # Create deterministic seed from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        random.seed(int(text_hash[:8], 16))
        
        # Generate embedding with some text-based characteristics
        embedding = []
        for i in range(self.embedding_dimension):
            # Add some text length influence
            base_value = random.random() - 0.5
            length_influence = (len(text) % 100) / 1000.0
            embedding.append(base_value + length_influence)
        
        return embedding
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text caching"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.embedding_cache),
            "cache_limit": self.cache_size,
            "embedding_dimension": self.embedding_dimension
        }


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> EmbeddingServicePlugin:
    """Create plugin instance"""
    return EmbeddingServicePlugin(config)