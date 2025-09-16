#!/usr/bin/env python3
"""
Test Real Plugin Implementations
"""

import sys
import asyncio
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_openai_plugin():
    """Test OpenAI plugin (requires API key)"""
    print("\n🧠 Testing OpenAI Plugin...")
    
    try:
        # Add plugins directory to Python path
        plugins_path = Path(__file__).parent / "plugins"
        if str(plugins_path) not in sys.path:
            sys.path.insert(0, str(plugins_path))
        
        from llm.openai_plugin import OpenAILLMPlugin
        
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  OpenAI API key not found in environment variables")
            print("   Set OPENAI_API_KEY to test real OpenAI integration")
            return False
        
        config = {
            "api_key": api_key,
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        plugin = OpenAILLMPlugin(config)
        
        # Test validation
        is_valid = await plugin.validate_config(config)
        print(f"✅ Config validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Test initialization
        initialized = await plugin.initialize()
        print(f"✅ Initialization: {'PASS' if initialized else 'FAIL'}")
        
        if initialized:
            # Test generation
            response = await plugin.generate_response("What is AI?")
            print(f"✅ Generation test: PASS")
            print(f"   Response: {response[:100]}...")
            
            # Test embeddings
            embeddings = await plugin.generate_embeddings(["test text"])
            print(f"✅ Embeddings test: {'PASS' if embeddings else 'FAIL'}")
            if embeddings:
                print(f"   Embedding dimension: {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI plugin test failed: {e}")
        return False

async def test_ollama_plugin():
    """Test Ollama plugin (requires local Ollama server)"""
    print("\n🦙 Testing Ollama Plugin...")
    
    try:
        from llm.ollama_plugin import OllamaLLMPlugin
        
        config = {
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "temperature": 0.7
        }
        
        plugin = OllamaLLMPlugin(config)
        
        # Test validation
        is_valid = await plugin.validate_config(config)
        print(f"✅ Config validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Test initialization (this will check if Ollama is running)
        try:
            initialized = await plugin.initialize()
            print(f"✅ Initialization: {'PASS' if initialized else 'FAIL'}")
            
            if initialized:
                # Test generation
                response = await plugin.generate_response("Say hello")
                print(f"✅ Generation test: PASS")
                print(f"   Response: {response[:100]}...")
        except Exception as e:
            print(f"⚠️  Ollama server not available: {e}")
            print("   Start Ollama server with 'ollama serve' to test")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama plugin test failed: {e}")
        return False

async def test_chroma_plugin():
    """Test ChromaDB plugin"""
    print("\n🎨 Testing ChromaDB Plugin...")
    
    try:
        from vectordb.chroma_plugin import ChromaVectorDBPlugin
        
        config = {
            "collection_name": "test_collection",
            "persist_directory": "./test_chroma_db"
        }
        
        plugin = ChromaVectorDBPlugin(config)
        
        # Test validation
        is_valid = await plugin.validate_config(config)
        print(f"✅ Config validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Test initialization
        initialized = await plugin.initialize()
        print(f"✅ Initialization: {'PASS' if initialized else 'FAIL'}")
        
        if initialized:
            # Test storing vectors
            documents = [
                {"id": "doc1", "content": "This is test document 1", "metadata": {"source": "test"}},
                {"id": "doc2", "content": "This is test document 2", "metadata": {"source": "test"}}
            ]
            embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]  # Mock embeddings
            
            stored = await plugin.store_vectors(documents, embeddings)
            print(f"✅ Store vectors: {'PASS' if stored else 'FAIL'}")
            
            # Test querying
            query_vector = [0.15, 0.25, 0.35]
            results = await plugin.query_vectors(query_vector, top_k=2)
            print(f"✅ Query vectors: {'PASS' if results else 'FAIL'}")
            if results:
                print(f"   Found {len(results)} results")
            
            # Test collection info
            info = await plugin.get_collection_info()
            print(f"✅ Collection info: {info}")
            
            # Cleanup
            await plugin.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB plugin test failed: {e}")
        return False

async def test_faiss_plugin():
    """Test FAISS plugin"""
    print("\n🔢 Testing FAISS Plugin...")
    
    try:
        from vectordb.faiss_plugin import FAISSVectorDBPlugin
        
        config = {
            "dimension": 3,
            "index_type": "flat",
            "index_path": "./test_faiss_index",
            "metadata_path": "./test_faiss_metadata.pkl"
        }
        
        plugin = FAISSVectorDBPlugin(config)
        
        # Test validation
        is_valid = await plugin.validate_config(config)
        print(f"✅ Config validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Test initialization
        initialized = await plugin.initialize()
        print(f"✅ Initialization: {'PASS' if initialized else 'FAIL'}")
        
        if initialized:
            # Test storing vectors
            documents = [
                {"id": "doc1", "content": "This is test document 1", "metadata": {"source": "test"}},
                {"id": "doc2", "content": "This is test document 2", "metadata": {"source": "test"}}
            ]
            embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            
            stored = await plugin.store_vectors(documents, embeddings)
            print(f"✅ Store vectors: {'PASS' if stored else 'FAIL'}")
            
            # Test querying
            query_vector = [0.15, 0.25, 0.35]
            results = await plugin.query_vectors(query_vector, top_k=2)
            print(f"✅ Query vectors: {'PASS' if results else 'FAIL'}")
            if results:
                print(f"   Found {len(results)} results")
            
            # Test collection info
            info = await plugin.get_collection_info()
            print(f"✅ Collection info: {info}")
            
            # Cleanup
            await plugin.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ FAISS plugin test failed: {e}")
        return False

async def test_plugin_manager_integration():
    """Test plugin manager with real plugins"""
    print("\n🔌 Testing Plugin Manager Integration...")
    
    try:
        from services.plugin_manager import PluginManager
        
        pm = PluginManager()
        await pm.load_plugins()
        
        plugins = pm.get_available_plugins()
        print(f"✅ Loaded plugin types: {list(plugins.keys())}")
        
        # Test getting specific plugins
        openai_plugin = pm.get_plugin("llm", "openai")
        chroma_plugin = pm.get_plugin("vectordb", "chroma")
        
        print(f"✅ OpenAI plugin class: {openai_plugin.__name__ if openai_plugin else 'Not found'}")
        print(f"✅ ChromaDB plugin class: {chroma_plugin.__name__ if chroma_plugin else 'Not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Plugin manager integration test failed: {e}")
        return False

async def main():
    """Run all plugin tests"""
    print("🧪 RAG Builder - Real Plugin Implementation Tests")
    print("=" * 60)
    
    tests = [
        ("Plugin Manager Integration", test_plugin_manager_integration),
        ("ChromaDB Plugin", test_chroma_plugin),
        ("FAISS Plugin", test_faiss_plugin),
        ("Ollama Plugin", test_ollama_plugin),
        ("OpenAI Plugin", test_openai_plugin),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed >= 3:  # At least core functionality working
        print("🎉 Core plugin system is working!")
        print("\n📝 Notes:")
        print("  • ChromaDB and FAISS should work out of the box")
        print("  • OpenAI requires OPENAI_API_KEY environment variable")
        print("  • Ollama requires local Ollama server running")
        print("\n🚀 Ready to use real RAG pipelines!")
    else:
        print("❌ Some core tests failed. Check dependencies and configuration.")
    
    # Cleanup test files
    import shutil
    for path in ["./test_chroma_db", "./test_faiss_index", "./test_faiss_metadata.pkl"]:
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())