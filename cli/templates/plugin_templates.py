"""
Plugin Code Templates
"""

from typing import Dict, Any


class PluginTemplates:
    """Generate plugin code templates"""
    
    def get_main_template(self, plugin_type: str, name: str, template_type: str = "basic") -> str:
        """Get main plugin file template"""
        class_name = self._to_pascal_case(name)
        
        if plugin_type == "datasource":
            return self._get_datasource_template(class_name)
        elif plugin_type == "vectordb":
            return self._get_vectordb_template(class_name)
        elif plugin_type == "llm":
            return self._get_llm_template(class_name)
        elif plugin_type == "utility":
            return self._get_utility_template(class_name)
        else:
            return self._get_base_template(class_name)
    
    def _get_datasource_template(self, class_name: str) -> str:
        return f'''"""
{class_name} DataSource Plugin
"""

import logging
from typing import Dict, List, Any
from rag_builder_sdk import BaseDataSourcePlugin

logger = logging.getLogger(__name__)


class {class_name}Plugin(BaseDataSourcePlugin):
    """Custom DataSource plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        required_fields = ["connection_string", "table_name"]
        return all(field in config and config[field] for field in required_fields)
    
    async def initialize(self) -> bool:
        """Initialize the data source connection"""
        try:
            # TODO: Implement your connection logic here
            connection_string = self.config["connection_string"]
            logger.info(f"Connecting to data source: {{connection_string}}")
            
            # Example: self.connection = create_connection(connection_string)
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize data source: {{e}}")
            return False
    
    async def get_documents(self) -> List[Dict[str, Any]]:
        """Retrieve documents from the data source"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # TODO: Implement your document retrieval logic here
            table_name = self.config["table_name"]
            logger.info(f"Retrieving documents from table: {{table_name}}")
            
            # Example implementation:
            documents = [
                {{
                    "id": "doc_1",
                    "content": "Sample document content",
                    "metadata": {{"source": table_name}}
                }}
            ]
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {{e}}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        if self.connection:
            # TODO: Close your connection here
            pass
        self.initialized = False


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> {class_name}Plugin:
    """Create plugin instance"""
    return {class_name}Plugin(config)
'''
    
    def _get_vectordb_template(self, class_name: str) -> str:
        return f'''"""
{class_name} VectorDB Plugin
"""

import logging
from typing import Dict, List, Any
from rag_builder_sdk import BaseVectorDBPlugin

logger = logging.getLogger(__name__)


class {class_name}Plugin(BaseVectorDBPlugin):
    """Custom VectorDB plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.collection = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        required_fields = ["collection_name", "dimension"]
        return all(field in config and config[field] for field in required_fields)
    
    async def initialize(self) -> bool:
        """Initialize the vector database connection"""
        try:
            # TODO: Implement your vector DB initialization here
            collection_name = self.config["collection_name"]
            dimension = self.config["dimension"]
            
            logger.info(f"Initializing vector collection: {{collection_name}} (dim={{dimension}})")
            
            # Example: self.client = create_client()
            # Example: self.collection = self.client.get_collection(collection_name)
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {{e}}")
            return False
    
    async def store_vectors(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """Store document vectors in the database"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # TODO: Implement your vector storage logic here
            logger.info(f"Storing {{len(documents)}} vectors")
            
            # Example implementation:
            for doc, embedding in zip(documents, embeddings):
                # Store vector with metadata
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store vectors: {{e}}")
            return False
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query similar vectors"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # TODO: Implement your vector query logic here
            logger.info(f"Querying vectors (top_k={{top_k}})")
            
            # Example implementation:
            results = [
                {{
                    "id": "result_1",
                    "content": "Similar document content",
                    "score": 0.95,
                    "metadata": {{"source": "vector_db"}}
                }}
            ]
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query vectors: {{e}}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            # TODO: Close your client connection here
            pass
        self.initialized = False


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> {class_name}Plugin:
    """Create plugin instance"""
    return {class_name}Plugin(config)
'''
    
    def _get_llm_template(self, class_name: str) -> str:
        return f'''"""
{class_name} LLM Plugin
"""

import logging
from typing import Dict, List, Any
from rag_builder_sdk import BaseLLMPlugin

logger = logging.getLogger(__name__)


class {class_name}Plugin(BaseLLMPlugin):
    """Custom LLM plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        required_fields = ["api_key", "model"]
        return all(field in config and config[field] for field in required_fields)
    
    async def initialize(self) -> bool:
        """Initialize the LLM client"""
        try:
            # TODO: Implement your LLM client initialization here
            api_key = self.config["api_key"]
            model = self.config["model"]
            
            logger.info(f"Initializing LLM client with model: {{model}}")
            
            # Example: self.client = create_llm_client(api_key)
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {{e}}")
            return False
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate text response"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # TODO: Implement your text generation logic here
            model = self.config["model"]
            temperature = self.config.get("temperature", 0.7)
            
            logger.info(f"Generating response with model: {{model}}")
            
            # Combine context and prompt
            full_prompt = f"Context: {{context}}\\n\\nQuestion: {{prompt}}"
            
            # Example implementation:
            response = f"Generated response for: {{prompt[:50]}}..."
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {{e}}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate text embeddings"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # TODO: Implement your embedding generation logic here
            logger.info(f"Generating embeddings for {{len(texts)}} texts")
            
            # Example implementation:
            embeddings = []
            for text in texts:
                # Generate embedding vector (example: 384 dimensions)
                embedding = [0.0] * 384  # Replace with actual embedding
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {{e}}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            # TODO: Close your client connection here
            pass
        self.initialized = False


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> {class_name}Plugin:
    """Create plugin instance"""
    return {class_name}Plugin(config)
'''
    
    def _get_utility_template(self, class_name: str) -> str:
        return f'''"""
{class_name} Utility Plugin
"""

import logging
from typing import Dict, List, Any
from rag_builder_sdk import BasePlugin

logger = logging.getLogger(__name__)


class {class_name}Plugin(BasePlugin):
    """Custom Utility plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        return "enabled" in config
    
    async def initialize(self) -> bool:
        """Initialize the utility plugin"""
        try:
            # TODO: Implement your initialization logic here
            enabled = self.config.get("enabled", True)
            
            if not enabled:
                logger.info("Plugin is disabled")
                return False
            
            logger.info("Initializing utility plugin")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize utility: {{e}}")
            return False
    
    async def process_data(self, data: Any) -> Any:
        """Process data through the utility"""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        try:
            # TODO: Implement your data processing logic here
            logger.info("Processing data through utility")
            
            # Example processing
            processed_data = data  # Replace with actual processing
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to process data: {{e}}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        self.initialized = False


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> {class_name}Plugin:
    """Create plugin instance"""
    return {class_name}Plugin(config)
'''
    
    def _get_base_template(self, class_name: str) -> str:
        return f'''"""
{class_name} Plugin
"""

import logging
from typing import Dict, Any
from rag_builder_sdk import BasePlugin

logger = logging.getLogger(__name__)


class {class_name}Plugin(BasePlugin):
    """Custom plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        # TODO: Implement your validation logic here
        return True
    
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # TODO: Implement your initialization logic here
            logger.info("Initializing plugin")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {{e}}")
            return False
    
    async def cleanup(self):
        """Clean up resources"""
        self.initialized = False


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> {class_name}Plugin:
    """Create plugin instance"""
    return {class_name}Plugin(config)
'''
    
    def get_init_template(self, name: str) -> str:
        """Get __init__.py template"""
        class_name = self._to_pascal_case(name)
        return f'''"""
{name.replace("-", " ").title()} Plugin Package
"""

from .{name.replace("-", "_")}_plugin import {class_name}Plugin, create_plugin

__version__ = "1.0.0"
__all__ = ["{class_name}Plugin", "create_plugin"]
'''
    
    def get_test_template(self, plugin_type: str, name: str) -> str:
        """Get test file template"""
        class_name = self._to_pascal_case(name)
        return f'''"""
Tests for {class_name} Plugin
"""

import pytest
import asyncio
from src.{name.replace("-", "_")}_plugin import {class_name}Plugin


class Test{class_name}Plugin:
    """Test cases for {class_name} plugin"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = self._get_test_config()
        self.plugin = {class_name}Plugin(self.config)
    
    def _get_test_config(self):
        """Get test configuration"""
        # TODO: Return appropriate test configuration
        return {{}}
    
    @pytest.mark.asyncio
    async def test_validate_config(self):
        """Test configuration validation"""
        assert await self.plugin.validate_config(self.config)
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test plugin initialization"""
        result = await self.plugin.initialize()
        assert result is True
        assert self.plugin.initialized is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test plugin cleanup"""
        await self.plugin.initialize()
        await self.plugin.cleanup()
        assert self.plugin.initialized is False
    
    # TODO: Add more specific tests for your plugin type
'''
    
    def get_requirements_template(self, plugin_type: str) -> str:
        """Get requirements.txt template"""
        base_requirements = ["rag-builder-sdk>=1.0.0"]
        
        type_requirements = {
            "datasource": ["sqlalchemy", "pandas"],
            "vectordb": ["numpy", "faiss-cpu"],
            "llm": ["openai", "tiktoken"],
            "utility": []
        }
        
        requirements = base_requirements + type_requirements.get(plugin_type, [])
        return "\\n".join(requirements) + "\\n"
    
    def get_readme_template(self, name: str, plugin_type: str, description: str) -> str:
        """Get README.md template"""
        title = name.replace("-", " ").title()
        return f'''# {title}

{description}

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

```yaml
{name}:
  # TODO: Add configuration options
```

## Usage

```python
from {name.replace("-", "_")}_plugin import create_plugin

# Create plugin instance
plugin = create_plugin(config)

# Initialize plugin
await plugin.initialize()

# Use plugin functionality
# TODO: Add usage examples

# Cleanup
await plugin.cleanup()
```

## Development

### Testing

```bash
rag-plugin test
```

### Building

```bash
rag-plugin build
```

## License

MIT License
'''
    
    def get_setup_template(self, name: str, plugin_type: str, author: str, description: str) -> str:
        """Get setup.py template"""
        class_name = self._to_pascal_case(name)
        return f'''"""
Setup script for {name} plugin
"""

from setuptools import setup, find_packages

setup(
    name="{name}",
    version="1.0.0",
    description="{description}",
    author="{author}",
    packages=find_packages(),
    install_requires=[
        "rag-builder-sdk>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    entry_points={{
        "rag_builder.plugins": [
            "{name} = src.{name.replace('-', '_')}_plugin:{class_name}Plugin"
        ]
    }}
)
'''
    
    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case or kebab-case to PascalCase"""
        return ''.join(word.capitalize() for word in snake_str.replace('-', '_').split('_'))