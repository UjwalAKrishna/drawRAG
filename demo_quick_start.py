#!/usr/bin/env python3
"""
Quick demo script to showcase RAG Builder functionality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def demo():
    """Quick demo of RAG Builder"""
    print("🎯 RAG Builder Quick Demo")
    print("=" * 40)
    
    try:
        from backend.core import Manager
        
        # Initialize
        print("🚀 Starting RAG Builder...")
        manager = Manager("plugins")
        await manager.start()
        
        # Show plugins
        plugins = manager.list_plugins()
        print(f"\n🔌 Loaded Plugins: {len(plugins) if plugins else 0}")
        
        # Show capabilities  
        capabilities = manager.list_capabilities()
        print(f"⚡ Available Capabilities: {len(capabilities) if capabilities else 0}")
        
        if capabilities:
            print("\n📋 Capabilities:")
            for cap_name, providers in list(capabilities.items())[:5]:  # Show first 5
                print(f"  • {cap_name} ({len(providers)} providers)")
        
        # Try a simple capability
        if 'add' in capabilities:
            print(f"\n🧮 Testing 'add' capability...")
            result = await manager.call('add', 5, 3)
            print(f"   5 + 3 = {result}")
        
        if 'clean_text' in capabilities:
            print(f"\n📝 Testing 'clean_text' capability...")
            result = await manager.call('clean_text', "  Hello   World!  ")
            print(f"   Cleaned: '{result}'")
        
        await manager.stop()
        
        print(f"\n✅ Demo completed successfully!")
        print(f"\n🌐 To start the web interface:")
        print(f"   python3 run_server.py")
        print(f"   Then open: http://localhost:8000")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo())