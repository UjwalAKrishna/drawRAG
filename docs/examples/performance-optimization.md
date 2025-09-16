# ⚡ Performance Optimization Examples

Practical examples and techniques for optimizing RAG Builder performance in production environments.

## 🚀 Plugin Performance Optimization

### 1. **Efficient Data Processing Plugin**

```python
# plugins/optimized_processor.py

import numpy as np
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any, Iterator
from functools import lru_cache
from sdk.base_plugin import BasePlugin

class OptimizedProcessor(BasePlugin):
    """High-performance data processing plugin."""
    
    def __init__(self):
        super().__init__()
        self.batch_size = 1000
        self.num_workers = mp.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.num_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.num_workers)
    
    def batch_process(self, items: List[Any], batch_size: int = None) -> Iterator[List[Any]]:
        """Process items in batches for memory efficiency."""
        batch_size = batch_size or self.batch_size
        
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    def parallel_process_threads(self, items: List[str], process_func) -> List[Any]:
        """Process items in parallel using threads (I/O bound tasks)."""
        futures = []
        
        for batch in self.batch_process(items):
            future = self.thread_pool.submit(self._process_batch, batch, process_func)
            futures.append(future)
        
        results = []
        for future in futures:
            results.extend(future.result())
        
        return results
    
    def parallel_process_multiprocessing(self, items: List[str], process_func) -> List[Any]:
        """Process items in parallel using processes (CPU bound tasks)."""
        futures = []
        
        for batch in self.batch_process(items):
            future = self.process_pool.submit(self._process_batch, batch, process_func)
            futures.append(future)
        
        results = []
        for future in futures:
            results.extend(future.result())
        
        return results
    
    @staticmethod
    def _process_batch(batch: List[str], process_func) -> List[Any]:
        """Process a single batch of items."""
        return [process_func(item) for item in batch]
    
    @lru_cache(maxsize=10000)
    def cached_computation(self, input_data: str) -> str:
        """Expensive computation with LRU caching."""
        # Simulate expensive operation
        import time
        time.sleep(0.01)  # Remove in production
        return f"processed_{input_data}"
    
    def vectorized_operations(self, numbers: List[float]) -> Dict[str, float]:
        """Use NumPy for vectorized operations."""
        arr = np.array(numbers)
        
        return {
            'sum': np.sum(arr),
            'mean': np.mean(arr),
            'std': np.std(arr),
            'min': np.min(arr),
            'max': np.max(arr)
        }
    
    def memory_efficient_processing(self, large_dataset: Iterator[Dict]) -> Iterator[Dict]:
        """Process large datasets without loading everything into memory."""
        for item in large_dataset:
            # Process one item at a time
            processed = self.process_single_item(item)
            yield processed
    
    def process_single_item(self, item: Dict) -> Dict:
        """Process a single item efficiently."""
        # Avoid creating unnecessary copies
        result = item.copy()  # Only copy if needed
        result['processed'] = True
        return result
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)
        if hasattr(self, 'process_pool'):
            self.process_pool.shutdown(wait=True)
```

### 2. **Optimized Vector Search Plugin**

```python
# plugins/optimized_vector_search.py

import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
from sdk.vector_db_plugin import VectorDBPlugin

class OptimizedVectorSearch(VectorDBPlugin):
    """High-performance vector search using FAISS."""
    
    def __init__(self):
        super().__init__()
        self.dimension = 768
        self.index = None
        self.id_map = {}
        self.metadata_store = {}
        self.index_type = "IVF"  # IVF, HNSW, or Flat
        
    def initialize_index(self):
        """Initialize FAISS index for optimal performance."""
        if self.index_type == "IVF":
            # Inverted File Index - good for large datasets
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            
        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World - fast approximate search
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            self.index.hnsw.efConstruction = 40
            self.index.hnsw.efSearch = 16
            
        elif self.index_type == "Flat":
            # Exact search - best accuracy, slower for large datasets
            self.index = faiss.IndexFlatIP(self.dimension)
        
        return self.index
    
    def add_vectors_batch(self, vectors: np.ndarray, ids: List[str], 
                         metadata: List[Dict[str, Any]]) -> bool:
        """Add vectors in batches for better performance."""
        if self.index is None:
            self.initialize_index()
        
        # Ensure vectors are normalized for cosine similarity
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        
        # Train index if needed (for IVF)
        if self.index_type == "IVF" and not self.index.is_trained:
            if len(vectors) >= 100:  # Need enough vectors to train
                self.index.train(vectors)
            else:
                # Use a subset for training
                training_vectors = np.random.random((1000, self.dimension)).astype('float32')
                self.index.train(training_vectors)
        
        # Add vectors to index
        start_id = len(self.id_map)
        self.index.add(vectors)
        
        # Update ID mapping and metadata
        for i, (doc_id, meta) in enumerate(zip(ids, metadata)):
            internal_id = start_id + i
            self.id_map[doc_id] = internal_id
            self.metadata_store[internal_id] = meta
        
        return True
    
    def search_optimized(self, query_vector: np.ndarray, k: int = 10, 
                        threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Optimized vector search with filtering."""
        if self.index is None:
            return []
        
        # Normalize query vector
        query_vector = query_vector / np.linalg.norm(query_vector)
        query_vector = query_vector.reshape(1, -1)
        
        # Search with extra candidates for filtering
        search_k = min(k * 2, self.index.ntotal)
        distances, indices = self.index.search(query_vector, search_k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # No more results
                break
            
            similarity = float(distance)  # FAISS returns cosine similarity for IP index
            
            if similarity >= threshold:
                metadata = self.metadata_store.get(idx, {})
                results.append({
                    'index': int(idx),
                    'similarity': similarity,
                    'metadata': metadata
                })
            
            if len(results) >= k:
                break
        
        return results
    
    def build_optimized_index(self, vectors: np.ndarray, 
                             nlist: int = None) -> faiss.Index:
        """Build optimized index for production use."""
        n_vectors, dimension = vectors.shape
        
        if n_vectors < 1000:
            # Use flat index for small datasets
            index = faiss.IndexFlatIP(dimension)
        elif n_vectors < 100000:
            # Use IVF for medium datasets
            nlist = nlist or min(int(np.sqrt(n_vectors)), 1000)
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        else:
            # Use IVF with PQ for large datasets
            nlist = nlist or int(np.sqrt(n_vectors))
            m = 8  # Number of sub-quantizers
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, 8)
        
        # Add GPU support if available
        if faiss.get_num_gpus() > 0:
            index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
        
        return index
    
    def save_index(self, file_path: str) -> bool:
        """Save index to disk."""
        try:
            faiss.write_index(self.index, file_path)
            
            # Save metadata separately
            import pickle
            metadata_path = file_path.replace('.index', '_metadata.pkl')
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'id_map': self.id_map,
                    'metadata_store': self.metadata_store
                }, f)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving index: {str(e)}")
            return False
    
    def load_index(self, file_path: str) -> bool:
        """Load index from disk."""
        try:
            self.index = faiss.read_index(file_path)
            
            # Load metadata
            import pickle
            metadata_path = file_path.replace('.index', '_metadata.pkl')
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.id_map = data['id_map']
                self.metadata_store = data['metadata_store']
            
            return True
        except Exception as e:
            self.logger.error(f"Error loading index: {str(e)}")
            return False
```

### 3. **Async Processing Plugin**

```python
# plugins/async_processor.py

import asyncio
import aiohttp
import aiofiles
from typing import List, Dict, Any, AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from sdk.base_plugin import BasePlugin

class AsyncProcessor(BasePlugin):
    """Asynchronous processing plugin for I/O bound tasks."""
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_url_async(self, url: str) -> Dict[str, Any]:
        """Fetch URL asynchronously with rate limiting."""
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    content = await response.text()
                    return {
                        'url': url,
                        'status': response.status,
                        'content_length': len(content),
                        'content': content[:1000]  # First 1000 chars
                    }
            except Exception as e:
                return {
                    'url': url,
                    'error': str(e),
                    'status': None
                }
    
    async def fetch_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple URLs concurrently."""
        tasks = [self.fetch_url_async(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def process_files_async(self, file_paths: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """Process files asynchronously."""
        for file_path in file_paths:
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    
                yield {
                    'file_path': file_path,
                    'content_length': len(content),
                    'processed': True
                }
            except Exception as e:
                yield {
                    'file_path': file_path,
                    'error': str(e),
                    'processed': False
                }
    
    async def cpu_bound_async(self, data: List[Any]) -> List[Any]:
        """Handle CPU-bound tasks asynchronously using thread pool."""
        loop = asyncio.get_event_loop()
        
        # Split data into chunks for parallel processing
        chunk_size = len(data) // 4 if len(data) > 4 else len(data)
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        # Process chunks in thread pool
        tasks = [
            loop.run_in_executor(self.thread_pool, self._process_chunk, chunk)
            for chunk in chunks
        ]
        
        chunk_results = await asyncio.gather(*tasks)
        
        # Flatten results
        results = []
        for chunk_result in chunk_results:
            results.extend(chunk_result)
        
        return results
    
    def _process_chunk(self, chunk: List[Any]) -> List[Any]:
        """Process a chunk of data (CPU-intensive)."""
        return [self._expensive_computation(item) for item in chunk]
    
    def _expensive_computation(self, item: Any) -> Any:
        """Simulate expensive computation."""
        # Replace with actual computation
        return f"processed_{item}"
    
    async def streaming_process(self, data_stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
        """Process streaming data asynchronously."""
        async for item in data_stream:
            # Process item
            processed_item = await self._async_process_item(item)
            yield processed_item
    
    async def _async_process_item(self, item: Any) -> Any:
        """Process a single item asynchronously."""
        # Simulate async processing
        await asyncio.sleep(0.001)  # Remove in production
        return f"async_processed_{item}"
```

## 📊 Caching Strategies

### 4. **Multi-Level Cache Plugin**

```python
# plugins/advanced_cache.py

import redis
import pickle
import time
import hashlib
from typing import Any, Optional, Dict, Union
from functools import wraps
from sdk.base_plugin import BasePlugin

class MultiLevelCache(BasePlugin):
    """Advanced multi-level caching system."""
    
    def __init__(self):
        super().__init__()
        # Level 1: In-memory cache (fastest)
        self.memory_cache = {}
        self.memory_access_times = {}
        self.max_memory_items = 1000
        
        # Level 2: Redis cache (fast, persistent)
        self.redis_client = None
        self.redis_ttl = 3600  # 1 hour
        
        # Level 3: Disk cache (slower, large capacity)
        self.disk_cache_dir = "./cache/"
        self.disk_ttl = 86400  # 24 hours
        
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
        except:
            self.redis_client = None
    
    def _generate_key(self, key: str) -> str:
        """Generate consistent cache key."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        cache_key = self._generate_key(key)
        
        # Level 1: Memory cache
        if cache_key in self.memory_cache:
            self.memory_access_times[cache_key] = time.time()
            return self.memory_cache[cache_key]
        
        # Level 2: Redis cache
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if value:
                    deserialized = pickle.loads(value)
                    # Promote to memory cache
                    self._set_memory_cache(cache_key, deserialized)
                    return deserialized
            except:
                pass
        
        # Level 3: Disk cache
        try:
            disk_path = f"{self.disk_cache_dir}/{cache_key}.pkl"
            if os.path.exists(disk_path):
                with open(disk_path, 'rb') as f:
                    value = pickle.load(f)
                    # Promote to higher levels
                    self._set_memory_cache(cache_key, value)
                    if self.redis_client:
                        self._set_redis_cache(cache_key, value)
                    return value
        except:
            pass
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache levels."""
        cache_key = self._generate_key(key)
        
        # Set in all levels
        self._set_memory_cache(cache_key, value)
        
        if self.redis_client:
            self._set_redis_cache(cache_key, value, ttl or self.redis_ttl)
        
        self._set_disk_cache(cache_key, value)
        
        return True
    
    def _set_memory_cache(self, key: str, value: Any):
        """Set value in memory cache with LRU eviction."""
        if len(self.memory_cache) >= self.max_memory_items:
            # LRU eviction
            oldest_key = min(self.memory_access_times, 
                           key=self.memory_access_times.get)
            del self.memory_cache[oldest_key]
            del self.memory_access_times[oldest_key]
        
        self.memory_cache[key] = value
        self.memory_access_times[key] = time.time()
    
    def _set_redis_cache(self, key: str, value: Any, ttl: int):
        """Set value in Redis cache."""
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
        except:
            pass
    
    def _set_disk_cache(self, key: str, value: Any):
        """Set value in disk cache."""
        try:
            import os
            os.makedirs(self.disk_cache_dir, exist_ok=True)
            
            disk_path = f"{self.disk_cache_dir}/{key}.pkl"
            with open(disk_path, 'wb') as f:
                pickle.dump(value, f)
        except:
            pass
    
    def cached(self, ttl: int = 3600, key_func=None):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash((args, tuple(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Compute and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries."""
        if pattern:
            # Pattern-based invalidation
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
                del self.memory_access_times[key]
        else:
            # Clear all
            self.memory_cache.clear()
            self.memory_access_times.clear()
        
        # Clear Redis if available
        if self.redis_client and not pattern:
            try:
                self.redis_client.flushdb()
            except:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max': self.max_memory_items,
            'redis_available': self.redis_client is not None,
            'disk_cache_dir': self.disk_cache_dir
        }
```

This performance optimization guide provides practical, production-ready techniques for maximizing RAG Builder performance across different scenarios and workloads.