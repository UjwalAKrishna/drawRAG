"""
Init Command - Initialize new plugin project
"""

import os
from pathlib import Path
from typing import Dict, Any
from .base_command import BaseCommand
try:
    from ..templates import PluginTemplates
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from templates import PluginTemplates


class InitCommand(BaseCommand):
    """Initialize a new plugin project"""
    
    def execute(self, args) -> int:
        """Execute init command"""
        plugin_name = args.name
        plugin_type = args.type
        template_type = args.template
        author = args.author or "Plugin Developer"
        description = args.description or f"A {plugin_type} plugin for RAG Builder"
        
        # Validate plugin name
        if not self._is_valid_plugin_name(plugin_name):
            self.print_error("Invalid plugin name. Use lowercase letters, numbers, and hyphens only.")
            return 1
        
        # Create plugin directory
        plugin_dir = self.current_dir / plugin_name
        if plugin_dir.exists():
            self.print_error(f"Directory '{plugin_name}' already exists")
            return 1
        
        if not self.create_directory(plugin_dir):
            return 1
        
        # Generate plugin structure
        try:
            self._create_plugin_structure(
                plugin_dir, plugin_name, plugin_type, 
                template_type, author, description
            )
            
            self.print_success(f"Plugin '{plugin_name}' created successfully!")
            self.print_info(f"Directory: {plugin_dir}")
            self.print_info("Next steps:")
            print("  1. cd " + plugin_name)
            print("  2. rag-plugin validate")
            print("  3. rag-plugin test --local")
            
            return 0
            
        except Exception as e:
            self.print_error(f"Failed to create plugin: {e}")
            return 1
    
    def _is_valid_plugin_name(self, name: str) -> bool:
        """Validate plugin name"""
        import re
        return bool(re.match(r'^[a-z0-9-]+$', name))
    
    def _create_plugin_structure(self, plugin_dir: Path, name: str, plugin_type: str, 
                               template_type: str, author: str, description: str):
        """Create the plugin directory structure"""
        
        # Create manifest
        manifest = self._create_manifest(name, plugin_type, author, description)
        self.save_manifest(manifest, str(plugin_dir))
        
        # Create directory structure
        directories = [
            plugin_dir / "src",
            plugin_dir / "tests", 
            plugin_dir / "docs",
            plugin_dir / "examples"
        ]
        
        for directory in directories:
            self.create_directory(directory)
        
        # Create main plugin file
        templates = PluginTemplates()
        main_content = templates.get_main_template(plugin_type, name, template_type)
        self.write_file(plugin_dir / "src" / f"{name}_plugin.py", main_content)
        
        # Create init file
        init_content = templates.get_init_template(name)
        self.write_file(plugin_dir / "src" / "__init__.py", init_content)
        
        # Create test file
        test_content = templates.get_test_template(plugin_type, name)
        self.write_file(plugin_dir / "tests" / f"test_{name}.py", test_content)
        
        # Create requirements file
        requirements = templates.get_requirements_template(plugin_type)
        self.write_file(plugin_dir / "requirements.txt", requirements)
        
        # Create README
        readme_content = templates.get_readme_template(name, plugin_type, description)
        self.write_file(plugin_dir / "README.md", readme_content)
        
        # Create setup.py
        setup_content = templates.get_setup_template(name, plugin_type, author, description)
        self.write_file(plugin_dir / "setup.py", setup_content)
    
    def _create_manifest(self, name: str, plugin_type: str, author: str, description: str) -> Dict[str, Any]:
        """Create plugin manifest"""
        return {
            "name": name.replace("-", " ").title(),
            "key": name,
            "type": plugin_type,
            "version": "1.0.0",
            "description": description,
            "author": author,
            "entrypoint": f"src/{name}_plugin.py",
            "main_class": f"{self._to_pascal_case(name)}Plugin",
            "requirements": [
                "rag-builder-sdk"
            ],
            "config_schema": self._get_default_schema(plugin_type),
            "capabilities": self._get_default_capabilities(plugin_type),
            "tags": [plugin_type],
            "license": "MIT",
            "min_rag_version": "1.0.0",
            "python_version": ">=3.8"
        }
    
    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case or kebab-case to PascalCase"""
        return ''.join(word.capitalize() for word in snake_str.replace('-', '_').split('_'))
    
    def _get_default_schema(self, plugin_type: str) -> Dict[str, Any]:
        """Get default configuration schema for plugin type"""
        schemas = {
            "datasource": {
                "connection_string": {
                    "type": "string",
                    "required": True,
                    "description": "Database connection string"
                },
                "table_name": {
                    "type": "string", 
                    "required": True,
                    "description": "Table name to query"
                }
            },
            "vectordb": {
                "collection_name": {
                    "type": "string",
                    "required": True,
                    "description": "Collection name"
                },
                "dimension": {
                    "type": "integer",
                    "required": True,
                    "description": "Vector dimension"
                }
            },
            "llm": {
                "api_key": {
                    "type": "string",
                    "required": True,
                    "description": "API key"
                },
                "model": {
                    "type": "string",
                    "required": True,
                    "description": "Model name"
                },
                "temperature": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 2,
                    "description": "Sampling temperature"
                }
            },
            "utility": {
                "enabled": {
                    "type": "boolean",
                    "required": True,
                    "description": "Enable utility"
                }
            }
        }
        return schemas.get(plugin_type, {})
    
    def _get_default_capabilities(self, plugin_type: str) -> list:
        """Get default capabilities for plugin type"""
        capabilities = {
            "datasource": ["read_data", "query_data"],
            "vectordb": ["store_vectors", "query_vectors", "delete_vectors"],
            "llm": ["generate_text", "generate_embeddings"],
            "utility": ["process_data"]
        }
        return capabilities.get(plugin_type, [])