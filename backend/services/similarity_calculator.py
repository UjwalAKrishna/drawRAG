"""
Similarity Calculator - Handles vector similarity calculations
"""

import logging
from typing import List, Dict, Any
import math

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """Calculates similarity between vectors and performs vector operations"""
    
    def __init__(self):
        pass
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance between two vectors"""
        if len(vec1) != len(vec2):
            return float('inf')
        
        return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5
    
    def manhattan_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Manhattan distance between two vectors"""
        if len(vec1) != len(vec2):
            return float('inf')
        
        return sum(abs(a - b) for a, b in zip(vec1, vec2))
    
    def dot_product(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate dot product of two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        return sum(a * b for a, b in zip(vec1, vec2))
    
    def similarity_search(self, query_embedding: List[float], document_embeddings: List[List[float]], 
                         metric: str = "cosine", top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search between query and document embeddings"""
        try:
            similarities = []
            
            for i, doc_embedding in enumerate(document_embeddings):
                if metric == "cosine":
                    score = self.cosine_similarity(query_embedding, doc_embedding)
                elif metric == "euclidean":
                    # Convert distance to similarity (closer = higher score)
                    distance = self.euclidean_distance(query_embedding, doc_embedding)
                    score = 1.0 / (1.0 + distance)
                elif metric == "manhattan":
                    # Convert distance to similarity (closer = higher score)
                    distance = self.manhattan_distance(query_embedding, doc_embedding)
                    score = 1.0 / (1.0 + distance)
                elif metric == "dot_product":
                    score = self.dot_product(query_embedding, doc_embedding)
                else:
                    # Default to cosine
                    score = self.cosine_similarity(query_embedding, doc_embedding)
                
                similarities.append({
                    "index": i,
                    "similarity": score,
                    "metric": metric
                })
            
            # Sort by similarity (descending for similarity scores)
            if metric in ["cosine", "dot_product"]:
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
            else:
                # For distance metrics, lower is better
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def batch_similarity(self, query_embeddings: List[List[float]], document_embeddings: List[List[float]], 
                        metric: str = "cosine") -> List[List[float]]:
        """Calculate similarity matrix between multiple queries and documents"""
        similarity_matrix = []
        
        for query_emb in query_embeddings:
            query_similarities = []
            for doc_emb in document_embeddings:
                if metric == "cosine":
                    sim = self.cosine_similarity(query_emb, doc_emb)
                elif metric == "euclidean":
                    distance = self.euclidean_distance(query_emb, doc_emb)
                    sim = 1.0 / (1.0 + distance)
                elif metric == "manhattan":
                    distance = self.manhattan_distance(query_emb, doc_emb)
                    sim = 1.0 / (1.0 + distance)
                else:
                    sim = self.cosine_similarity(query_emb, doc_emb)
                
                query_similarities.append(sim)
            
            similarity_matrix.append(query_similarities)
        
        return similarity_matrix
    
    def find_most_similar_pairs(self, embeddings: List[List[float]], threshold: float = 0.8, 
                               metric: str = "cosine") -> List[Dict[str, Any]]:
        """Find pairs of embeddings that are highly similar"""
        similar_pairs = []
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                if metric == "cosine":
                    similarity = self.cosine_similarity(embeddings[i], embeddings[j])
                elif metric == "euclidean":
                    distance = self.euclidean_distance(embeddings[i], embeddings[j])
                    similarity = 1.0 / (1.0 + distance)
                else:
                    similarity = self.cosine_similarity(embeddings[i], embeddings[j])
                
                if similarity >= threshold:
                    similar_pairs.append({
                        "index1": i,
                        "index2": j,
                        "similarity": similarity,
                        "metric": metric
                    })
        
        # Sort by similarity (descending)
        similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_pairs
    
    def cluster_embeddings(self, embeddings: List[List[float]], num_clusters: int = 5, 
                          metric: str = "cosine") -> Dict[str, Any]:
        """Simple clustering of embeddings using similarity"""
        if len(embeddings) <= num_clusters:
            # Each embedding is its own cluster
            return {
                "clusters": [[i] for i in range(len(embeddings))],
                "centroids": embeddings,
                "num_clusters": len(embeddings)
            }
        
        # Simple k-means-like clustering
        import random
        random.seed(42)  # For reproducibility
        
        # Initialize centroids randomly
        centroid_indices = random.sample(range(len(embeddings)), num_clusters)
        centroids = [embeddings[i] for i in centroid_indices]
        
        clusters = [[] for _ in range(num_clusters)]
        
        # Assign each embedding to nearest centroid
        for i, embedding in enumerate(embeddings):
            best_cluster = 0
            best_similarity = -1.0
            
            for j, centroid in enumerate(centroids):
                if metric == "cosine":
                    similarity = self.cosine_similarity(embedding, centroid)
                else:
                    distance = self.euclidean_distance(embedding, centroid)
                    similarity = 1.0 / (1.0 + distance)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = j
            
            clusters[best_cluster].append(i)
        
        return {
            "clusters": clusters,
            "centroids": centroids,
            "num_clusters": len([c for c in clusters if c])  # Non-empty clusters
        }
    
    def calculate_embedding_stats(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """Calculate statistics about a set of embeddings"""
        if not embeddings:
            return {"error": "No embeddings provided"}
        
        dimension = len(embeddings[0])
        if not all(len(emb) == dimension for emb in embeddings):
            return {"error": "Inconsistent embedding dimensions"}
        
        # Calculate mean and std for each dimension
        means = [sum(emb[i] for emb in embeddings) / len(embeddings) for i in range(dimension)]
        
        variances = [
            sum((emb[i] - means[i]) ** 2 for emb in embeddings) / len(embeddings)
            for i in range(dimension)
        ]
        stds = [var ** 0.5 for var in variances]
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        return {
            "num_embeddings": len(embeddings),
            "dimension": dimension,
            "mean_values": means[:5],  # First 5 dimensions only
            "std_values": stds[:5],   # First 5 dimensions only
            "average_pairwise_similarity": avg_similarity,
            "min_similarity": min(similarities) if similarities else 0.0,
            "max_similarity": max(similarities) if similarities else 0.0
        }