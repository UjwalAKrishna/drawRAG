"""
Build Command - Build plugin package
"""

import shutil
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime
from .base_command import BaseCommand


class BuildCommand(BaseCommand):
    """Build plugin package"""
    
    def execute(self, args) -> int:
        """Execute build command"""
        plugin_path = Path(".")
        output_dir = Path(args.output) if args.output else plugin_path / "dist"
        package_format = args.format
        
        self.print_info(f"Building plugin package in format: {package_format}")
        
        # Validate plugin
        if not self._validate_plugin_for_build(plugin_path):
            return 1
        
        # Create output directory
        if not self.create_directory(output_dir):
            return 1
        
        # Load manifest
        manifest = self.load_manifest(str(plugin_path))
        if not manifest:
            self.print_error("Cannot load plugin manifest")
            return 1
        
        # Build package
        try:
            package_path = self._create_package(plugin_path, output_dir, manifest, package_format)
            
            if package_path:
                self.print_success(f"Plugin package created: {package_path}")
                self._print_package_info(package_path, manifest)
                return 0
            else:
                self.print_error("Failed to create package")
                return 1
                
        except Exception as e:
            self.print_error(f"Build failed: {e}")
            return 1
    
    def _validate_plugin_for_build(self, path: Path) -> bool:
        """Validate plugin is ready for building"""
        # Check manifest exists
        if not self.find_manifest_file(str(path)):
            self.print_error("No plugin manifest found")
            return False
        
        # Check source directory exists
        if not (path / "src").exists():
            self.print_error("Source directory (src/) not found")
            return False
        
        # Check entrypoint exists
        manifest = self.load_manifest(str(path))
        if manifest and "entrypoint" in manifest:
            entrypoint_path = path / manifest["entrypoint"]
            if not entrypoint_path.exists():
                self.print_error(f"Entrypoint file not found: {manifest['entrypoint']}")
                return False
        
        return True
    
    def _create_package(self, plugin_path: Path, output_dir: Path, 
                       manifest: dict, package_format: str) -> Path:
        """Create the plugin package"""
        plugin_name = manifest.get("key", "plugin")
        version = manifest.get("version", "1.0.0")
        
        # Package filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if package_format == "zip":
            package_name = f"{plugin_name}-{version}.zip"
        else:
            package_name = f"{plugin_name}-{version}.tar.gz"
        
        package_path = output_dir / package_name
        
        # Files to include in package
        include_patterns = [
            "src/**/*",
            "plugin.yaml",
            "plugin.yml", 
            "plugin.json",
            "README.md",
            "requirements.txt",
            "setup.py",
            "LICENSE",
            "docs/**/*",
            "examples/**/*"
        ]
        
        # Files to exclude
        exclude_patterns = [
            "**/__pycache__/**",
            "**/*.pyc",
            "**/.pytest_cache/**",
            "**/tests/**",
            "**/.git/**",
            "**/dist/**",
            "**/*.egg-info/**"
        ]
        
        # Collect files to package
        files_to_package = self._collect_files(plugin_path, include_patterns, exclude_patterns)
        
        if not files_to_package:
            self.print_error("No files found to package")
            return None
        
        # Create package
        if package_format == "zip":
            return self._create_zip_package(package_path, plugin_path, files_to_package)
        else:
            return self._create_tar_package(package_path, plugin_path, files_to_package)
    
    def _collect_files(self, plugin_path: Path, include_patterns: list, exclude_patterns: list) -> list:
        """Collect files for packaging"""
        import fnmatch
        
        files_to_package = []
        
        for pattern in include_patterns:
            matching_files = list(plugin_path.glob(pattern))
            for file_path in matching_files:
                if file_path.is_file():
                    # Check if file should be excluded
                    relative_path = file_path.relative_to(plugin_path)
                    should_exclude = False
                    
                    for exclude_pattern in exclude_patterns:
                        if fnmatch.fnmatch(str(relative_path), exclude_pattern):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        files_to_package.append(file_path)
        
        return files_to_package
    
    def _create_zip_package(self, package_path: Path, plugin_path: Path, files: list) -> Path:
        """Create ZIP package"""
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                arcname = file_path.relative_to(plugin_path)
                zipf.write(file_path, arcname)
                
        return package_path
    
    def _create_tar_package(self, package_path: Path, plugin_path: Path, files: list) -> Path:
        """Create TAR.GZ package"""
        with tarfile.open(package_path, 'w:gz') as tarf:
            for file_path in files:
                arcname = file_path.relative_to(plugin_path)
                tarf.add(file_path, arcname)
                
        return package_path
    
    def _print_package_info(self, package_path: Path, manifest: dict):
        """Print information about the created package"""
        import os
        
        size_mb = os.path.getsize(package_path) / (1024 * 1024)
        
        print(f"")
        print(f"📦 Package Details:")
        print(f"   Name: {manifest.get('name', 'Unknown')}")
        print(f"   Version: {manifest.get('version', 'Unknown')}")
        print(f"   Type: {manifest.get('type', 'Unknown')}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Location: {package_path}")
        print(f"")
        print(f"🚀 Ready for distribution!")
        
        # Print next steps
        print(f"Next steps:")
        print(f"  1. Test the package: rag-plugin test")
        print(f"  2. Validate: rag-plugin validate --strict")
        print(f"  3. Publish to registry (when available)")
    
    def _create_build_metadata(self, plugin_path: Path, manifest: dict) -> dict:
        """Create build metadata"""
        return {
            "build_time": datetime.now().isoformat(),
            "plugin_name": manifest.get("name"),
            "plugin_version": manifest.get("version"),
            "plugin_type": manifest.get("type"),
            "builder_version": "1.0.0",
            "files_included": len(self._collect_files(plugin_path, ["**/*"], [])),
        }