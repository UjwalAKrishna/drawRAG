#!/usr/bin/env python3
"""
RAG Builder - Development Server Launcher
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """Launch the development server"""
    print("🚀 Starting RAG Builder Development Server...")
    print("📁 Frontend: http://localhost:8000/static/index.html")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    print("\n" + "="*50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend", "frontend"],
        log_level="info"
    )

if __name__ == "__main__":
    main()