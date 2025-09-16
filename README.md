# 🚀 RAG Builder v2.0

**The Ultimate Dynamic Plugin Framework for RAG Applications**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Framework](https://img.shields.io/badge/Framework-Dynamic%20Plugins-orange.svg)](https://github.com/ragbuilder/ragbuilder)

> **Zero Configuration • Hot Reloading • Enterprise Grade**

RAG Builder makes building Retrieval-Augmented Generation applications as easy as writing Python functions. Create production-ready RAG systems in minutes, not months.

## ✨ **Why RAG Builder?**

```python
# Create a plugin in 30 seconds
def clean_text(text: str) -> str:
    return text.strip().lower()

def count_words(text: str) -> int:
    return len(text.split())

# That's it! Framework auto-discovers and loads your plugin
```

### **🎯 Zero Configuration**
- **No YAML manifests** - Just write Python functions
- **Auto-discovery** - Framework finds everything automatically  
- **Hot reloading** - Update plugins without restart
- **Instant deployment** - From code to production in seconds

### **⚡ Super Dynamic**
- **Any Python callable** becomes a plugin capability
- **Dynamic routing** - Call any capability by name
- **Smart caching** - Automatic performance optimization
- **Load balancing** - Intelligent plugin selection

### **🏢 Enterprise Ready**
- **Advanced metrics** - Real-time performance monitoring
- **Error recovery** - Comprehensive error handling
- **Security validation** - Multi-layer plugin validation
- **Dependency resolution** - Automatic plugin dependencies

## 🚀 **Quick Start**

### **1. Installation**

```bash
git clone https://github.com/ragbuilder/ragbuilder.git
cd ragbuilder
pip install -r requirements.txt
```

### **2. Start the Framework**

```bash
python run_server.py
```

Framework starts at `http://localhost:8000` with auto-discovered plugins!

### **3. Create Your First Plugin**

```bash
# Use the CLI to scaffold a new plugin
rag-plugin init my-awesome-plugin --type llm

# Or just create a Python file in plugins/
echo 'def hello(name): return f"Hello {name}!"' > plugins/my_plugin.py
```

### **4. Test Your Plugin**

```bash
# Framework automatically discovers and loads your plugin
curl -X POST http://localhost:8000/api/call/hello \
  -H "Content-Type: application/json" \
  -d '{"args": ["World"]}'

# Response: {"success": true, "result": "Hello World!"}
```

## 📚 **Documentation**

- **[📚 Complete Documentation](docs/)** - Architecture, guides, and API reference
- **[🏗️ Architecture Guide](docs/architecture/)** - Framework design and concepts  
- **[🔌 Plugin Development](docs/guides/)** - Create your own plugins
- **[🛠️ CLI & SDK Reference](docs/reference/)** - Tools and utilities
- **[💡 Examples](docs/examples/)** - Real-world implementations

## 🌟 **Community**

- **GitHub**: [github.com/ragbuilder/ragbuilder](https://github.com/ragbuilder/ragbuilder)
- **Discord**: [Join our community](https://discord.gg/ragbuilder)
- **Twitter**: [@ragbuilder](https://twitter.com/ragbuilder)
- **Docs**: [docs.ragbuilder.dev](https://docs.ragbuilder.dev)

---

**Built with ❤️ by the RAG Builder community**

*Making RAG development as easy as writing Python functions.*