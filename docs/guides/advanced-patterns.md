# 🎯 Advanced Plugin Patterns

Advanced techniques and patterns for building sophisticated RAG Builder plugins.

## 🏗️ Architectural Patterns

### 1. **Plugin Composition Pattern**

Build complex functionality by combining simpler plugins.

```python
# Component plugins
class TextCleaner(BasePlugin):
    def clean(self, text: str) -> str:
        return text.strip().lower()

class TextAnalyzer(BasePlugin):
    def analyze(self, text: str) -> dict:
        return {
            'word_count': len(text.split()),
            'char_count': len(text),
            'language': 'en'  # simplified
        }

# Composite plugin
class TextProcessor(BasePlugin):
    def __init__(self):
        super().__init__()
        self.cleaner = TextCleaner()
        self.analyzer = TextAnalyzer()
    
    def process_document(self, text: str) -> dict:
        """Complete document processing pipeline."""
        # Step 1: Clean text
        cleaned = self.cleaner.clean(text)
        
        # Step 2: Analyze text
        analysis = self.analyzer.analyze(cleaned)
        
        # Step 3: Combine results
        return {
            'original': text,
            'cleaned': cleaned,
            'analysis': analysis,
            'processed_at': datetime.utcnow().isoformat()
        }
```

### 2. **Plugin Factory Pattern**

Dynamically create plugins based on configuration or runtime conditions.

```python
from abc import ABC, abstractmethod

class LLMPlugin(BasePlugin, ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class OpenAIPlugin(LLMPlugin):
    def __init__(self, model: str = "gpt-3.5-turbo"):
        super().__init__()
        self.model = model
        self.client = openai.OpenAI()
    
    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class HuggingFacePlugin(LLMPlugin):
    def __init__(self, model: str = "gpt2"):
        super().__init__()
        from transformers import pipeline
        self.generator = pipeline('text-generation', model=model)
    
    def generate(self, prompt: str) -> str:
        result = self.generator(prompt, max_length=100, num_return_sequences=1)
        return result[0]['generated_text']

# Plugin Factory
class LLMPluginFactory:
    _plugins = {
        'openai': OpenAIPlugin,
        'huggingface': HuggingFacePlugin
    }
    
    @classmethod
    def create_plugin(cls, provider: str, **kwargs) -> LLMPlugin:
        if provider not in cls._plugins:
            raise ValueError(f"Unknown LLM provider: {provider}")
        
        plugin_class = cls._plugins[provider]
        return plugin_class(**kwargs)
    
    @classmethod
    def register_plugin(cls, name: str, plugin_class: type):
        cls._plugins[name] = plugin_class

# Usage
class SmartLLMRouter(BasePlugin):
    def __init__(self):
        super().__init__()
        self.factory = LLMPluginFactory()
        self.plugins = {}
    
    def generate_with_provider(self, prompt: str, provider: str = "openai") -> str:
        if provider not in self.plugins:
            self.plugins[provider] = self.factory.create_plugin(provider)
        
        return self.plugins[provider].generate(prompt)
```

### 3. **Pipeline Pattern**

Chain multiple processing steps together with flexible ordering.

```python
from typing import Callable, List, Any

class ProcessingStep:
    def __init__(self, name: str, function: Callable, **kwargs):
        self.name = name
        self.function = function
        self.kwargs = kwargs
    
    def execute(self, data: Any) -> Any:
        return self.function(data, **self.kwargs)

class ProcessingPipeline(BasePlugin):
    def __init__(self):
        super().__init__()
        self.steps: List[ProcessingStep] = []
    
    def add_step(self, name: str, function: Callable, **kwargs):
        """Add a processing step to the pipeline."""
        step = ProcessingStep(name, function, **kwargs)
        self.steps.append(step)
        return self
    
    def remove_step(self, name: str):
        """Remove a step from the pipeline."""
        self.steps = [step for step in self.steps if step.name != name]
        return self
    
    def execute_pipeline(self, data: Any) -> dict:
        """Execute the complete pipeline."""
        results = {'input': data, 'steps': []}
        current_data = data
        
        for step in self.steps:
            try:
                step_result = step.execute(current_data)
                results['steps'].append({
                    'name': step.name,
                    'success': True,
                    'output': step_result
                })
                current_data = step_result
            except Exception as e:
                results['steps'].append({
                    'name': step.name,
                    'success': False,
                    'error': str(e)
                })
                break  # Stop pipeline on error
        
        results['final_output'] = current_data
        return results

# Example usage
class DocumentProcessor(ProcessingPipeline):
    def __init__(self):
        super().__init__()
        
        # Build processing pipeline
        self.add_step('clean', self.clean_text) \
            .add_step('tokenize', self.tokenize_text) \
            .add_step('analyze', self.analyze_tokens) \
            .add_step('summarize', self.create_summary)
    
    def clean_text(self, text: str) -> str:
        return text.strip().lower()
    
    def tokenize_text(self, text: str) -> List[str]:
        return text.split()
    
    def analyze_tokens(self, tokens: List[str]) -> dict:
        return {
            'token_count': len(tokens),
            'unique_tokens': len(set(tokens)),
            'avg_length': sum(len(token) for token in tokens) / len(tokens)
        }
    
    def create_summary(self, analysis: dict) -> str:
        return f"Document contains {analysis['token_count']} tokens"
```

## 🔄 Asynchronous Patterns

### 1. **Async Plugin with Concurrent Processing**

```python
import asyncio
import aiohttp
from typing import List

class AsyncWebScraper(BasePlugin):
    def __init__(self):
        super().__init__()
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> dict:
        """Fetch content from a single URL."""
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                return {
                    'url': url,
                    'status': response.status,
                    'content': content[:1000],  # First 1000 chars
                    'length': len(content)
                }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status': None
            }
    
    async def fetch_multiple_urls(self, urls: List[str], max_concurrent: int = 10) -> List[dict]:
        """Fetch content from multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url: str):
            async with semaphore:
                return await self.fetch_url(url)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)
        
        return processed_results

# Synchronous wrapper for async plugin
class WebScraperWrapper(BasePlugin):
    def __init__(self):
        super().__init__()
        self.async_scraper = AsyncWebScraper()
    
    def scrape_urls(self, urls: List[str]) -> List[dict]:
        """Synchronous interface for async scraping."""
        async def run_scraping():
            async with self.async_scraper as scraper:
                return await scraper.fetch_multiple_urls(urls)
        
        return asyncio.run(run_scraping())
```

### 2. **Background Task Pattern**

```python
import threading
import queue
from typing import Optional

class BackgroundProcessor(BasePlugin):
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.result_store = {}
        self.worker_thread = None
        self.running = False
    
    def start_worker(self):
        """Start background worker thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def stop_worker(self):
        """Stop background worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _worker_loop(self):
        """Main worker loop."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:  # Sentinel to stop
                    break
                
                task_id, func, args, kwargs = task
                try:
                    result = func(*args, **kwargs)
                    self.result_store[task_id] = {
                        'status': 'completed',
                        'result': result
                    }
                except Exception as e:
                    self.result_store[task_id] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                self.task_queue.task_done()
            
            except queue.Empty:
                continue
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background processing."""
        task_id = str(uuid.uuid4())
        
        if not self.running:
            self.start_worker()
        
        self.task_queue.put((task_id, func, args, kwargs))
        
        # Initialize result entry
        self.result_store[task_id] = {'status': 'pending'}
        
        return task_id
    
    def get_result(self, task_id: str) -> Optional[dict]:
        """Get result of a background task."""
        return self.result_store.get(task_id)
    
    def wait_for_result(self, task_id: str, timeout: int = 30) -> Optional[dict]:
        """Wait for task completion with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_result(task_id)
            if result and result['status'] != 'pending':
                return result
            time.sleep(0.1)
        
        return None
    
    # High-level interface methods
    def process_large_dataset(self, dataset: List[dict]) -> str:
        """Process large dataset in background."""
        def heavy_processing(data):
            # Simulate heavy processing
            time.sleep(2)
            return {'processed_count': len(data), 'summary': 'completed'}
        
        return self.submit_task(heavy_processing, dataset)
```

## 🔌 Plugin Communication Patterns

### 1. **Event-Driven Plugin System**

```python
from typing import Dict, List, Callable
from enum import Enum

class EventType(Enum):
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    DATA_PROCESSED = "data_processed"
    ERROR_OCCURRED = "error_occurred"

class EventBus:
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)
    
    def emit(self, event_type: EventType, data: dict):
        """Emit an event to all subscribers."""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in event callback: {e}")

# Event-aware base plugin
class EventDrivenPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()
    
    def on_plugin_loaded(self, data: dict):
        """Handle plugin loaded event."""
        pass
    
    def on_data_processed(self, data: dict):
        """Handle data processed event."""
        pass
    
    def setup_event_listeners(self):
        """Setup event listeners."""
        self.event_bus.subscribe(EventType.PLUGIN_LOADED, self.on_plugin_loaded)
        self.event_bus.subscribe(EventType.DATA_PROCESSED, self.on_data_processed)

# Example event-driven plugins
class DataProcessor(EventDrivenPlugin):
    def process_data(self, data: dict) -> dict:
        result = {'processed': True, 'data': data}
        
        # Emit event after processing
        self.event_bus.emit(EventType.DATA_PROCESSED, {
            'plugin': self.name,
            'input': data,
            'output': result
        })
        
        return result

class DataLogger(EventDrivenPlugin):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.setup_event_listeners()
    
    def on_data_processed(self, event_data: dict):
        """Log data processing events."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'plugin': event_data['plugin'],
            'input_size': len(str(event_data['input'])),
            'output_size': len(str(event_data['output']))
        }
        self.logs.append(log_entry)
    
    def get_processing_stats(self) -> dict:
        return {
            'total_events': len(self.logs),
            'plugins': list(set(log['plugin'] for log in self.logs)),
            'latest_events': self.logs[-10:]  # Last 10 events
        }
```

### 2. **Plugin Registry Pattern**

```python
class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.capabilities: Dict[str, str] = {}  # capability -> plugin_name
    
    def register_plugin(self, plugin: BasePlugin):
        """Register a plugin and its capabilities."""
        plugin_name = plugin.name or plugin.__class__.__name__
        self.plugins[plugin_name] = plugin
        
        # Register capabilities
        for capability in plugin.get_capabilities():
            self.capabilities[capability] = plugin_name
    
    def unregister_plugin(self, plugin_name: str):
        """Unregister a plugin."""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            
            # Remove capabilities
            for capability in plugin.get_capabilities():
                if capability in self.capabilities:
                    del self.capabilities[capability]
            
            del self.plugins[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get plugin by name."""
        return self.plugins.get(plugin_name)
    
    def get_plugin_for_capability(self, capability: str) -> Optional[BasePlugin]:
        """Get plugin that provides a specific capability."""
        plugin_name = self.capabilities.get(capability)
        return self.plugins.get(plugin_name) if plugin_name else None
    
    def call_capability(self, capability: str, *args, **kwargs):
        """Call a capability by name."""
        plugin = self.get_plugin_for_capability(capability)
        if not plugin:
            raise ValueError(f"No plugin found for capability: {capability}")
        
        method = getattr(plugin, capability)
        return method(*args, **kwargs)

# Plugin that uses the registry
class PluginOrchestrator(BasePlugin):
    def __init__(self):
        super().__init__()
        self.registry = PluginRegistry()
    
    def execute_workflow(self, workflow_config: dict) -> dict:
        """Execute a multi-step workflow using registered plugins."""
        results = {}
        
        for step in workflow_config['steps']:
            step_name = step['name']
            capability = step['capability']
            args = step.get('args', [])
            kwargs = step.get('kwargs', {})
            
            try:
                result = self.registry.call_capability(capability, *args, **kwargs)
                results[step_name] = {
                    'success': True,
                    'result': result
                }
            except Exception as e:
                results[step_name] = {
                    'success': False,
                    'error': str(e)
                }
                if workflow_config.get('fail_fast', True):
                    break
        
        return results
```

## 🎯 Specialized Plugin Patterns

### 1. **Caching Plugin with Multiple Strategies**

```python
from abc import ABC, abstractmethod
import redis
import pickle

class CacheStrategy(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None):
        pass
    
    @abstractmethod
    def delete(self, key: str):
        pass

class MemoryCache(CacheStrategy):
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        entry = self.cache.get(key)
        if entry and (entry['expires'] is None or time.time() < entry['expires']):
            return entry['value']
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        if len(self.cache) >= self.max_size:
            # Simple LRU eviction
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['accessed'])
            del self.cache[oldest_key]
        
        expires = time.time() + ttl if ttl else None
        self.cache[key] = {
            'value': value,
            'expires': expires,
            'accessed': time.time()
        }
    
    def delete(self, key: str):
        self.cache.pop(key, None)

class RedisCache(CacheStrategy):
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)
    
    def get(self, key: str) -> Optional[Any]:
        data = self.redis_client.get(key)
        return pickle.loads(data) if data else None
    
    def set(self, key: str, value: Any, ttl: int = None):
        data = pickle.dumps(value)
        self.redis_client.set(key, data, ex=ttl)
    
    def delete(self, key: str):
        self.redis_client.delete(key)

class SmartCachePlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.strategies = {
            'memory': MemoryCache(max_size=500),
            'redis': RedisCache()
        }
        self.default_strategy = 'memory'
    
    def get_cached(self, key: str, strategy: str = None) -> Optional[Any]:
        """Get value from cache using specified strategy."""
        strategy = strategy or self.default_strategy
        cache = self.strategies.get(strategy)
        return cache.get(key) if cache else None
    
    def set_cached(self, key: str, value: Any, ttl: int = None, strategy: str = None):
        """Set value in cache using specified strategy."""
        strategy = strategy or self.default_strategy
        cache = self.strategies.get(strategy)
        if cache:
            cache.set(key, value, ttl)
    
    def cached_computation(self, computation_key: str, computation_func: Callable, 
                          *args, ttl: int = 3600, strategy: str = None, **kwargs):
        """Execute computation with caching."""
        # Check cache first
        cached_result = self.get_cached(computation_key, strategy)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache result
        result = computation_func(*args, **kwargs)
        self.set_cached(computation_key, result, ttl, strategy)
        
        return result
```

### 2. **Configuration-Driven Plugin**

```python
import yaml
from typing import Union

class ConfigurablePlugin(BasePlugin):
    def __init__(self, config_path: str = None):
        super().__init__()
        self.config_path = config_path
        self.config = self.load_configuration()
        self.setup_from_config()
    
    def load_configuration(self) -> dict:
        """Load configuration from file or environment."""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        
        # Default configuration
        return {
            'processing': {
                'batch_size': 100,
                'timeout': 30,
                'retries': 3
            },
            'output': {
                'format': 'json',
                'include_metadata': True
            },
            'features': {
                'enable_caching': True,
                'enable_logging': True,
                'enable_metrics': False
            }
        }
    
    def setup_from_config(self):
        """Setup plugin based on configuration."""
        # Setup processing parameters
        self.batch_size = self.config['processing']['batch_size']
        self.timeout = self.config['processing']['timeout']
        self.retries = self.config['processing']['retries']
        
        # Setup features
        if self.config['features']['enable_caching']:
            self.cache = PluginCache()
        
        if self.config['features']['enable_logging']:
            self.logger = PluginLogger(self.__class__.__name__)
        
        if self.config['features']['enable_metrics']:
            self.metrics = PluginMetrics()
    
    def update_config(self, config_updates: dict):
        """Update configuration at runtime."""
        def update_nested_dict(d, updates):
            for key, value in updates.items():
                if isinstance(value, dict) and key in d:
                    update_nested_dict(d[key], value)
                else:
                    d[key] = value
        
        update_nested_dict(self.config, config_updates)
        self.setup_from_config()
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

# Example usage
class DataProcessorPlugin(ConfigurablePlugin):
    def process_batch(self, data: List[dict]) -> List[dict]:
        """Process data in configurable batches."""
        results = []
        batch_size = self.batch_size
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            if hasattr(self, 'logger'):
                self.logger.info(f"Processing batch {i//batch_size + 1}")
            
            # Process batch with retry logic
            for attempt in range(self.retries):
                try:
                    batch_results = self._process_single_batch(batch)
                    results.extend(batch_results)
                    break
                except Exception as e:
                    if attempt == self.retries - 1:
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return results
    
    def _process_single_batch(self, batch: List[dict]) -> List[dict]:
        """Process a single batch of data."""
        return [{'processed': True, **item} for item in batch]
```

---

These advanced patterns enable you to build sophisticated, maintainable, and scalable plugins for complex RAG applications. Choose the patterns that best fit your specific use cases and combine them as needed.