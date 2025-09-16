# 🐍 SDK Reference

Complete Python SDK documentation for RAG Builder v2.0 plugin development.

## 📦 Installation

The SDK is included with RAG Builder:

```bash
# Install RAG Builder
pip install -r requirements.txt

# SDK is automatically available
from sdk.base_plugin import BasePlugin
from sdk.llm_plugin import LLMPlugin
from sdk.data_source_plugin import DataSourcePlugin
from sdk.vector_db_plugin import VectorDBPlugin
```

## 🏗️ Core Classes

### `BasePlugin`

Base class for all RAG Builder plugins.

```python
from sdk.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    """Base plugin implementation."""
    
    def __init__(self):
        super().__init__()
        # Plugin initialization code
    
    def capability_function(self, param: str) -> str:
        """Any method becomes a capability."""
        return f"Processed: {param}"
```

#### Methods

##### `__init__(self)`
Initialize the plugin instance.

```python
def __init__(self):
    super().__init__()
    self.config = self.load_config()
    self.initialized = True
```

##### `get_capabilities(self) -> List[str]`
Get list of available capabilities (methods) in the plugin.

```python
capabilities = plugin.get_capabilities()
# Returns: ['capability_function', 'another_method']
```

##### `validate_input(self, data: Any) -> bool`
Validate input data before processing.

```python
def validate_input(self, data: str) -> bool:
    return isinstance(data, str) and len(data) > 0
```

##### `handle_error(self, error: Exception) -> dict`
Custom error handling for the plugin.

```python
def handle_error(self, error: Exception) -> dict:
    return {
        'error': str(error),
        'type': type(error).__name__,
        'recoverable': True
    }
```

#### Properties

##### `name: str`
Plugin name (automatically derived from class name).

##### `version: str`
Plugin version (default: "1.0.0").

##### `description: str`
Plugin description for documentation.

### `LLMPlugin`

Specialized base class for Language Model plugins.

```python
from sdk.llm_plugin import LLMPlugin

class MyLLMPlugin(LLMPlugin):
    """LLM plugin for text generation."""
    
    def __init__(self):
        super().__init__()
        self.model = self.load_model()
    
    def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """Generate text from prompt."""
        return self.model.generate(prompt, max_length=max_length)
    
    def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of text."""
        return {
            'sentiment': 'positive',
            'confidence': 0.95
        }
```

#### Methods

##### `load_model(self) -> Any`
Load the language model. Override in subclasses.

```python
def load_model(self):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    model_name = "gpt2"
    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    return AutoModelForCausalLM.from_pretrained(model_name)
```

##### `preprocess_text(self, text: str) -> str`
Preprocess text before model input.

```python
def preprocess_text(self, text: str) -> str:
    return text.strip().lower()
```

##### `postprocess_output(self, output: str) -> str`
Postprocess model output.

```python
def postprocess_output(self, output: str) -> str:
    return output.strip()
```

#### Properties

##### `model_name: str`
Name of the loaded model.

##### `model_type: str`
Type of model (e.g., "causal_lm", "sequence_classification").

### `DataSourcePlugin`

Base class for data source and retrieval plugins.

```python
from sdk.data_source_plugin import DataSourcePlugin

class MyDataSource(DataSourcePlugin):
    """Database connection plugin."""
    
    def __init__(self):
        super().__init__()
        self.connection = self.connect()
    
    def connect(self) -> Any:
        """Establish connection to data source."""
        import sqlite3
        return sqlite3.connect("database.db")
    
    def query(self, sql: str) -> List[dict]:
        """Execute SQL query."""
        cursor = self.connection.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    
    def fetch_documents(self, filter_criteria: dict) -> List[dict]:
        """Fetch documents based on criteria."""
        # Implementation specific to data source
        pass
```

#### Methods

##### `connect(self) -> Any`
Establish connection to the data source.

##### `disconnect(self)`
Close connection to the data source.

```python
def disconnect(self):
    if hasattr(self, 'connection') and self.connection:
        self.connection.close()
```

##### `test_connection(self) -> bool`
Test if connection is active.

```python
def test_connection(self) -> bool:
    try:
        # Test connection with simple query
        self.query("SELECT 1")
        return True
    except:
        return False
```

#### Properties

##### `connection_string: str`
Connection string for the data source.

##### `is_connected: bool`
Whether the plugin is connected to the data source.

### `VectorDBPlugin`

Base class for vector database plugins.

```python
from sdk.vector_db_plugin import VectorDBPlugin
import numpy as np

class MyVectorDB(VectorDBPlugin):
    """Vector database plugin for similarity search."""
    
    def __init__(self):
        super().__init__()
        self.index = self.initialize_index()
    
    def initialize_index(self) -> Any:
        """Initialize vector index."""
        # Implementation depends on vector DB
        pass
    
    def add_vectors(self, vectors: List[List[float]], metadata: List[dict] = None):
        """Add vectors to the index."""
        for i, vector in enumerate(vectors):
            meta = metadata[i] if metadata else {}
            self.index.add(vector, meta)
    
    def search(self, query_vector: List[float], k: int = 5) -> List[dict]:
        """Search for similar vectors."""
        results = self.index.search(query_vector, k)
        return [
            {
                'vector': result.vector,
                'distance': result.distance,
                'metadata': result.metadata
            }
            for result in results
        ]
    
    def embed_text(self, text: str) -> List[float]:
        """Convert text to vector embedding."""
        # Use embedding model
        return self.embedding_model.encode(text).tolist()
```

#### Methods

##### `add_vectors(self, vectors: List[List[float]], metadata: List[dict] = None)`
Add vectors to the index with optional metadata.

##### `search(self, query_vector: List[float], k: int = 5) -> List[dict]`
Search for k most similar vectors.

##### `delete_vectors(self, ids: List[str])`
Delete vectors by their IDs.

##### `update_vector(self, id: str, vector: List[float], metadata: dict = None)`
Update an existing vector.

#### Properties

##### `dimension: int`
Dimension of vectors in the index.

##### `index_size: int`
Number of vectors in the index.

## 🛠️ Utility Classes

### `PluginConfig`

Configuration management for plugins.

```python
from sdk.config import PluginConfig

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.config = PluginConfig(
            config_file="my_plugin_config.yaml",
            defaults={
                'max_retries': 3,
                'timeout': 30,
                'debug': False
            }
        )
    
    def process(self, data: str) -> str:
        max_retries = self.config.get('max_retries')
        timeout = self.config.get('timeout')
        # Use configuration values
```

#### Methods

##### `get(self, key: str, default: Any = None) -> Any`
Get configuration value.

##### `set(self, key: str, value: Any)`
Set configuration value.

##### `load_from_file(self, file_path: str)`
Load configuration from file.

##### `save_to_file(self, file_path: str)`
Save configuration to file.

### `PluginLogger`

Logging utility for plugins.

```python
from sdk.logger import PluginLogger

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.logger = PluginLogger(name=self.__class__.__name__)
    
    def process(self, data: str) -> str:
        self.logger.info(f"Processing data: {len(data)} characters")
        
        try:
            result = self.expensive_operation(data)
            self.logger.debug(f"Operation completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            raise
```

#### Methods

##### `debug(self, message: str)`
Log debug message.

##### `info(self, message: str)`
Log info message.

##### `warning(self, message: str)`
Log warning message.

##### `error(self, message: str)`
Log error message.

##### `critical(self, message: str)`
Log critical message.

### `PluginCache`

Caching utility for plugins.

```python
from sdk.cache import PluginCache

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.cache = PluginCache(
            max_size=1000,
            ttl=3600  # 1 hour
        )
    
    @PluginCache.cached(ttl=1800)
    def expensive_computation(self, input_data: str) -> str:
        """This method's results are automatically cached."""
        # Expensive computation
        return result
    
    def get_cached_result(self, key: str) -> Any:
        return self.cache.get(key)
    
    def set_cache(self, key: str, value: Any, ttl: int = None):
        self.cache.set(key, value, ttl)
```

#### Methods

##### `get(self, key: str) -> Any`
Get value from cache.

##### `set(self, key: str, value: Any, ttl: int = None)`
Set value in cache.

##### `delete(self, key: str)`
Delete value from cache.

##### `clear(self)`
Clear all cached values.

##### `@cached(ttl: int = None)`
Decorator for automatic method caching.

## 🔧 Decorators

### `@capability`

Mark methods as plugin capabilities.

```python
from sdk.decorators import capability

class MyPlugin(BasePlugin):
    @capability(
        description="Process text input",
        parameters={
            'text': {'type': 'str', 'description': 'Input text'},
            'uppercase': {'type': 'bool', 'default': False}
        },
        returns={'type': 'str', 'description': 'Processed text'}
    )
    def process_text(self, text: str, uppercase: bool = False) -> str:
        result = text.strip()
        return result.upper() if uppercase else result.lower()
```

### `@validate_input`

Validate input parameters.

```python
from sdk.decorators import validate_input

class MyPlugin(BasePlugin):
    @validate_input({
        'text': {'type': str, 'min_length': 1, 'max_length': 1000},
        'count': {'type': int, 'min': 1, 'max': 100}
    })
    def process_multiple(self, text: str, count: int) -> List[str]:
        return [f"{text}_{i}" for i in range(count)]
```

### `@retry`

Automatic retry on failure.

```python
from sdk.decorators import retry

class MyPlugin(BasePlugin):
    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    def unreliable_operation(self, data: str) -> str:
        # This will retry up to 3 times with exponential backoff
        return self.external_api_call(data)
```

### `@timeout`

Set execution timeout.

```python
from sdk.decorators import timeout

class MyPlugin(BasePlugin):
    @timeout(30)  # 30 seconds timeout
    def long_running_task(self, data: str) -> str:
        # Will raise TimeoutError if execution takes longer than 30 seconds
        return self.process_large_dataset(data)
```

## 📊 Examples

### Simple Text Processing Plugin

```python
from sdk.base_plugin import BasePlugin
from sdk.decorators import capability, validate_input

class TextProcessor(BasePlugin):
    """Simple text processing plugin."""
    
    def __init__(self):
        super().__init__()
        self.name = "text_processor"
        self.version = "1.0.0"
        self.description = "Basic text processing utilities"
    
    @capability(description="Clean and normalize text")
    @validate_input({'text': {'type': str, 'min_length': 1}})
    def clean_text(self, text: str) -> str:
        """Remove extra whitespace and normalize case."""
        return text.strip().lower()
    
    @capability(description="Count words in text")
    def count_words(self, text: str) -> int:
        """Count the number of words."""
        return len(text.split())
    
    @capability(description="Extract keywords from text")
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract top keywords from text."""
        words = text.lower().split()
        # Simple keyword extraction (remove stop words, etc.)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
        keywords = [word for word in words if word not in stop_words]
        return list(set(keywords))[:max_keywords]
```

### LLM Integration Plugin

```python
from sdk.llm_plugin import LLMPlugin
from sdk.decorators import capability, retry, timeout

class SmartLLM(LLMPlugin):
    """Advanced LLM plugin with multiple capabilities."""
    
    def __init__(self):
        super().__init__()
        self.name = "smart_llm"
        self.model_name = "gpt-3.5-turbo"
    
    def load_model(self):
        # Initialize your LLM client
        import openai
        return openai.OpenAI(api_key=self.config.get('api_key'))
    
    @capability(description="Generate text from prompt")
    @timeout(30)
    @retry(max_attempts=2)
    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """Generate text using LLM."""
        response = self.model.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    @capability(description="Summarize long text")
    def summarize(self, text: str, max_length: int = 150) -> str:
        """Create a summary of the input text."""
        prompt = f"Summarize this text in {max_length} words or less:\n\n{text}"
        return self.generate_text(prompt, max_tokens=max_length)
    
    @capability(description="Analyze sentiment")
    def analyze_sentiment(self, text: str) -> dict:
        """Analyze the sentiment of text."""
        prompt = f"Analyze the sentiment of this text. Respond with just 'positive', 'negative', or 'neutral':\n\n{text}"
        sentiment = self.generate_text(prompt, max_tokens=10).strip().lower()
        
        return {
            'sentiment': sentiment,
            'confidence': 0.9 if sentiment in ['positive', 'negative', 'neutral'] else 0.5
        }
```

### Data Source Plugin

```python
from sdk.data_source_plugin import DataSourcePlugin
from sdk.decorators import capability
import sqlite3
import pandas as pd

class DatabaseConnector(DataSourcePlugin):
    """SQLite database connector plugin."""
    
    def __init__(self):
        super().__init__()
        self.name = "database_connector"
        self.db_path = self.config.get('database_path', 'data.db')
    
    def connect(self):
        """Connect to SQLite database."""
        return sqlite3.connect(self.db_path)
    
    @capability(description="Execute SQL query")
    def query(self, sql: str) -> List[dict]:
        """Execute SQL query and return results."""
        try:
            df = pd.read_sql_query(sql, self.connection)
            return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise
    
    @capability(description="Get table schema")
    def get_schema(self, table_name: str) -> List[dict]:
        """Get schema information for a table."""
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        return [
            {
                'name': col[1],
                'type': col[2],
                'nullable': not col[3],
                'primary_key': bool(col[5])
            }
            for col in columns
        ]
    
    @capability(description="List all tables")
    def list_tables(self) -> List[str]:
        """Get list of all tables in database."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
```

## 🚀 Advanced Features

### Plugin Lifecycle Hooks

```python
class AdvancedPlugin(BasePlugin):
    def on_load(self):
        """Called when plugin is loaded."""
        self.logger.info("Plugin loaded successfully")
        self.initialize_resources()
    
    def on_unload(self):
        """Called when plugin is unloaded."""
        self.cleanup_resources()
        self.logger.info("Plugin unloaded")
    
    def on_error(self, error: Exception):
        """Called when plugin encounters an error."""
        self.logger.error(f"Plugin error: {error}")
        # Send alert, cleanup, etc.
```

### Custom Validation

```python
from sdk.validation import ValidationRule

class CustomPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        
        # Define custom validation rules
        self.validation_rules = {
            'email_validation': ValidationRule(
                lambda x: '@' in x and '.' in x,
                "Must be a valid email address"
            ),
            'positive_number': ValidationRule(
                lambda x: isinstance(x, (int, float)) and x > 0,
                "Must be a positive number"
            )
        }
    
    @validate_input({
        'email': 'email_validation',
        'score': 'positive_number'
    })
    def process_user_data(self, email: str, score: float) -> dict:
        return {'email': email, 'score': score, 'processed': True}
```

---

This SDK reference provides comprehensive documentation for building powerful, production-ready plugins with RAG Builder v2.0. Use these classes and utilities to create robust, scalable plugins for your RAG applications.