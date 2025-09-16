#!/usr/bin/env python3
"""
RAG Builder Server Runner - Dynamic Framework
"""

import uvicorn
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    # Run the framework API
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        reload_dirs=["backend", "plugins"]
    )