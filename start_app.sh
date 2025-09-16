#!/bin/bash

echo "🚀 Starting RAG Builder v2.0..."
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

# Check if required files exist
if [ ! -f "run_server.py" ]; then
    echo "❌ run_server.py not found!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip3 install -r requirements.txt --quiet

# Run tests first
echo "🧪 Running tests..."
python3 test_app.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests passed! Starting server..."
    echo "🌐 Open your browser to: http://localhost:8000"
    echo "🔄 Press Ctrl+C to stop the server"
    echo ""
    
    # Start the server
    python3 run_server.py
else
    echo "❌ Tests failed. Please check the setup."
    exit 1
fi