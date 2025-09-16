#!/usr/bin/env python3
"""
RAG Builder Server Runner - Core Framework Version
"""

import uvicorn
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    # Run the new core framework API
    uvicorn.run(
        "api:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        reload_dirs=["backend", "plugins_builtin"]
    )