# 🔌 Plugin Development Guide

This comprehensive guide will teach you everything you need to know about creating plugins for RAG Builder. From your first 30-second plugin to advanced enterprise-grade implementations.

## 🚀 **Quick Start: Your First Plugin**

### **Method 1: Zero-Config Functions (30 seconds)**

The fastest way to create a plugin:

```python
# plugins/my_first_plugin.py

def greet(name: str) -> str:
    """Greet someone by name"""
    return f"Hello, {name}! Welcome to RAG Builder!"

def calculate_age(birth_year: int, current_year: int = 2024) -> int:
    """Calculate age from birth year"""
    return current_year - birth_year

def analyze_text(text: str) -> dict:
    """Basic text analysis"""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "sentences": text.count('.') + text.count('!') + text.count('?')
    }
```

**That's it!** The framework automatically:
- Discovers these functions
- Registers them as capabilities
- Makes them available via API
- Generates documentation from docstrings

### **Test Your Plugin**

```bash
# Start the framework
python run_server.py

# Test via API
curl -X POST http://localhost:8000/api/call/greet \
  -H "Content-Type: application/json" \
  -d '{"args": ["Alice"]}'

# Response: {"success": true, "result": "Hello, Alice! Welcome to RAG Builder!"}
```

### **Test via Python**

```python
from backend.core import Manager
import asyncio

async def test_plugin():
    manager = Manager()
    await manager.start()
    
    # Call your capabilities
    greeting = await manager.call("greet", "Bob")
    age = await manager.call("calculate_age", 1990)
    analysis = await manager.call("analyze_text", "Hello world! How are you?")
    
    print(f"Greeting: {greeting}")
    print(f"Age: {age}")
    print(f"Analysis: {analysis}")
    
    await manager.stop()

asyncio.run(test_plugin())
```

## 🛠️ **Plugin Development Methods**

### **Method 2: Simple Classes**

For more organized code:

```python
# plugins/text_processor.py
from rag_builder_sdk import QuickPlugin

class TextProcessorPlugin(QuickPlugin):
    """Advanced text processing capabilities"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.default_language = config.get("language", "en")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        return ' '.join(text.strip().split())
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> list:
        """Extract key words from text"""
        words = text.lower().split()
        # Simple keyword extraction (in real implementation, use NLP)
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def sentiment_score(self, text: str) -> float:
        """Simple sentiment scoring"""
        positive_words = ["good", "great", "excellent", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words
```

### **Method 3: Advanced Plugins with Decorators**

For production-grade plugins:

```python
# plugins/smart_llm.py
from rag_builder_sdk import LLMPlugin, capability, event_handler, requires, provides_schema

class SmartLLMPlugin(LLMPlugin):
    """Intelligent LLM with advanced features"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.api_key = config["api_key"]
        self.model = config.get("model", "gpt-3.5-turbo")
        self.cache = {}
        self.stats = {"requests": 0, "cache_hits": 0}
    
    @capability("Generate intelligent text responses")
    @provides_schema({
        "input": {"prompt": "string", "temperature": "number"},
        "output": {"type": "string", "description": "Generated response"}
    })
    async def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text using advanced LLM"""
        self.stats["requests"] += 1
        
        # Check cache
        cache_key = f"{prompt}_{temperature}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]
        
        # Generate response (mock implementation)
        response = f"Smart response to '{prompt}' (temp: {temperature})"
        
        # Cache response
        self.cache[cache_key] = response
        return response
    
    @capability("Get model statistics")
    def get_stats(self) -> dict:
        """Get LLM usage statistics"""
        cache_hit_rate = self.stats["cache_hits"] / max(self.stats["requests"], 1)
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "model": self.model
        }
    
    @event_handler("system_startup")
    async def on_startup(self, event_data):
        """Handle system startup"""
        print(f"🤖 Smart LLM Plugin ready with model: {self.model}")
    
    @requires("clean_text")
    @capability("Generate clean response")
    async def generate_clean_response(self, prompt: str) -> str:
        """Generate response with cleaned input"""
        # Framework automatically calls clean_text capability
        cleaned_prompt = await self.call_dependency("clean_text", prompt)
        return await self.generate_text(cleaned_prompt)
```

## 📦 **Using the CLI for Plugin Development**

### **Create New Plugin**

```bash
# Scaffold a new plugin
rag-plugin init my-awesome-plugin --type llm --author "Your Name" --description "An awesome LLM plugin"

# This creates:
my-awesome-plugin/
├── plugin.yaml          # Plugin manifest
├── src/
│   ├── __init__.py
│   └── my_awesome_plugin.py
├── tests/
│   └── test_my_awesome_plugin.py
├── README.md
├── requirements.txt
└── setup.py
```

### **Develop with Live Reload**

```bash
cd my-awesome-plugin

# Validate your plugin
rag-plugin validate

# Test locally
rag-plugin test --local

# Start development server
rag-plugin dev-server --port 8080
```

### **Build and Package**

```bash
# Build plugin package
rag-plugin build --format zip

# This creates: dist/my-awesome-plugin-1.0.0.zip
```

## 🎯 **Plugin Types & Patterns**

### **Data Source Plugins**

```python
from rag_builder_sdk import DataSourcePlugin

class DatabasePlugin(DataSourcePlugin):
    """Connect to databases and retrieve documents"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.connection_string = config["connection_string"]
        self.table_name = config["table_name"]
    
    async def get_documents(self) -> list:
        """Retrieve documents from database"""
        # Connect to database and fetch documents
        documents = [
            {"id": "1", "content": "Document 1", "metadata": {"source": "db"}},
            {"id": "2", "content": "Document 2", "metadata": {"source": "db"}}
        ]
        return documents
    
    async def search_documents(self, query: str) -> list:
        """Search documents with query"""
        # Implement database search
        return [doc for doc in await self.get_documents() if query.lower() in doc["content"].lower()]
```

### **Vector Database Plugins**

```python
from rag_builder_sdk import VectorDBPlugin

class ChromaPlugin(VectorDBPlugin):
    """ChromaDB integration"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.collection_name = config["collection_name"]
        # Initialize ChromaDB connection
    
    async def store_vectors(self, documents: list, embeddings: list) -> bool:
        """Store document vectors"""
        # Store in ChromaDB
        return True
    
    async def query_vectors(self, query_vector: list, top_k: int = 5) -> list:
        """Query similar vectors"""
        # Query ChromaDB and return results
        return [
            {"id": "1", "content": "Similar doc 1", "score": 0.95},
            {"id": "2", "content": "Similar doc 2", "score": 0.87}
        ]
```

### **Utility Plugins**

```python
from rag_builder_sdk import BasePlugin, capability

class AnalyticsPlugin(BasePlugin):
    """Analytics and monitoring utilities"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.metrics = {}
    
    @capability("Track metric")
    def track_metric(self, name: str, value: float, tags: dict = None):
        """Track a metric value"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.now(),
            "tags": tags or {}
        })
    
    @capability("Get metrics summary")
    def get_metrics_summary(self) -> dict:
        """Get summary of all metrics"""
        summary = {}
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    "count": len(values),
                    "avg": sum(v["value"] for v in values) / len(values),
                    "min": min(v["value"] for v in values),
                    "max": max(v["value"] for v in values)
                }
        return summary
```

## 🔧 **Advanced Plugin Features**

### **Plugin Dependencies**

```python
class AdvancedRAGPlugin(BasePlugin):
    """Plugin that combines multiple capabilities"""
    
    # Declare plugin dependencies
    dependencies = ["text_processor", "vector_db", "llm"]
    
    @requires("clean_text", "generate_embeddings", "store_vectors")
    async def process_documents(self, documents: list) -> dict:
        """Complete document processing pipeline"""
        processed_docs = []
        
        for doc in documents:
            # Clean text using text_processor plugin
            clean_content = await self.call_dependency("clean_text", doc["content"])
            
            # Generate embeddings using LLM plugin
            embeddings = await self.call_dependency("generate_embeddings", [clean_content])
            
            # Store in vector database
            await self.call_dependency("store_vectors", [doc], embeddings)
            
            processed_docs.append({
                "id": doc["id"],
                "original_length": len(doc["content"]),
                "cleaned_length": len(clean_content),
                "stored": True
            })
        
        return {
            "processed_count": len(processed_docs),
            "documents": processed_docs
        }
```

### **Event-Driven Plugins**

```python
class WorkflowPlugin(BasePlugin):
    """Plugin that responds to system events"""
    
    @event_handler("document_uploaded")
    async def on_document_upload(self, event_data):
        """Automatically process uploaded documents"""
        document = event_data["document"]
        
        # Process the document
        result = await self.framework.call("process_documents", [document])
        
        # Emit completion event
        await self.framework.emit("document_processed", {
            "document_id": document["id"],
            "processing_result": result
        })
    
    @event_handler("processing_error") 
    async def on_processing_error(self, event_data):
        """Handle processing errors"""
        error = event_data["error"]
        context = event_data["context"]
        
        # Log error
        logger.error(f"Processing failed: {error}")
        
        # Implement retry logic
        if context.get("retry_count", 0) < 3:
            await self.retry_processing(context)
```

### **Configuration and Validation**

```python
class ConfigurablePlugin(BasePlugin):
    """Plugin with advanced configuration"""
    
    # Configuration schema
    config_schema = {
        "api_key": {"type": "string", "required": True},
        "timeout": {"type": "integer", "default": 30, "minimum": 1},
        "retries": {"type": "integer", "default": 3, "minimum": 0},
        "model": {"type": "string", "enum": ["gpt-3.5", "gpt-4"], "default": "gpt-3.5"}
    }
    
    def __init__(self, **config):
        super().__init__(**config)
        
        # Validate configuration
        self.validate_config(config)
        
        # Set up with validated config
        self.api_key = config["api_key"]
        self.timeout = config.get("timeout", 30)
        self.retries = config.get("retries", 3)
        self.model = config.get("model", "gpt-3.5")
    
    def validate_config(self, config: dict) -> bool:
        """Validate plugin configuration"""
        schema = self.config_schema
        
        # Check required fields
        for field, spec in schema.items():
            if spec.get("required", False) and field not in config:
                raise ValueError(f"Required field '{field}' missing")
        
        # Validate types and constraints
        for field, value in config.items():
            if field in schema:
                spec = schema[field]
                
                # Type validation
                if spec["type"] == "string" and not isinstance(value, str):
                    raise ValueError(f"Field '{field}' must be string")
                elif spec["type"] == "integer" and not isinstance(value, int):
                    raise ValueError(f"Field '{field}' must be integer")
                
                # Constraint validation
                if "minimum" in spec and value < spec["minimum"]:
                    raise ValueError(f"Field '{field}' must be >= {spec['minimum']}")
                if "enum" in spec and value not in spec["enum"]:
                    raise ValueError(f"Field '{field}' must be one of {spec['enum']}")
        
        return True
```

## 📊 **Testing Your Plugins**

### **Unit Testing**

```python
# tests/test_my_plugin.py
import pytest
import asyncio
from src.my_plugin import MyPlugin

@pytest.mark.asyncio
async def test_plugin_initialization():
    """Test plugin initializes correctly"""
    config = {"api_key": "test_key", "model": "test_model"}
    plugin = MyPlugin(**config)
    
    assert plugin.api_key == "test_key"
    assert plugin.model == "test_model"
    
    # Test initialization
    success = await plugin.initialize()
    assert success is True

@pytest.mark.asyncio  
async def test_capability_execution():
    """Test plugin capabilities work correctly"""
    plugin = MyPlugin(api_key="test")
    await plugin.initialize()
    
    # Test capability
    result = await plugin.execute_capability("generate_text", "Hello world")
    assert isinstance(result, str)
    assert len(result) > 0
    
    await plugin.cleanup()

def test_plugin_configuration():
    """Test plugin configuration validation"""
    # Valid config should work
    valid_config = {"api_key": "test", "timeout": 30}
    plugin = MyPlugin(**valid_config)
    assert plugin.validate_config(valid_config)
    
    # Invalid config should raise error
    invalid_config = {"timeout": "not_an_integer"}
    with pytest.raises(ValueError):
        MyPlugin(**invalid_config)
```

### **Integration Testing**

```python
# tests/test_integration.py
import pytest
from backend.core import Manager

@pytest.mark.asyncio
async def test_plugin_integration():
    """Test plugin works with framework"""
    manager = Manager("plugins")
    await manager.start()
    
    # Test plugin is loaded
    plugins = manager.list_plugins()
    assert "my_plugin" in plugins
    
    # Test capabilities are available
    capabilities = manager.list_capabilities()
    assert "generate_text" in capabilities
    
    # Test capability execution
    result = await manager.call("generate_text", "Test prompt")
    assert isinstance(result, str)
    
    await manager.stop()
```

## 🚀 **Best Practices**

### **1. Error Handling**

```python
@capability("Safe text processing")
async def process_text_safely(self, text: str) -> dict:
    """Process text with comprehensive error handling"""
    try:
        # Validate input
        if not text or not isinstance(text, str):
            return {"error": "Invalid input: text must be non-empty string"}
        
        # Process text
        result = await self.expensive_processing(text)
        
        return {"success": True, "result": result}
        
    except ConnectionError as e:
        logger.error(f"Connection failed: {e}")
        return {"error": "Service temporarily unavailable", "retry": True}
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"error": f"Invalid input: {str(e)}", "retry": False}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": "Internal processing error", "retry": True}
```

### **2. Performance Optimization**

```python
class OptimizedPlugin(BasePlugin):
    """Plugin with performance optimizations"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.cache = {}
        self.connection_pool = self.create_connection_pool()
    
    @capability("Optimized processing")
    async def optimized_process(self, data: str) -> str:
        """Process data with caching and connection pooling"""
        
        # Check cache first
        cache_key = self.generate_cache_key(data)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Use connection pool for database operations
        async with self.connection_pool.acquire() as connection:
            result = await self.process_with_connection(connection, data)
        
        # Cache result
        self.cache[cache_key] = result
        
        # Limit cache size
        if len(self.cache) > 1000:
            self.cleanup_cache()
        
        return result
```

### **3. Resource Management**

```python
class ResourceManagedPlugin(BasePlugin):
    """Plugin with proper resource management"""
    
    async def initialize(self) -> bool:
        """Initialize resources"""
        try:
            self.connection = await self.create_connection()
            self.thread_pool = ThreadPoolExecutor(max_workers=4)
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources properly"""
        if hasattr(self, 'connection'):
            await self.connection.close()
        
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)
        
        # Clear any caches
        if hasattr(self, 'cache'):
            self.cache.clear()
```

---

This guide covers everything you need to know about plugin development for RAG Builder. Start with simple functions, progress to advanced patterns, and always follow best practices for production-ready plugins.