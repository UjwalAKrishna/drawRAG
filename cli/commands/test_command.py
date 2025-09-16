"""
Test Command - Run plugin tests
"""

import subprocess
import sys
from pathlib import Path
from .base_command import BaseCommand


class TestCommand(BaseCommand):
    """Run plugin tests"""
    
    def execute(self, args) -> int:
        """Execute test command"""
        plugin_path = Path(args.path)
        local_mode = args.local
        coverage = args.coverage
        
        self.print_info(f"Running tests for plugin at: {plugin_path}")
        
        # Check if plugin exists
        if not self._is_valid_plugin_directory(plugin_path):
            self.print_error("Not a valid plugin directory")
            return 1
        
        # Check for test files
        test_files = self._find_test_files(plugin_path)
        if not test_files:
            self.print_warning("No test files found")
            if not local_mode:
                self.print_info("Creating basic test structure...")
                self._create_basic_tests(plugin_path)
                test_files = self._find_test_files(plugin_path)
        
        if local_mode:
            return self._run_local_tests(plugin_path, test_files, coverage)
        else:
            return self._run_integration_tests(plugin_path, test_files, coverage)
    
    def _is_valid_plugin_directory(self, path: Path) -> bool:
        """Check if directory contains a valid plugin"""
        manifest_file = self.find_manifest_file(str(path))
        src_dir = path / "src"
        return manifest_file is not None and src_dir.exists()
    
    def _find_test_files(self, path: Path) -> list:
        """Find test files in the plugin directory"""
        test_dirs = [path / "tests", path / "test"]
        test_files = []
        
        for test_dir in test_dirs:
            if test_dir.exists():
                test_files.extend(list(test_dir.glob("test_*.py")))
                test_files.extend(list(test_dir.glob("*_test.py")))
        
        return test_files
    
    def _create_basic_tests(self, path: Path):
        """Create basic test structure if none exists"""
        test_dir = path / "tests"
        test_dir.mkdir(exist_ok=True)
        
        manifest = self.load_manifest(str(path))
        if not manifest:
            return
        
        plugin_name = manifest.get("key", "plugin")
        test_content = f'''"""
Basic tests for {plugin_name}
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_plugin_import():
    """Test that plugin can be imported"""
    try:
        # Try to import the main plugin module
        import {plugin_name.replace("-", "_")}_plugin
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import plugin: {{e}}")


def test_plugin_creation():
    """Test that plugin can be created with basic config"""
    try:
        from {plugin_name.replace("-", "_")}_plugin import create_plugin
        
        config = {{}}  # Add basic test config here
        plugin = create_plugin(config)
        assert plugin is not None
    except Exception as e:
        pytest.fail(f"Failed to create plugin: {{e}}")


@pytest.mark.asyncio
async def test_plugin_initialization():
    """Test plugin initialization"""
    try:
        from {plugin_name.replace("-", "_")}_plugin import create_plugin
        
        config = {{}}  # Add basic test config here
        plugin = create_plugin(config)
        
        # Test initialization
        result = await plugin.initialize()
        assert isinstance(result, bool)
        
        # Test cleanup
        await plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Plugin initialization failed: {{e}}")
'''
        
        test_file = test_dir / f"test_{plugin_name.replace('-', '_')}.py"
        self.write_file(test_file, test_content)
        
        # Create __init__.py
        init_file = test_dir / "__init__.py"
        self.write_file(init_file, "# Test package")
    
    def _run_local_tests(self, path: Path, test_files: list, coverage: bool) -> int:
        """Run tests in local environment"""
        self.print_info("Running tests in local environment...")
        
        # Change to plugin directory
        original_cwd = Path.cwd()
        try:
            # Install dependencies
            if (path / "requirements.txt").exists():
                self.print_info("Installing dependencies...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ], cwd=path, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.print_warning("Failed to install some dependencies")
                    print(result.stderr)
            
            # Run pytest
            cmd = [sys.executable, "-m", "pytest", "-v"]
            
            if coverage:
                cmd.extend(["--cov=src", "--cov-report=term-missing"])
            
            if test_files:
                cmd.extend([str(f.relative_to(path)) for f in test_files])
            else:
                cmd.append("tests/")
            
            self.print_info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=path)
            
            if result.returncode == 0:
                self.print_success("All tests passed!")
            else:
                self.print_error("Some tests failed")
            
            return result.returncode
            
        except Exception as e:
            self.print_error(f"Error running tests: {e}")
            return 1
    
    def _run_integration_tests(self, path: Path, test_files: list, coverage: bool) -> int:
        """Run tests with RAG Builder integration"""
        self.print_info("Running integration tests with RAG Builder...")
        
        # TODO: Implement integration testing
        # This would involve:
        # 1. Starting a test RAG Builder instance
        # 2. Loading the plugin into the test environment
        # 3. Running tests against the full system
        # 4. Cleaning up test environment
        
        self.print_warning("Integration testing not yet implemented")
        self.print_info("Falling back to local tests...")
        
        return self._run_local_tests(path, test_files, coverage)
    
    def _check_pytest_available(self) -> bool:
        """Check if pytest is available"""
        try:
            subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _install_test_dependencies(self) -> bool:
        """Install testing dependencies"""
        try:
            self.print_info("Installing pytest...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], 
                         check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False