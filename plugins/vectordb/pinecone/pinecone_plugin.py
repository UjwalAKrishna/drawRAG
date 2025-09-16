"""
Pinecone Vector Database Plugin - Real implementation
"""

import pinecone
from typing import Dict, List, Any, Optional
import logging
import uuid
import sys
from pathlib import Path

# Add backend to Python path for base plugin imports
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.base_plugin import VectorDBPlugin

logger = logging.getLogger(__name__)

class PineconeVectorDBPlugin(VectorDBPlugin):
    """Real Pinecone implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.environment = config.get("environment")
        self.index_name = config.get("index_name", "rag-builder-index")
        self.dimension = config.get("dimension", 1536)
        self.metric = config.get("metric", "cosine")
        
        self.index = None
        self.pc = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Pinecone configuration"""
        required_fields = ["api_key", "environment", "index_name"]
        if not all(field in config and config[field] for field in required_fields):
            return False
        
        # Validate dimension
        dimension = config.get("dimension", 1536)
        if not isinstance(dimension, int) or dimension <= 0:
            return False
        
        # Validate metric
        metric = config.get("metric", "cosine")
        valid_metrics = ["cosine", "euclidean", "dotproduct"]
        if metric not in valid_metrics:
            return False
        
        return True
    
    async def initialize(self) -> bool:
        """Initialize Pinecone client"""
        try:
            # Initialize Pinecone
            self.pc = pinecone.Pinecone(
                api_key=self.api_key,
                environment=self.environment
            )
            
            # Check if index exists, create if not
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=pinecone.ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
            self.initialized = True
            logger.info(f"Pinecone client initialized with index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new Pinecone index"""
        try:
            if not self.pc:
                return False
            
            # Check if index already exists
            existing_indexes = self.pc.list_indexes().names()
            if collection_name in existing_indexes:
                logger.info(f"Index {collection_name} already exists")
                self.index = self.pc.Index(collection_name)
                self.index_name = collection_name
                return True
            
            # Create new index
            self.pc.create_index(
                name=collection_name,
                dimension=dimension,
                metric=self.metric,
                spec=pinecone.ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
            self.index = self.pc.Index(collection_name)
            self.index_name = collection_name
            self.dimension = dimension
            
            logger.info(f"Created Pinecone index: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Pinecone index {collection_name}: {e}")
            return False
    
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store document vectors in Pinecone"""
        if not self.initialized or not self.index:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Prepare vectors for Pinecone
            vectors = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                doc_id = doc.get("id", str(uuid.uuid4()))
                metadata = {
                    "content": doc.get("content", "")[:40000],  # Pinecone metadata limit
                    "source": doc.get("metadata", {}).get("source", "unknown"),
                    **{k: v for k, v in doc.get("metadata", {}).items() 
                       if k != "source" and len(str(v)) < 1000}  # Limit metadata size
                }
                
                vectors.append({
                    "id": doc_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert vectors in batches (Pinecone has batch size limits)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            logger.info(f"Stored {len(documents)} documents in Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store vectors in Pinecone: {e}")
            return False
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors from Pinecone"""
        if not self.initialized or not self.index:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Query Pinecone
            response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Format results
            results = []
            for match in response.matches:
                metadata = match.metadata or {}
                results.append({
                    "id": match.id,
                    "content": metadata.get("content", ""),
                    "metadata": {k: v for k, v in metadata.items() if k != "content"},
                    "score": float(match.score)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query vectors from Pinecone: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a Pinecone index"""
        try:
            if not self.pc:
                return False
            
            self.pc.delete_index(collection_name)
            
            if collection_name == self.index_name:
                self.index = None
            
            logger.info(f"Deleted Pinecone index: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Pinecone index {collection_name}: {e}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Pinecone index"""
        if not self.initialized or not self.index:
            return {"vector_count": 0, "dimension": 0, "status": "not_initialized"}
        
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "vector_count": stats.total_vector_count,
                "dimension": self.dimension,
                "status": "active",
                "index_name": self.index_name,
                "metric": self.metric,
                "environment": self.environment
            }
            
        except Exception as e:
            logger.error(f"Failed to get Pinecone index info: {e}")
            return {"vector_count": 0, "dimension": 0, "status": "error"}
    
    async def cleanup(self):
        """Clean up Pinecone resources"""
        self.index = None
        self.pc = None
        await super().cleanup()