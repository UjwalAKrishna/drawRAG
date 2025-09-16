# 🚀 Getting Started with RAG Builder

Welcome to RAG Builder! This guide will help you build your first RAG application in just a few minutes.

## 📋 Prerequisites

- Python 3.8 or higher
- Basic understanding of Python functions
- (Optional) Git for cloning the repository

## 🛠️ Installation

### Option 1: Clone from GitHub
```bash
git clone https://github.com/ragbuilder/ragbuilder.git
cd ragbuilder
pip install -r requirements.txt
```

### Option 2: Install via pip (coming soon)
```bash
pip install ragbuilder
```

## 🏃 Quick Start

### Step 1: Start the Framework
```bash
python run_server.py
```

The framework will start at `http://localhost:8000` and automatically discover any plugins in the `plugins/` directory.

### Step 2: Create Your First Plugin

Create a simple text processing plugin:

```python
# plugins/my_first_plugin.py

def clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace and converting to lowercase."""
    return text.strip().lower()

def count_words(text: str) -> int:
    """Count the number of words in the given text."""
    return len(text.split())

def reverse_text(text: str) -> str:
    """Reverse the input text."""
    return text[::-1]
```

That's it! The framework automatically discovers and loads your plugin.

### Step 3: Test Your Plugin

Test your plugin using the REST API:

```bash
# Clean text
curl -X POST http://localhost:8000/api/call/clean_text \
  -H "Content-Type: application/json" \
  -d '{"args": ["  Hello WORLD  "]}'

# Response: {"success": true, "result": "hello world"}

# Count words
curl -X POST http://localhost:8000/api/call/count_words \
  -H "Content-Type: application/json" \
  -d '{"args": ["Hello beautiful world"]}'

# Response: {"success": true, "result": 3}
```

### Step 4: Use the Web Interface

Open `http://localhost:8000` in your browser to use the interactive web interface:

1. Select a capability from the dropdown
2. Enter your input parameters
3. Click "Execute" to see the results

## 🔍 Exploring the Framework

### View Available Capabilities
```bash
curl http://localhost:8000/api/capabilities
```

### Get Plugin Information
```bash
curl http://localhost:8000/api/plugins
```

### Check Framework Health
```bash
curl http://localhost:8000/api/health
```

## 🎯 Next Steps

### Create More Advanced Plugins

Try creating plugins for different types of tasks:

```python
# plugins/llm_helper.py

def summarize_text(text: str, max_length: int = 100) -> str:
    """Summarize text to a maximum length."""
    words = text.split()
    if len(' '.join(words)) <= max_length:
        return text
    
    # Simple truncation for demo
    summary = []
    length = 0
    for word in words:
        if length + len(word) + 1 > max_length:
            break
        summary.append(word)
        length += len(word) + 1
    
    return ' '.join(summary) + '...'

def extract_keywords(text: str, max_keywords: int = 5) -> list:
    """Extract keywords from text (simple implementation)."""
    # Simple keyword extraction (in production, use NLP libraries)
    words = text.lower().split()
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [word for word in words if word not in stop_words and len(word) > 3]
    return list(set(keywords))[:max_keywords]
```

### Use the CLI Tools

```bash
# Initialize a new plugin
python setup_cli.py
rag-plugin init my-new-plugin --type data-source

# Validate your plugins
rag-plugin validate

# Run tests
rag-plugin test
```

### Explore Plugin Types

RAG Builder supports several plugin types:

- **Data Source Plugins**: Connect to databases, APIs, files
- **LLM Plugins**: Integrate with language models
- **Vector Database Plugins**: Handle embeddings and similarity search
- **Processing Plugins**: Transform and manipulate data

## 🐛 Troubleshooting

### Common Issues

**Plugin not loading?**
- Check the `plugins/` directory contains your `.py` file
- Ensure your functions have proper type hints
- Check the server logs for syntax errors

**API calls failing?**
- Verify the server is running on `http://localhost:8000`
- Check that the capability name matches your function name
- Ensure proper JSON formatting in requests

**Import errors?**
- Install required dependencies: `pip install -r requirements.txt`
- Check Python version compatibility (3.8+)

### Debug Mode

Start the framework in debug mode for detailed logging:

```bash
python run_server.py --debug
```

## 📚 What's Next?

- **[Plugin Development Guide](plugin-development.md)** - Create advanced plugins
- **[API Reference](../reference/api-reference.md)** - Complete API documentation
- **[Architecture Overview](../architecture/overview.md)** - Understand how it works
- **[Examples](../examples/)** - See real-world implementations

## 🤝 Getting Help

- **GitHub Issues**: [Report bugs or ask questions](https://github.com/ragbuilder/ragbuilder/issues)
- **Discord**: [Join our community](https://discord.gg/ragbuilder)
- **Documentation**: Explore more guides in this documentation

---

**Congratulations! 🎉** You've successfully created your first RAG Builder application. The framework makes it incredibly easy to build powerful, production-ready RAG systems with just Python functions.