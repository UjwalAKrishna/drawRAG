"""
Plugin Configuration Schemas - Schema definitions for all plugin types
"""

from typing import Dict, Any


class PluginSchemas:
    """Centralized schema definitions for plugin configurations"""
    
    @staticmethod
    def get_sqlite_schema() -> Dict[str, Any]:
        return {
            "database_path": {"type": "string", "required": True, "description": "Path to SQLite database file"},
            "table_name": {"type": "string", "required": True, "description": "Table name to query"},
            "text_column": {"type": "string", "required": True, "description": "Column containing text data"}
        }
    
    @staticmethod
    def get_upload_schema() -> Dict[str, Any]:
        return {
            "file_types": {"type": "array", "items": {"type": "string"}, "description": "Allowed file types"},
            "max_size": {"type": "string", "description": "Maximum file size"}
        }
    
    @staticmethod
    def get_postgres_schema() -> Dict[str, Any]:
        return {
            "host": {"type": "string", "required": True, "description": "PostgreSQL host"},
            "port": {"type": "integer", "required": True, "description": "PostgreSQL port"},
            "database": {"type": "string", "required": True, "description": "Database name"},
            "username": {"type": "string", "required": True, "description": "Username"},
            "password": {"type": "string", "required": True, "description": "Password"},
            "table_name": {"type": "string", "required": True, "description": "Table name to query"},
            "text_column": {"type": "string", "required": True, "description": "Column containing text data"}
        }
    
    @staticmethod
    def get_chroma_schema() -> Dict[str, Any]:
        return {
            "collection_name": {"type": "string", "required": True, "description": "Collection name"},
            "persist_directory": {"type": "string", "description": "Directory to persist data"}
        }
    
    @staticmethod
    def get_faiss_schema() -> Dict[str, Any]:
        return {
            "index_type": {"type": "string", "enum": ["flat", "ivf"], "description": "FAISS index type"},
            "dimension": {"type": "integer", "required": True, "description": "Vector dimension"}
        }
    
    @staticmethod
    def get_pinecone_schema() -> Dict[str, Any]:
        return {
            "api_key": {"type": "string", "required": True, "description": "Pinecone API key"},
            "environment": {"type": "string", "required": True, "description": "Pinecone environment"},
            "index_name": {"type": "string", "required": True, "description": "Index name"},
            "dimension": {"type": "integer", "description": "Vector dimension"},
            "metric": {"type": "string", "enum": ["cosine", "euclidean", "dotproduct"], "description": "Distance metric"}
        }
    
    @staticmethod
    def get_openai_schema() -> Dict[str, Any]:
        return {
            "api_key": {"type": "string", "required": True, "description": "OpenAI API key"},
            "model": {"type": "string", "enum": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], "description": "Model to use"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "description": "Sampling temperature"},
            "max_tokens": {"type": "integer", "minimum": 1, "description": "Maximum tokens to generate"}
        }
    
    @staticmethod
    def get_ollama_schema() -> Dict[str, Any]:
        return {
            "base_url": {"type": "string", "description": "Ollama server URL"},
            "model": {"type": "string", "required": True, "description": "Model name"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "description": "Sampling temperature"}
        }
    
    @staticmethod
    def get_anthropic_schema() -> Dict[str, Any]:
        return {
            "api_key": {"type": "string", "required": True, "description": "Anthropic API key"},
            "model": {"type": "string", "enum": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], "description": "Model to use"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "description": "Sampling temperature"},
            "max_tokens": {"type": "integer", "minimum": 1, "description": "Maximum tokens to generate"}
        }
    
    @staticmethod
    def get_mysql_schema() -> Dict[str, Any]:
        return {
            "host": {"type": "string", "required": True, "description": "MySQL host"},
            "port": {"type": "integer", "required": True, "description": "MySQL port"},
            "database": {"type": "string", "required": True, "description": "Database name"},
            "username": {"type": "string", "required": True, "description": "Username"},
            "password": {"type": "string", "required": True, "description": "Password"},
            "table_name": {"type": "string", "required": True, "description": "Table name to query"},
            "text_column": {"type": "string", "required": True, "description": "Column containing text data"}
        }
    
    @staticmethod
    def get_weaviate_schema() -> Dict[str, Any]:
        return {
            "url": {"type": "string", "required": True, "description": "Weaviate instance URL"},
            "api_key": {"type": "string", "description": "API key (if required)"},
            "class_name": {"type": "string", "required": True, "description": "Weaviate class name"},
            "text_property": {"type": "string", "required": True, "description": "Text property name"}
        }
    
    @staticmethod
    def get_schema_for_plugin(plugin_type: str, subtype: str) -> Dict[str, Any]:
        """Get schema for a specific plugin type and subtype"""
        schema_map = {
            ("datasource", "sqlite"): PluginSchemas.get_sqlite_schema,
            ("datasource", "upload"): PluginSchemas.get_upload_schema,
            ("datasource", "postgres"): PluginSchemas.get_postgres_schema,
            ("datasource", "mysql"): PluginSchemas.get_mysql_schema,
            ("vectordb", "chroma"): PluginSchemas.get_chroma_schema,
            ("vectordb", "faiss"): PluginSchemas.get_faiss_schema,
            ("vectordb", "pinecone"): PluginSchemas.get_pinecone_schema,
            ("vectordb", "weaviate"): PluginSchemas.get_weaviate_schema,
            ("llm", "openai"): PluginSchemas.get_openai_schema,
            ("llm", "ollama"): PluginSchemas.get_ollama_schema,
            ("llm", "anthropic"): PluginSchemas.get_anthropic_schema,
        }
        
        schema_func = schema_map.get((plugin_type, subtype))
        if schema_func:
            return schema_func()
        
        return {}
    
    @staticmethod
    def validate_config_against_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration against schema"""
        errors = []
        
        # Check required fields
        for field_name, field_schema in schema.items():
            if field_schema.get("required", False):
                if field_name not in config or not config[field_name]:
                    errors.append(f"Required field '{field_name}' is missing")
        
        # Check field types and constraints
        for field_name, value in config.items():
            if field_name in schema:
                field_schema = schema[field_name]
                
                # Type validation
                expected_type = field_schema.get("type")
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{field_name}' must be a string")
                elif expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Field '{field_name}' must be an integer")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field_name}' must be a number")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{field_name}' must be an array")
                
                # Enum validation
                if "enum" in field_schema and value not in field_schema["enum"]:
                    errors.append(f"Field '{field_name}' must be one of: {field_schema['enum']}")
                
                # Range validation for numbers
                if expected_type in ["number", "integer"]:
                    if "minimum" in field_schema and value < field_schema["minimum"]:
                        errors.append(f"Field '{field_name}' must be >= {field_schema['minimum']}")
                    if "maximum" in field_schema and value > field_schema["maximum"]:
                        errors.append(f"Field '{field_name}' must be <= {field_schema['maximum']}")
        
        return len(errors) == 0, errors