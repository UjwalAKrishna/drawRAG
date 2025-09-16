"""
ChromaDB Vector Database Plugin - Real implementation
"""

import chromadb
from chromadb.config import Settings
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

class ChromaVectorDBPlugin(VectorDBPlugin):
    """Real ChromaDB implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.collection_name = config.get("collection_name", "rag_collection")
        self.persist_directory = config.get("persist_directory", "./chroma_db")
        self.client = None
        self.collection = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate ChromaDB configuration"""
        required_fields = ["collection_name"]
        return all(field in config and config[field] for field in required_fields)
    
    async def initialize(self) -> bool:
        """Initialize ChromaDB client"""
        try:
            # Create ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "RAG Builder collection"}
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection"""
        try:
            if not self.client:
                return False
            
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"dimension": dimension}
            )
            self.collection_name = collection_name
            logger.info(f"Created ChromaDB collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store document vectors in ChromaDB"""
        if not self.initialized or not self.collection:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                doc_id = doc.get("id", str(uuid.uuid4()))
                ids.append(doc_id)
                texts.append(doc.get("content", ""))
                metadatas.append(doc.get("metadata", {}))
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Stored {len(documents)} documents in ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store vectors in ChromaDB: {e}")
            return False
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors from ChromaDB"""
        if not self.initialized or not self.collection:
            raise RuntimeError("Plugin not initialized")
        
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)
                distances = results["distances"][0] if results["distances"] else [0.0] * len(documents)
                
                for i, doc in enumerate(documents):
                    formatted_results.append({
                        "id": results["ids"][0][i] if results["ids"] else f"doc_{i}",
                        "content": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "score": 1.0 - distances[i] if i < len(distances) else 0.0  # Convert distance to similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query vectors from ChromaDB: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            if not self.client:
                return False
            
            self.client.delete_collection(collection_name)
            if collection_name == self.collection_name:
                self.collection = None
            
            logger.info(f"Deleted ChromaDB collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        if not self.initialized or not self.collection:
            return {"vector_count": 0, "dimension": 0, "status": "not_initialized"}
        
        try:
            count = self.collection.count()
            return {
                "vector_count": count,
                "dimension": "variable",  # ChromaDB handles variable dimensions
                "status": "active",
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"vector_count": 0, "dimension": 0, "status": "error"}
    
    async def cleanup(self):
        """Clean up ChromaDB resources"""
        self.collection = None
        self.client = None
        await super().cleanup()