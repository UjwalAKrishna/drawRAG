# 🛠️ CLI Reference

Complete command-line interface documentation for RAG Builder v2.0.

## 📋 Installation

The CLI tools are included with RAG Builder. After installing the framework:

```bash
# Setup CLI tools
python setup_cli.py

# Verify installation
rag-plugin --version
```

## 🚀 Quick Start

```bash
# Initialize a new plugin
rag-plugin init my-plugin --type data-source

# Validate all plugins
rag-plugin validate

# Start development server
rag-plugin dev

# Run tests
rag-plugin test
```

## 📖 Commands Overview

| Command | Description |
|---------|-------------|
| `init` | Initialize a new plugin |
| `validate` | Validate plugin syntax and structure |
| `test` | Run plugin tests |
| `build` | Build plugins for production |
| `dev` | Start development server |
| `framework` | Framework management commands |

---

## 🔧 Command Details

### `rag-plugin init`

Initialize a new plugin with scaffolding and templates.

```bash
rag-plugin init [PLUGIN_NAME] [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | string | `basic` | Plugin type (basic, llm, data-source, vector-db) |
| `--directory` | string | `plugins/` | Target directory for the plugin |
| `--template` | string | `default` | Template to use for scaffolding |
| `--author` | string | | Author name for plugin metadata |
| `--description` | string | | Plugin description |
| `--interactive` | flag | `false` | Interactive mode with prompts |

#### Examples

```bash
# Basic plugin
rag-plugin init text-utils

# LLM plugin with custom directory
rag-plugin init my-llm --type llm --directory custom-plugins/

# Interactive mode
rag-plugin init --interactive

# With metadata
rag-plugin init sentiment-analyzer \
  --type llm \
  --author "John Doe" \
  --description "Sentiment analysis plugin"
```

#### Plugin Types

**`basic`** - Simple function-based plugin
```python
def process_text(text: str) -> str:
    """Process input text."""
    return text.upper()
```

**`llm`** - Language model integration plugin
```python
from sdk.llm_plugin import LLMPlugin

class MyLLM(LLMPlugin):
    def generate(self, prompt: str) -> str:
        # LLM implementation
        pass
```

**`data-source`** - Data connection and retrieval plugin
```python
from sdk.data_source_plugin import DataSourcePlugin

class MyDataSource(DataSourcePlugin):
    def fetch(self, query: str) -> list:
        # Data fetching implementation
        pass
```

**`vector-db`** - Vector database integration plugin
```python
from sdk.vector_db_plugin import VectorDBPlugin

class MyVectorDB(VectorDBPlugin):
    def search(self, query_vector: list, k: int = 5) -> list:
        # Vector search implementation
        pass
```

### `rag-plugin validate`

Validate plugins for syntax, structure, and dependencies.

```bash
rag-plugin validate [OPTIONS] [PLUGIN_NAMES...]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--directory` | string | `plugins/` | Directory to validate |
| `--strict` | flag | `false` | Enable strict validation mode |
| `--fix` | flag | `false` | Auto-fix common issues |
| `--format` | string | `table` | Output format (table, json, yaml) |
| `--output` | string | | Save results to file |

#### Examples

```bash
# Validate all plugins
rag-plugin validate

# Validate specific plugins
rag-plugin validate text-processor llm-helper

# Strict mode with JSON output
rag-plugin validate --strict --format json

# Auto-fix issues
rag-plugin validate --fix
```

#### Validation Checks

- **Syntax**: Python syntax and import errors
- **Type Hints**: Function parameter and return type annotations
- **Documentation**: Docstrings and parameter descriptions
- **Dependencies**: Required package availability
- **Security**: Basic security pattern scanning
- **Performance**: Potential performance issues

#### Sample Output

```
┌─────────────────┬────────┬─────────┬──────────────────────────────┐
│ Plugin          │ Status │ Issues  │ Description                  │
├─────────────────┼────────┼─────────┼──────────────────────────────┤
│ text-processor  │ ✅ PASS │ 0       │ All checks passed            │
│ llm-helper      │ ⚠️ WARN │ 2       │ Missing type hints           │
│ broken-plugin   │ ❌ FAIL │ 5       │ Syntax errors, missing deps  │
└─────────────────┴────────┴─────────┴──────────────────────────────┘
```

### `rag-plugin test`

Run comprehensive tests for plugins.

```bash
rag-plugin test [OPTIONS] [PLUGIN_NAMES...]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--directory` | string | `plugins/` | Directory containing plugins |
| `--coverage` | flag | `false` | Generate code coverage report |
| `--benchmark` | flag | `false` | Run performance benchmarks |
| `--integration` | flag | `false` | Run integration tests |
| `--verbose` | flag | `false` | Verbose test output |
| `--parallel` | integer | `4` | Number of parallel test workers |

#### Examples

```bash
# Test all plugins
rag-plugin test

# Test specific plugins with coverage
rag-plugin test text-processor --coverage

# Full test suite with benchmarks
rag-plugin test --integration --benchmark --verbose
```

#### Test Types

**Unit Tests**: Test individual functions
```python
def test_clean_text():
    result = clean_text("  Hello  ")
    assert result == "hello"
```

**Integration Tests**: Test plugin loading and execution
```python
def test_plugin_integration():
    framework = FrameworkManager()
    result = framework.call_capability("clean_text", ["  Test  "])
    assert result == "test"
```

**Performance Tests**: Benchmark plugin performance
```python
def test_performance():
    start_time = time.time()
    for i in range(1000):
        clean_text(f"test {i}")
    duration = time.time() - start_time
    assert duration < 1.0  # Should complete in under 1 second
```

### `rag-plugin build`

Build and package plugins for production deployment.

```bash
rag-plugin build [OPTIONS] [PLUGIN_NAMES...]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output` | string | `dist/` | Output directory for built plugins |
| `--format` | string | `wheel` | Package format (wheel, tar, zip) |
| `--optimize` | flag | `false` | Enable code optimization |
| `--minify` | flag | `false` | Minify plugin code |
| `--include-deps` | flag | `false` | Bundle dependencies |

#### Examples

```bash
# Build all plugins
rag-plugin build

# Build specific plugin with optimization
rag-plugin build text-processor --optimize --minify

# Build with dependencies bundled
rag-plugin build --include-deps --format zip
```

### `rag-plugin dev`

Start development server with hot reloading and debugging features.

```bash
rag-plugin dev [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | integer | `8000` | Server port |
| `--host` | string | `localhost` | Server host |
| `--debug` | flag | `false` | Enable debug mode |
| `--reload` | flag | `true` | Enable hot reloading |
| `--watch` | string | `plugins/` | Directory to watch for changes |

#### Examples

```bash
# Start development server
rag-plugin dev

# Custom port with debug mode
rag-plugin dev --port 9000 --debug

# Watch custom directory
rag-plugin dev --watch custom-plugins/
```

#### Development Features

- **Hot Reloading**: Automatically reload plugins on file changes
- **Debug Mode**: Detailed error messages and stack traces
- **Interactive Console**: Built-in Python console for testing
- **API Explorer**: Web-based API testing interface
- **Performance Monitor**: Real-time performance metrics

### `rag-plugin framework`

Framework management and configuration commands.

```bash
rag-plugin framework [SUBCOMMAND] [OPTIONS]
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| `status` | Show framework status and health |
| `config` | View or modify framework configuration |
| `logs` | View framework logs |
| `reset` | Reset framework to default state |
| `update` | Update framework to latest version |

#### Examples

```bash
# Show framework status
rag-plugin framework status

# View configuration
rag-plugin framework config

# View recent logs
rag-plugin framework logs --tail 100

# Reset framework
rag-plugin framework reset --confirm
```

---

## ⚙️ Configuration

### Global Configuration

CLI configuration is stored in `~/.ragbuilder/config.yaml`:

```yaml
# Default settings
defaults:
  plugin_directory: "plugins/"
  server_port: 8000
  debug_mode: false
  
# Plugin templates
templates:
  basic: "https://github.com/ragbuilder/templates/basic"
  llm: "https://github.com/ragbuilder/templates/llm"
  
# Development settings
development:
  hot_reload: true
  auto_validate: true
  show_warnings: true
```

### Project Configuration

Project-specific configuration in `ragbuilder.yaml`:

```yaml
# Project settings
project:
  name: "My RAG Application"
  version: "1.0.0"
  
# Plugin directories
plugins:
  directories:
    - "plugins/"
    - "custom-plugins/"
  exclude:
    - "*.tmp"
    - "test_*"
    
# Validation settings
validation:
  strict_mode: true
  require_type_hints: true
  require_docstrings: true
  
# Testing settings
testing:
  coverage_threshold: 80
  benchmark_timeout: 30
  parallel_workers: 4
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAGBUILDER_HOME` | Framework home directory | `~/.ragbuilder` |
| `RAGBUILDER_PLUGINS_DIR` | Default plugins directory | `plugins/` |
| `RAGBUILDER_DEBUG` | Enable debug mode | `false` |
| `RAGBUILDER_PORT` | Default server port | `8000` |

## 🔍 Debugging & Troubleshooting

### Common Issues

**Command not found: `rag-plugin`**
```bash
# Reinstall CLI tools
python setup_cli.py

# Check PATH
echo $PATH
```

**Plugin validation errors**
```bash
# Run with verbose output
rag-plugin validate --verbose

# Check specific plugin
rag-plugin validate my-plugin --strict
```

**Development server not starting**
```bash
# Check port availability
rag-plugin dev --port 9000

# Enable debug mode
rag-plugin dev --debug
```

### Verbose Mode

Add `--verbose` to any command for detailed output:

```bash
rag-plugin init my-plugin --verbose
rag-plugin validate --verbose
rag-plugin test --verbose
```

### Log Files

CLI operations are logged to:
- `~/.ragbuilder/logs/cli.log` - General CLI operations
- `~/.ragbuilder/logs/dev.log` - Development server logs
- `~/.ragbuilder/logs/test.log` - Test execution logs

## 🧪 Examples

### Complete Plugin Development Workflow

```bash
# 1. Initialize new plugin
rag-plugin init sentiment-analyzer --type llm --interactive

# 2. Develop plugin (edit files)
# ... write your plugin code ...

# 3. Validate during development
rag-plugin validate sentiment-analyzer

# 4. Run tests
rag-plugin test sentiment-analyzer --coverage

# 5. Start development server
rag-plugin dev --debug

# 6. Build for production
rag-plugin build sentiment-analyzer --optimize

# 7. Deploy (framework commands)
rag-plugin framework deploy
```

### Batch Operations

```bash
# Validate multiple plugins
rag-plugin validate plugin1 plugin2 plugin3

# Test with different configurations
rag-plugin test --integration --benchmark --verbose

# Build all plugins with optimization
rag-plugin build --optimize --include-deps
```

### Custom Workflows

```bash
# Create custom validation pipeline
rag-plugin validate --strict --format json > validation.json
rag-plugin test --coverage --format json > tests.json
rag-plugin build --optimize

# Development with custom settings
rag-plugin dev --port 9000 --watch custom-plugins/ --debug
```

---

## 📚 Additional Resources

- **[Plugin Development Guide](../guides/plugin-development.md)** - Complete plugin creation guide
- **[API Reference](api-reference.md)** - REST API documentation
- **[Examples](../examples/)** - Real-world plugin examples
- **[Troubleshooting](../guides/troubleshooting.md)** - Common issues and solutions

The RAG Builder CLI provides a complete development experience for building, testing, and deploying plugin-based RAG applications. Use these tools to streamline your development workflow and ensure high-quality plugins.