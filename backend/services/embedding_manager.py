"""
Embedding Manager - Handles text embedding generation and management
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from .similarity_calculator import SimilarityCalculator

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding generation for RAG pipelines"""
    
    def __init__(self):
        self.embedding_cache: Dict[str, List[float]] = {}
        self.embedding_stats = {
            "total_embeddings": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        self.similarity_calc = SimilarityCalculator()
    
    async def generate_embeddings(self, texts: List[str], llm_plugin=None) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        embeddings = []
        
        for text in texts:
            # Check cache first
            text_hash = self._hash_text(text)
            if text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
                self.embedding_stats["cache_hits"] += 1
                continue
            
            # Generate new embedding
            try:
                if llm_plugin and hasattr(llm_plugin, 'generate_embeddings'):
                    # Use provided LLM plugin
                    embedding = await llm_plugin.generate_embeddings([text])
                    if embedding and len(embedding) > 0:
                        embedding_vector = embedding[0]
                    else:
                        embedding_vector = self._generate_mock_embedding(text)
                else:
                    # Fallback to mock embedding
                    embedding_vector = self._generate_mock_embedding(text)
                
                # Cache the embedding
                self.embedding_cache[text_hash] = embedding_vector
                embeddings.append(embedding_vector)
                
                self.embedding_stats["cache_misses"] += 1
                self.embedding_stats["total_embeddings"] += 1
                
            except Exception as e:
                logger.error(f"Embedding generation failed for text: {e}")
                # Use mock embedding as fallback
                embedding_vector = self._generate_mock_embedding(text)
                embeddings.append(embedding_vector)
        
        return embeddings
    
    async def generate_query_embedding(self, query: str, llm_plugin=None) -> List[float]:
        """Generate embedding for a single query"""
        embeddings = await self.generate_embeddings([query], llm_plugin)
        return embeddings[0] if embeddings else []
    
    def _generate_mock_embedding(self, text: str, dimension: int = 384) -> List[float]:
        """Generate a mock embedding based on text content"""
        import hashlib
        import random
        
        # Create deterministic seed from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        random.seed(int(text_hash[:8], 16))
        
        # Generate embedding with some text-based characteristics
        embedding = []
        for i in range(dimension):
            # Add some text length influence
            base_value = random.random() - 0.5
            length_influence = (len(text) % 100) / 1000.0
            embedding.append(base_value + length_influence)
        
        return embedding
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text caching"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
    
    async def process_documents_for_vectordb(self, documents: List[Dict[str, Any]], llm_plugin=None) -> Dict[str, Any]:
        """Process documents and generate embeddings for vector database storage"""
        try:
            # Extract text content
            texts = [doc.get("content", "") for doc in documents]
            
            # Generate embeddings
            embeddings = await self.generate_embeddings(texts, llm_plugin)
            
            # Prepare data for vector database
            processed_docs = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                processed_docs.append({
                    "id": doc.get("id", f"doc_{i}"),
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "embedding": embedding
                })
            
            return {
                "status": "success",
                "documents": processed_docs,
                "count": len(processed_docs),
                "embedding_dimension": len(embeddings[0]) if embeddings else 0
            }
            
        except Exception as e:
            logger.error(f"Document processing for vectordb failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to process documents for vector database"
            }
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding generation statistics"""
        cache_hit_rate = 0.0
        if self.embedding_stats["cache_hits"] + self.embedding_stats["cache_misses"] > 0:
            cache_hit_rate = self.embedding_stats["cache_hits"] / (
                self.embedding_stats["cache_hits"] + self.embedding_stats["cache_misses"]
            )
        
        return {
            **self.embedding_stats,
            "cache_size": len(self.embedding_cache),
            "cache_hit_rate": cache_hit_rate
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_size_mb(self) -> float:
        """Estimate cache size in MB"""
        import sys
        total_size = sys.getsizeof(self.embedding_cache)
        for key, value in self.embedding_cache.items():
            total_size += sys.getsizeof(key) + sys.getsizeof(value)
        return total_size / (1024 * 1024)
    
    async def batch_embed_with_progress(self, texts: List[str], llm_plugin=None, batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings in batches with progress tracking"""
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.generate_embeddings(batch, llm_plugin)
            all_embeddings.extend(batch_embeddings)
            
            batch_num = i // batch_size + 1
            logger.info(f"Processed embedding batch {batch_num}/{total_batches}")
            
            # Small delay to prevent overwhelming the embedding service
            if batch_num < total_batches:
                await asyncio.sleep(0.1)
        
        return all_embeddings
    
    def validate_embedding_dimension(self, embeddings: List[List[float]], expected_dim: int = None) -> bool:
        """Validate embedding dimensions"""
        if not embeddings:
            return False
        
        # Check all embeddings have same dimension
        first_dim = len(embeddings[0])
        if not all(len(emb) == first_dim for emb in embeddings):
            return False
        
        # Check against expected dimension if provided
        if expected_dim and first_dim != expected_dim:
            return False
        
        return True
    
    async def similarity_search(self, query_embedding: List[float], document_embeddings: List[List[float]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search between query and document embeddings"""
        return self.similarity_calc.similarity_search(query_embedding, document_embeddings, "cosine", top_k)