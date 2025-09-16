"""
Validate Command - Validate plugin configuration and code
"""

import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Any
from .base_command import BaseCommand


class ValidateCommand(BaseCommand):
    """Validate plugin configuration and code"""
    
    def execute(self, args) -> int:
        """Execute validate command"""
        plugin_path = args.path
        strict_mode = args.strict
        
        self.print_info(f"Validating plugin at: {plugin_path}")
        
        errors = []
        warnings = []
        
        # Validate manifest
        manifest_errors, manifest_warnings = self._validate_manifest(plugin_path, strict_mode)
        errors.extend(manifest_errors)
        warnings.extend(manifest_warnings)
        
        # Validate code structure
        code_errors, code_warnings = self._validate_code_structure(plugin_path, strict_mode)
        errors.extend(code_errors)
        warnings.extend(code_warnings)
        
        # Validate Python syntax
        syntax_errors = self._validate_python_syntax(plugin_path)
        errors.extend(syntax_errors)
        
        # Print results
        if errors:
            self.print_error("Validation failed with errors:")
            for error in errors:
                print(f"  ❌ {error}")
        
        if warnings:
            self.print_warning("Validation warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        
        if not errors and not warnings:
            self.print_success("Plugin validation passed!")
        elif not errors:
            self.print_success("Plugin validation passed with warnings")
        
        return 1 if errors else 0
    
    def _validate_manifest(self, path: str, strict: bool) -> tuple[List[str], List[str]]:
        """Validate plugin manifest"""
        errors = []
        warnings = []
        
        manifest = self.load_manifest(path)
        if not manifest:
            errors.append("No valid plugin manifest found (plugin.yaml/plugin.json)")
            return errors, warnings
        
        # Required fields
        required_fields = ["name", "type", "version", "entrypoint", "main_class"]
        for field in required_fields:
            if field not in manifest:
                errors.append(f"Missing required field in manifest: {field}")
        
        # Validate plugin type
        valid_types = ["datasource", "vectordb", "llm", "utility"]
        if "type" in manifest and manifest["type"] not in valid_types:
            errors.append(f"Invalid plugin type: {manifest['type']}. Must be one of: {valid_types}")
        
        # Validate version format
        if "version" in manifest:
            if not self._is_valid_version(manifest["version"]):
                errors.append(f"Invalid version format: {manifest['version']}. Use semantic versioning (x.y.z)")
        
        # Validate entrypoint exists
        if "entrypoint" in manifest:
            entrypoint_path = Path(path) / manifest["entrypoint"]
            if not entrypoint_path.exists():
                errors.append(f"Entrypoint file not found: {manifest['entrypoint']}")
        
        # Strict mode validations
        if strict:
            recommended_fields = ["description", "author", "license", "config_schema"]
            for field in recommended_fields:
                if field not in manifest:
                    warnings.append(f"Recommended field missing from manifest: {field}")
        
        return errors, warnings
    
    def _validate_code_structure(self, path: str, strict: bool) -> tuple[List[str], List[str]]:
        """Validate plugin code structure"""
        errors = []
        warnings = []
        
        plugin_dir = Path(path)
        
        # Check for required directories
        required_dirs = ["src"]
        for dir_name in required_dirs:
            if not (plugin_dir / dir_name).exists():
                errors.append(f"Required directory missing: {dir_name}")
        
        # Check for recommended files
        recommended_files = ["README.md", "requirements.txt", "setup.py"]
        for file_name in recommended_files:
            if not (plugin_dir / file_name).exists():
                warnings.append(f"Recommended file missing: {file_name}")
        
        # Check for test directory (strict mode)
        if strict and not (plugin_dir / "tests").exists():
            warnings.append("Test directory missing (recommended for production plugins)")
        
        return errors, warnings
    
    def _validate_python_syntax(self, path: str) -> List[str]:
        """Validate Python syntax in plugin files"""
        errors = []
        
        plugin_dir = Path(path)
        python_files = list(plugin_dir.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the Python code
                ast.parse(content)
                
                # Additional checks
                if "class" not in content and py_file.name.endswith("_plugin.py"):
                    errors.append(f"No class definition found in main plugin file: {py_file}")
                
            except SyntaxError as e:
                errors.append(f"Syntax error in {py_file}: {e}")
            except Exception as e:
                errors.append(f"Error reading {py_file}: {e}")
        
        return errors
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        import re
        pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
        return bool(re.match(pattern, version))
    
    def _validate_plugin_class(self, path: str, manifest: Dict[str, Any]) -> List[str]:
        """Validate that the main plugin class exists and is properly structured"""
        errors = []
        
        if "entrypoint" not in manifest or "main_class" not in manifest:
            return errors
        
        try:
            entrypoint_path = Path(path) / manifest["entrypoint"]
            spec = importlib.util.spec_from_file_location("plugin_module", entrypoint_path)
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if main class exists
                main_class_name = manifest["main_class"]
                if not hasattr(module, main_class_name):
                    errors.append(f"Main class '{main_class_name}' not found in {manifest['entrypoint']}")
                else:
                    # Check if class has required methods
                    plugin_class = getattr(module, main_class_name)
                    required_methods = ["validate_config", "initialize"]
                    
                    for method in required_methods:
                        if not hasattr(plugin_class, method):
                            errors.append(f"Required method '{method}' missing from class {main_class_name}")
        
        except Exception as e:
            errors.append(f"Error validating plugin class: {e}")
        
        return errors