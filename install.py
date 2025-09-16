#!/usr/bin/env python3
"""
RAG Builder Installation Script
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   RAG Builder requires Python 3.8 or higher")
        return False

def setup_virtual_environment():
    """Set up virtual environment if it doesn't exist"""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔧 Creating virtual environment...")
    return run_command(f"{sys.executable} -m venv .venv", "Virtual environment creation")

def install_dependencies():
    """Install Python dependencies"""
    print("📚 Installing dependencies...")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = ".venv/Scripts/pip"
        python_path = ".venv/Scripts/python"
    else:  # Unix/Linux/macOS
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
    
    # Upgrade pip first
    if not run_command(f"{python_path} -m pip install --upgrade pip", "Pip upgrade"):
        return False
    
    # Install requirements
    return run_command(f"{pip_path} install -r requirements.txt", "Dependencies installation")

def create_env_file():
    """Create .env file template"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file template...")
    
    env_content = """# RAG Builder Environment Variables

# OpenAI Configuration (optional)
# OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration (optional)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Ollama Configuration (optional)
# OLLAMA_BASE_URL=http://localhost:11434

# Database Configuration (optional)
# DATABASE_URL=postgresql://user:password@localhost/ragbuilder

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file template")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    # Determine the correct python path
    if os.name == 'nt':  # Windows
        python_path = ".venv/Scripts/python"
    else:  # Unix/Linux/macOS
        python_path = ".venv/bin/python"
    
    return run_command(f"{python_path} test_real_plugins.py", "Installation test")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "🎉 RAG Builder Installation Complete!" + "\n")
    print("📋 Next Steps:")
    print("1. Activate the virtual environment:")
    
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source .venv/bin/activate")
    
    print("\n2. (Optional) Configure API keys in .env file:")
    print("   - Add your OpenAI API key for GPT models")
    print("   - Add your Anthropic API key for Claude models")
    print("   - Configure Ollama URL if using local models")
    
    print("\n3. Start the RAG Builder server:")
    print("   python run_server.py")
    
    print("\n4. Open your browser:")
    print("   Frontend: http://localhost:8000/static/index.html")
    print("   API Docs: http://localhost:8000/docs")
    
    print("\n🔌 Available Plugins:")
    print("   • Data Sources: SQLite, File Upload")
    print("   • Vector DBs: ChromaDB, FAISS")
    print("   • LLMs: OpenAI GPT, Ollama")
    
    print("\n📚 Documentation:")
    print("   • README.md - Complete setup guide")
    print("   • build-log.md - Development progress")
    print("   • test_real_plugins.py - Test all plugins")
    
    print("\n🚀 Happy RAG Building!")

def main():
    """Main installation process"""
    print("🔗 RAG Builder - Installation Script")
    print("=" * 50)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Virtual Environment Setup", setup_virtual_environment),
        ("Dependencies Installation", install_dependencies),
        ("Environment File Creation", create_env_file),
        ("Installation Test", test_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n🔍 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
            if step_name in ["Python Version Check", "Virtual Environment Setup"]:
                print(f"❌ Critical step failed: {step_name}")
                print("Installation cannot continue.")
                return False
    
    print("\n" + "=" * 50)
    
    if not failed_steps:
        print("✅ All installation steps completed successfully!")
        print_next_steps()
        return True
    else:
        print(f"⚠️  Installation completed with {len(failed_steps)} warnings:")
        for step in failed_steps:
            print(f"   • {step}")
        print("\nThe system should still work, but some features may be limited.")
        print_next_steps()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)