# 🔗 RAG Builder - Plug-and-Play RAG Pipeline Creator

A visual drag-and-drop interface for building Retrieval-Augmented Generation (RAG) pipelines without code.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone/Download the project**
2. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic python-multipart pyyaml
   ```

3. **Start the server:**
   ```bash
   python run_server.py
   ```

4. **Open your browser:**
   - Frontend: http://localhost:8000/static/index.html
   - API Docs: http://localhost:8000/docs

## 🎯 Features

### ✅ Current MVP Features
- **Drag-and-Drop UI**: Visual pipeline builder with component palette
- **Component Library**: Data Sources, Vector DBs, and LLMs
- **Real-time Configuration**: Configure components via side panel
- **Pipeline Visualization**: See connections between components
- **Test Queries**: Test your pipeline with sample questions
- **Export/Import**: Save and load pipeline configurations
- **Plugin System**: Extensible architecture for new components

### 🔌 Available Components

**Data Sources:**
- SQLite Database
- File Upload (PDF, TXT)
- PostgreSQL (planned)

**Vector Databases:**
- ChromaDB
- FAISS
- Pinecone (planned)

**LLMs:**
- OpenAI GPT
- Ollama (Local)
- Anthropic (planned)

## 🎮 How to Use

1. **Open the web interface** at http://localhost:8000/static/index.html
2. **Drag components** from the left palette to the canvas
3. **Connect components** by dragging them in order: Data Source → Vector DB → LLM
4. **Configure each component** by clicking on it and filling the configuration panel
5. **Test your pipeline** using the "Test Query" button
6. **Export your configuration** to save your work

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS)
├── Drag-and-drop interface
├── Component configuration
└── Query testing

Backend (FastAPI)
├── Pipeline Manager
├── Plugin Manager
├── Component validation
└── Query execution

Plugin System
├── Built-in plugins
├── External plugin support
└── Configuration schemas
```

## 🔧 Development

### Project Structure
```
/
├── frontend/              # Web interface
│   ├── index.html        # Main UI
│   ├── styles.css        # Styling
│   └── script.js         # Drag-and-drop logic
├── backend/              # Core framework only
│   ├── main.py          # API endpoints
│   ├── models.py        # Data models
│   └── services/        # Core services
│       ├── base_plugin.py    # Plugin base classes
│       ├── plugin_manager.py # Plugin management
│       └── pipeline_manager.py # Pipeline orchestration
├── plugins/             # All plugins (external to backend)
│   ├── llm/            # LLM plugins
│   │   ├── openai_plugin.py
│   │   └── ollama_plugin.py
│   ├── vectordb/       # Vector database plugins
│   │   ├── chroma_plugin.py
│   │   └── faiss_plugin.py
│   ├── datasource/     # Data source plugins
│   └── embedding/      # Embedding plugins
├── run_server.py       # Development server
├── install.py         # Installation script
└── test_real_plugins.py # Plugin testing
```

### Running Tests
```bash
python tmp_rovodev_test_basic.py  # Basic functionality test
python demo.py                   # Full feature demo
```

## 📋 Current Status

This is an **MVP (Minimum Viable Product)** focused on rapid prototyping. The system includes:

- ✅ Working drag-and-drop UI
- ✅ Component management system
- ✅ Plugin architecture foundation
- ✅ Mock query execution
- ✅ Configuration validation
- 🔄 Real LLM integration (in progress)
- 🔄 Actual vector database connections (in progress)
- 🔄 File upload processing (in progress)

## 🛣️ Roadmap

### Phase 1 (Current MVP)
- [x] Drag-and-drop UI
- [x] Basic component system
- [x] Plugin architecture
- [x] Mock query execution

### Phase 2 (Next)
- [ ] Real LLM integrations (OpenAI, Ollama)
- [ ] Vector database connections (ChromaDB, FAISS)
- [ ] File upload and processing
- [ ] Database connectors

### Phase 3 (Future)
- [ ] User authentication
- [ ] Pipeline sharing
- [ ] Advanced plugin marketplace
- [ ] Cloud deployment

## 🤝 Contributing

This project prioritizes **fast development** and **working prototypes**. To contribute:

1. Focus on getting features working quickly
2. Use the existing plugin system for new components
3. Update the build-log.md with completed features
4. Test with the demo script

## 📝 License

MIT License - Build amazing RAG systems!