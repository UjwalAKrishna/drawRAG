"""
FAISS Vector Database Plugin - Real implementation
"""

import faiss
import numpy as np
import pickle
import os
from typing import Dict, List, Any, Optional
import logging
import sys
from pathlib import Path

# Add backend to Python path for base plugin imports
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.base_plugin import VectorDBPlugin

logger = logging.getLogger(__name__)

class FAISSVectorDBPlugin(VectorDBPlugin):
    """Real FAISS implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.dimension = config.get("dimension", 384)
        self.index_type = config.get("index_type", "flat")
        self.index_path = config.get("index_path", "./faiss_index")
        self.metadata_path = config.get("metadata_path", "./faiss_metadata.pkl")
        
        self.index = None
        self.metadata = []  # Store document metadata
        self.id_to_index = {}  # Map document IDs to index positions
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate FAISS configuration"""
        required_fields = ["dimension"]
        if not all(field in config and config[field] for field in required_fields):
            return False
        
        # Validate dimension
        dimension = config.get("dimension")
        if not isinstance(dimension, int) or dimension <= 0:
            return False
        
        # Validate index type
        index_type = config.get("index_type", "flat")
        valid_types = ["flat", "ivf"]
        if index_type not in valid_types:
            return False
        
        return True
    
    async def initialize(self) -> bool:
        """Initialize FAISS index"""
        try:
            # Try to load existing index
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                await self._load_index()
                logger.info("Loaded existing FAISS index")
            else:
                # Create new index
                await self.create_collection("default", self.dimension)
                logger.info("Created new FAISS index")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new FAISS index"""
        try:
            self.dimension = dimension
            
            if self.index_type == "flat":
                # L2 distance (Euclidean)
                self.index = faiss.IndexFlatL2(dimension)
            elif self.index_type == "ivf":
                # IVF index for faster search on large datasets
                quantizer = faiss.IndexFlatL2(dimension)
                nlist = 100  # Number of clusters
                self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            else:
                raise ValueError(f"Unsupported index type: {self.index_type}")
            
            # Reset metadata
            self.metadata = []
            self.id_to_index = {}
            
            logger.info(f"Created FAISS {self.index_type} index with dimension {dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            return False
    
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store document vectors in FAISS"""
        if not self.initialized or self.index is None:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Convert embeddings to numpy array
            vectors = np.array(embeddings, dtype=np.float32)
            
            # Train index if it's IVF and not trained yet
            if self.index_type == "ivf" and not self.index.is_trained:
                if len(embeddings) >= 100:  # Need enough data to train
                    self.index.train(vectors)
                    logger.info("Trained IVF index")
                else:
                    logger.warning("Not enough data to train IVF index, using flat index instead")
                    self.index = faiss.IndexFlatL2(self.dimension)
            
            # Get starting index for new documents
            start_idx = self.index.ntotal
            
            # Add vectors to index
            self.index.add(vectors)
            
            # Store metadata
            for i, doc in enumerate(documents):
                doc_id = doc.get("id", f"doc_{start_idx + i}")
                metadata = {
                    "id": doc_id,
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {})
                }
                self.metadata.append(metadata)
                self.id_to_index[doc_id] = start_idx + i
            
            # Save index and metadata
            await self._save_index()
            
            logger.info(f"Stored {len(documents)} documents in FAISS index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store vectors in FAISS: {e}")
            return False
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors from FAISS"""
        if not self.initialized or self.index is None:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # Convert query to numpy array
            query_array = np.array([query_vector], dtype=np.float32)
            
            # Search
            distances, indices = self.index.search(query_array, top_k)
            
            # Format results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.metadata):  # Valid index
                    metadata = self.metadata[idx]
                    distance = distances[0][i]
                    
                    # Convert L2 distance to similarity score (0-1, higher is better)
                    # Using exponential decay: similarity = exp(-distance)
                    similarity = np.exp(-distance)
                    
                    results.append({
                        "id": metadata["id"],
                        "content": metadata["content"],
                        "metadata": metadata["metadata"],
                        "score": float(similarity)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query vectors from FAISS: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete FAISS index files"""
        try:
            # Remove index files
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
            if os.path.exists(self.metadata_path):
                os.remove(self.metadata_path)
            
            # Reset in-memory structures
            self.index = None
            self.metadata = []
            self.id_to_index = {}
            
            logger.info("Deleted FAISS index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete FAISS index: {e}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the FAISS index"""
        if not self.initialized or self.index is None:
            return {"vector_count": 0, "dimension": 0, "status": "not_initialized"}
        
        try:
            return {
                "vector_count": self.index.ntotal,
                "dimension": self.dimension,
                "status": "active",
                "index_type": self.index_type,
                "is_trained": getattr(self.index, 'is_trained', True),
                "index_path": self.index_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get FAISS index info: {e}")
            return {"vector_count": 0, "dimension": 0, "status": "error"}
    
    async def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'id_to_index': self.id_to_index,
                    'dimension': self.dimension,
                    'index_type': self.index_type
                }, f)
            
            logger.debug("Saved FAISS index and metadata")
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    async def _load_index(self):
        """Load FAISS index and metadata from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.id_to_index = data['id_to_index']
                self.dimension = data['dimension']
                self.index_type = data['index_type']
            
            logger.debug("Loaded FAISS index and metadata")
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise
    
    async def cleanup(self):
        """Clean up FAISS resources"""
        if self.index is not None:
            await self._save_index()
        
        self.index = None
        self.metadata = []
        self.id_to_index = {}
        await super().cleanup()