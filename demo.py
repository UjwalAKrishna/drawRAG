#!/usr/bin/env python3
"""
RAG Builder Demo - Shows the working functionality
"""

import sys
import asyncio
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from models import PipelineConfig, ComponentConfig, ComponentType, QueryRequest
from services.pipeline_manager import PipelineManager
from services.plugin_manager import PluginManager

async def demo_plugin_system():
    """Demonstrate the plugin system"""
    print("🔌 Plugin System Demo")
    print("-" * 30)
    
    pm = PluginManager()
    await pm.load_plugins()
    
    plugins = pm.get_available_plugins()
    
    for plugin_type, plugin_list in plugins.items():
        print(f"\n📦 {plugin_type.upper()} Plugins:")
        for plugin in plugin_list:
            print(f"  • {plugin['name']} v{plugin['version']}")
            if plugin.get('description'):
                print(f"    {plugin['description']}")

async def demo_pipeline_creation():
    """Demonstrate pipeline creation and management"""
    print("\n\n🏗️  Pipeline Creation Demo")
    print("-" * 30)
    
    # Create pipeline manager
    pipeline_manager = PipelineManager()
    
    # Create a sample pipeline
    config = PipelineConfig(
        name="Demo RAG Pipeline",
        description="A demonstration pipeline with SQLite → ChromaDB → OpenAI",
        components=[
            ComponentConfig(
                id="datasource_1",
                type=ComponentType.DATASOURCE,
                subtype="sqlite",
                name="SQLite Database",
                config={
                    "database_path": "./demo_data.db",
                    "table_name": "documents", 
                    "text_column": "content"
                }
            ),
            ComponentConfig(
                id="vectordb_1",
                type=ComponentType.VECTORDB,
                subtype="chroma",
                name="ChromaDB",
                config={
                    "collection_name": "demo_collection",
                    "persist_directory": "./chroma_demo"
                }
            ),
            ComponentConfig(
                id="llm_1",
                type=ComponentType.LLM,
                subtype="openai",
                name="OpenAI GPT-4o-mini",
                config={
                    "api_key": "sk-demo-key-placeholder",
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
        ],
        connections=[]
    )
    
    # Create the pipeline
    pipeline_id = await pipeline_manager.create_pipeline(config)
    print(f"✅ Created pipeline: {pipeline_id}")
    
    # List pipelines
    pipelines = await pipeline_manager.list_pipelines()
    print(f"📋 Total pipelines: {len(pipelines)}")
    
    for pipeline in pipelines:
        print(f"  • {pipeline['name']} ({pipeline['status']})")
        print(f"    Components: {pipeline['component_count']}")
        print(f"    Created: {pipeline['created_at']}")
    
    return pipeline_id

async def demo_query_execution(pipeline_id: str):
    """Demonstrate query execution"""
    print("\n\n🔍 Query Execution Demo")
    print("-" * 30)
    
    pipeline_manager = PipelineManager()
    
    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Explain the concept of neural networks"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        try:
            response = await pipeline_manager.execute_query(
                pipeline_id=pipeline_id,
                query=query,
                options={"include_sources": True}
            )
            
            print(f"✅ Answer: {response.answer}")
            print(f"📚 Sources: {len(response.sources)} documents")
            print(f"⏱️  Processing time: {response.processing_time:.2f}s")
            
            # Show sources
            for i, source in enumerate(response.sources[:2], 1):
                print(f"   {i}. {source.get('title', 'Unknown')} (score: {source.get('score', 'N/A')})")
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def demo_component_validation():
    """Demonstrate component validation"""
    print("\n\n✅ Component Validation Demo")
    print("-" * 30)
    
    pipeline_manager = PipelineManager()
    
    # Test valid configuration
    valid_config = ComponentConfig(
        id="test_sqlite",
        type=ComponentType.DATASOURCE,
        subtype="sqlite",
        name="Test SQLite",
        config={
            "database_path": "test.db",
            "table_name": "docs",
            "text_column": "content"
        }
    )
    
    is_valid = await pipeline_manager.validate_component_config(valid_config)
    print(f"Valid SQLite config: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    # Test invalid configuration
    invalid_config = ComponentConfig(
        id="test_invalid",
        type=ComponentType.DATASOURCE,
        subtype="sqlite",
        name="Invalid SQLite",
        config={}  # Missing required fields
    )
    
    is_valid = await pipeline_manager.validate_component_config(invalid_config)
    print(f"Invalid SQLite config: {'❌ FAIL' if not is_valid else '✅ PASS'} (expected to fail)")

async def main():
    """Run the complete demo"""
    print("🎯 RAG Builder - Complete Functionality Demo")
    print("=" * 50)
    
    try:
        # Demo 1: Plugin System
        await demo_plugin_system()
        
        # Demo 2: Pipeline Creation
        pipeline_id = await demo_pipeline_creation()
        
        # Demo 3: Query Execution
        await demo_query_execution(pipeline_id)
        
        # Demo 4: Component Validation
        await demo_component_validation()
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("\n📝 Next Steps:")
        print("  1. Run 'python run_server.py' to start the web interface")
        print("  2. Open http://localhost:8000/static/index.html")
        print("  3. Drag components to build your RAG pipeline")
        print("  4. Configure components and test queries")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())