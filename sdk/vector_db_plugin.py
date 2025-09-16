"""
Vector Database Plugin Base Class
"""

from abc import abstractmethod
from typing import Dict, List, Any, Optional
from .base_plugin import BasePlugin


class BaseVectorDBPlugin(BasePlugin):
    """Base class for vector database plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.plugin_type = "vectordb"
    
    @abstractmethod
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store document vectors in the database
        
        Args:
            documents: List of documents with id, content, and metadata
            embeddings: List of embedding vectors corresponding to documents
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: Similar documents with scores
        """
        pass
    
    async def delete_vectors(self, document_ids: List[str]) -> bool:
        """Delete vectors by document IDs (optional)
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            bool: True if deletion successful
        """
        # Default implementation - not all vector DBs support deletion
        return False
    
    async def update_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Update existing vectors (optional)
        
        Args:
            documents: List of documents to update
            embeddings: Updated embedding vectors
            
        Returns:
            bool: True if update successful
        """
        # Default implementation: delete and re-insert
        doc_ids = [doc["id"] for doc in documents]
        await self.delete_vectors(doc_ids)
        return await self.store_vectors(documents, embeddings)
    
    async def get_vector_count(self) -> int:
        """Get total number of vectors stored
        
        Returns:
            int: Total vector count
        """
        # Default implementation - not all vector DBs provide this efficiently
        return 0
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection/index information
        
        Returns:
            Dict[str, Any]: Collection metadata
        """
        return {
            "type": "vectordb",
            "vector_count": await self.get_vector_count(),
            "supports_deletion": hasattr(self, 'delete_vectors'),
            "supports_updates": hasattr(self, 'update_vectors'),
            "dimension": self.config.get("dimension", "unknown")
        }
    
    def validate_embedding_dimension(self, embeddings: List[List[float]]) -> bool:
        """Validate embedding dimensions
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            bool: True if dimensions are consistent and valid
        """
        if not embeddings:
            return True
        
        expected_dim = self.config.get("dimension")
        if expected_dim:
            return all(len(emb) == expected_dim for emb in embeddings)
        
        # If no expected dimension, check that all embeddings have same dimension
        first_dim = len(embeddings[0])
        return all(len(emb) == first_dim for emb in embeddings)
    
    async def test_connection(self) -> bool:
        """Test vector database connection"""
        if not self.initialized:
            return False
        
        try:
            # Try a simple query with a dummy vector
            test_vector = [0.0] * self.config.get("dimension", 384)
            results = await self.query_vectors(test_vector, top_k=1)
            return True  # If query doesn't fail, connection is working
        except Exception:
            return False