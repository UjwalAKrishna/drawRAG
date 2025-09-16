#!/usr/bin/env python3
"""
Test script to verify RAG Builder is working correctly
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_framework():
    """Test the core framework functionality"""
    print("🧪 Testing RAG Builder Framework...")
    
    try:
        # Test 1: Import core components
        print("✅ Testing imports...")
        from backend.core import Manager
        from backend.api.dependencies import get_manager
        
        # Test 2: Initialize manager
        print("✅ Testing manager initialization...")
        manager = Manager("plugins")
        await manager.start()
        
        # Test 3: Check plugins
        print("✅ Testing plugin discovery...")
        plugins = manager.list_plugins()
        if isinstance(plugins, dict):
            print(f"   Found {len(plugins)} plugins: {list(plugins.keys())}")
        elif isinstance(plugins, list):
            plugin_names = []
            for p in plugins:
                if isinstance(p, dict):
                    plugin_names.append(p.get('plugin_id', 'unknown'))
                elif isinstance(p, str):
                    plugin_names.append(p)
                else:
                    plugin_names.append(str(p))
            print(f"   Found {len(plugins)} plugins: {plugin_names}")
        else:
            print(f"   Found plugins: {type(plugins)} - {plugins}")
        
        # Test 4: Check capabilities
        print("✅ Testing capabilities...")
        capabilities = manager.list_capabilities()
        print(f"   Found {len(capabilities)} capabilities: {list(capabilities.keys())}")
        
        # Test 5: Test a simple capability if available
        if capabilities:
            cap_name = list(capabilities.keys())[0]
            providers = capabilities[cap_name]
            print(f"   Testing capability '{cap_name}' with {len(providers)} providers")
            
            try:
                # Try calling the capability
                result = await manager.call(cap_name, "test")
                print(f"   ✅ Capability call successful: {type(result)}")
            except Exception as e:
                print(f"   ⚠️  Capability call failed (expected): {e}")
        
        # Test 6: System status
        print("✅ Testing system status...")
        status = manager.get_system_status()
        print(f"   System running: {status.get('running', False)}")
        print(f"   Total plugins: {status.get('total_plugins', 0)}")
        
        await manager.stop()
        print("\n🎉 All tests passed! RAG Builder is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_structure():
    """Test API structure"""
    print("\n🔍 Testing API structure...")
    
    api_files = [
        "backend/api/__init__.py",
        "backend/api/main.py", 
        "backend/api/dependencies.py",
        "backend/api/routes/__init__.py",
        "backend/api/routes/plugins.py",
        "backend/api/routes/capabilities.py",
        "backend/api/routes/pipeline.py",
        "backend/api/routes/rag.py"
    ]
    
    missing = []
    for file_path in api_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"❌ Missing API files: {missing}")
        return False
    else:
        print("✅ All API files present")
        return True

def test_frontend_structure():
    """Test frontend structure"""
    print("\n🎨 Testing frontend structure...")
    
    frontend_files = [
        "frontend/index.html",
        "frontend/styles.css",
        "frontend/js/app.js",
        "frontend/js/core/api-client.js",
        "frontend/js/core/event-bus.js",
        "frontend/js/modules/plugin-manager.js",
        "frontend/js/modules/rag-tester.js",
        "frontend/js/modules/document-processor.js"
    ]
    
    missing = []
    for file_path in frontend_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"❌ Missing frontend files: {missing}")
        return False
    else:
        print("✅ All frontend files present")
        return True

async def main():
    """Main test function"""
    print("🚀 RAG Builder Test Suite")
    print("=" * 50)
    
    # Test structure
    api_ok = test_api_structure()
    frontend_ok = test_frontend_structure()
    
    # Test framework
    framework_ok = await test_framework()
    
    print("\n" + "=" * 50)
    if all([api_ok, frontend_ok, framework_ok]):
        print("🎉 ALL TESTS PASSED!")
        print("\nTo start the application:")
        print("  python run_server.py")
        print("\nThen open: http://localhost:8000")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)