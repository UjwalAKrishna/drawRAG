# 🚀 RAG Builder v2.0 - Complete Setup Guide

## What's Been Implemented

### ✅ Backend Restructure
- **Modular API Structure**: Moved from single `api.py` to organized `backend/api/` module
- **Route Separation**: Split into dedicated route files:
  - `plugins.py` - Plugin management, upload, reload
  - `capabilities.py` - Capability discovery and execution  
  - `pipeline.py` - Pipeline validation, execution, save/load
  - `rag.py` - RAG query execution and document indexing
- **Dependency Injection**: Clean manager instance handling
- **Better Error Handling**: Comprehensive error responses

### ✅ Dynamic Frontend
- **Plugin Manager**: Real-time plugin discovery from backend
- **Smart Categorization**: Auto-categorizes plugins by capabilities
- **Plugin Upload**: Drag & drop Python files to install plugins
- **Hot Reload**: Reload plugins without restart
- **RAG Tester**: Built-in query testing with result visualization
- **Document Processor**: Upload and index documents for RAG

### ✅ Key Features
1. **Zero Configuration**: Just drop Python files in `plugins/` folder
2. **Hot Reloading**: Update plugins without restart
3. **Dynamic UI**: Frontend adapts to available plugins
4. **Visual Pipeline Builder**: Drag & drop RAG workflow creation
5. **Real-time Testing**: Test RAG queries with immediate feedback
6. **Document Management**: Upload, process, and index documents

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the Setup
```bash
python3 test_app.py
```

### 3. Start the Application
```bash
python3 run_server.py
```

### 4. Open in Browser
Navigate to: `http://localhost:8000`

## 📁 Project Structure

```
ragbuilder/
├── backend/
│   ├── api/                    # API module
│   │   ├── main.py            # FastAPI app
│   │   ├── dependencies.py    # Dependency injection
│   │   └── routes/            # Route handlers
│   │       ├── plugins.py     # Plugin management
│   │       ├── capabilities.py # Capability execution
│   │       ├── pipeline.py    # Pipeline management
│   │       └── rag.py         # RAG operations
│   └── core/                  # Framework core
│       ├── framework.py       # Core framework
│       ├── manager.py         # High-level manager
│       └── loader.py          # Plugin loader
├── frontend/
│   ├── index.html            # Main UI
│   ├── styles.css            # Enhanced styles
│   └── js/
│       ├── core/             # Core modules
│       └── modules/          # Extended modules
│           ├── plugin-manager.js      # Plugin management
│           ├── rag-tester.js          # RAG testing
│           └── document-processor.js   # Document handling
└── plugins/                  # Plugin directory
    └── examples/             # Example plugins
```

## 🔌 How to Use

### Adding Plugins
1. **Upload via UI**: Drag & drop `.py` files in the frontend
2. **File System**: Drop Python files in `plugins/` folder
3. **Auto Discovery**: Framework automatically finds and loads plugins

### Creating Plugins
```python
# Simple function-based plugin
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    return text.strip().lower()

# Class-based plugin
from backend.core import QuickPlugin, capability

class MyPlugin(QuickPlugin):
    @capability("Process data")
    def process_data(self, data):
        return f"Processed: {data}"
```

### Building RAG Pipelines
1. **Drag Components**: From the plugin palette to canvas
2. **Connect Components**: Draw connections between components
3. **Configure Settings**: Set parameters for each component
4. **Test Pipeline**: Use the built-in query tester
5. **Save Pipeline**: Save configurations for reuse

### Testing RAG Queries
1. **Click "Test Query"** button
2. **Enter your question**
3. **View results** with sources and execution details
4. **Iterate** and improve your pipeline

## 🎯 Example Workflow

1. **Upload Documents**:
   - Go to Documents tab
   - Upload PDF, TXT, or other files
   - Click "Index Documents"

2. **Build Pipeline**:
   - Drag data source → vector database → LLM
   - Configure each component
   - Validate pipeline

3. **Test RAG**:
   - Open query tester
   - Ask questions about your documents
   - Get AI responses with sources

## 🔧 Configuration

### Environment Variables
Create `.env` file:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Plugin Configuration
Plugins auto-configure, but you can customize:
```python
# In your plugin
def initialize(self):
    self.config = {
        "api_key": os.getenv("YOUR_API_KEY"),
        "model": "gpt-4",
        "temperature": 0.7
    }
```

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# View logs
python3 run_server.py
```

### Plugin Issues
- Check plugin syntax
- Verify dependencies are installed
- Use reload button in UI
- Check browser console for errors

### Frontend Issues
- Clear browser cache
- Check browser console
- Verify all JS files are loading

## 🎉 What's Working Now

- ✅ **Fully Dynamic Plugin System**: Real plugins from backend
- ✅ **Plugin Upload & Management**: Drag & drop functionality
- ✅ **RAG Pipeline Builder**: Visual workflow creation
- ✅ **Document Processing**: Upload and index documents
- ✅ **Query Testing**: Real-time RAG testing
- ✅ **Hot Reloading**: Update plugins without restart
- ✅ **API Organization**: Clean, modular backend structure

The application is now fully functional with both frontend and backend working together seamlessly!