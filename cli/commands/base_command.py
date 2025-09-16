"""
Base Command Class
"""

import os
import json
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional


class BaseCommand(ABC):
    """Base class for all CLI commands"""
    
    def __init__(self):
        self.current_dir = Path.cwd()
    
    @abstractmethod
    def execute(self, args) -> int:
        """Execute the command"""
        pass
    
    def find_manifest_file(self, path: str = ".") -> Optional[Path]:
        """Find plugin manifest file"""
        plugin_dir = Path(path)
        for filename in ['plugin.yaml', 'plugin.yml', 'plugin.json']:
            manifest_path = plugin_dir / filename
            if manifest_path.exists():
                return manifest_path
        return None
    
    def load_manifest(self, path: str = ".") -> Optional[Dict[str, Any]]:
        """Load plugin manifest"""
        manifest_file = self.find_manifest_file(path)
        if not manifest_file:
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                if manifest_file.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading manifest: {e}")
            return None
    
    def save_manifest(self, data: Dict[str, Any], path: str = ".", format: str = "yaml") -> bool:
        """Save plugin manifest"""
        try:
            plugin_dir = Path(path)
            if format == "yaml":
                manifest_file = plugin_dir / "plugin.yaml"
                with open(manifest_file, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
            else:
                manifest_file = plugin_dir / "plugin.json"
                with open(manifest_file, 'w') as f:
                    json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving manifest: {e}")
            return False
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"⚠️  {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def create_directory(self, path: Path) -> bool:
        """Create directory if it doesn't exist"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.print_error(f"Failed to create directory {path}: {e}")
            return False
    
    def write_file(self, path: Path, content: str) -> bool:
        """Write content to file"""
        try:
            with open(path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            self.print_error(f"Failed to write file {path}: {e}")
            return False