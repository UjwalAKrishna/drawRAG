"""
Framework Command - Interact with the framework directly
"""

import asyncio
import sys
import os
from pathlib import Path
from .base_command import BaseCommand


class FrameworkCommand(BaseCommand):
    """Interact with the framework directly"""
    
    def execute(self, args) -> int:
        """Execute framework command"""
        # Add backend to path to access framework
        backend_path = Path(__file__).parent.parent.parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        action = getattr(args, 'action', 'status')
        
        if action == 'status':
            return self._show_status()
        elif action == 'test':
            return self._test_framework()
        elif action == 'metrics':
            return self._show_metrics()
        elif action == 'plugins':
            return self._list_plugins()
        elif action == 'capabilities':
            return self._list_capabilities()
        else:
            self.print_error(f"Unknown action: {action}")
            return 1
    
    def _show_status(self) -> int:
        """Show framework status"""
        try:
            from core import Manager
            
            async def get_status():
                manager = Manager("plugins")
                await manager.start()
                
                status = manager.get_system_status()
                plugins = manager.list_plugins()
                capabilities = manager.list_capabilities()
                
                self.print_success("Framework Status")
                print(f"  🏃 Running: {status.get('framework_running', False)}")
                print(f"  📦 Plugins: {len(plugins)}")
                print(f"  🔧 Capabilities: {len(capabilities)}")
                print(f"  💾 Cache Size: {status.get('cache_size', 0)}")
                print(f"  📊 Total Calls: {status.get('total_capabilities', 0)}")
                
                await manager.stop()
            
            asyncio.run(get_status())
            return 0
            
        except Exception as e:
            self.print_error(f"Failed to get status: {e}")
            return 1
    
    def _test_framework(self) -> int:
        """Test framework functionality"""
        try:
            from core import Manager
            
            async def test():
                self.print_info("Testing framework...")
                manager = Manager("plugins")
                await manager.start()
                
                # Test basic functionality
                plugins = manager.list_plugins()
                capabilities = manager.list_capabilities()
                
                self.print_success(f"✅ Framework started: {len(plugins)} plugins")
                self.print_success(f"✅ Capabilities available: {len(capabilities)}")
                
                # Test capability calls
                if capabilities:
                    for cap_name in list(capabilities.keys())[:3]:  # Test first 3
                        try:
                            providers = manager.discover_providers(cap_name)
                            self.print_success(f"✅ Capability '{cap_name}': {len(providers)} providers")
                        except Exception as e:
                            self.print_warning(f"⚠️ Capability '{cap_name}': {e}")
                
                # Test advanced features
                metrics = manager.get_metrics()
                self.print_success(f"✅ Metrics: {metrics.get('calls', 0)} calls, {metrics.get('cache_hit_rate', 0):.2%} cache hit rate")
                
                await manager.stop()
                self.print_success("🎉 Framework test completed!")
            
            asyncio.run(test())
            return 0
            
        except Exception as e:
            self.print_error(f"Framework test failed: {e}")
            return 1
    
    def _show_metrics(self) -> int:
        """Show detailed framework metrics"""
        try:
            from core import Manager
            
            async def get_metrics():
                manager = Manager("plugins")
                await manager.start()
                
                metrics = manager.get_metrics()
                
                self.print_success("Framework Metrics")
                print(f"  📞 Total Calls: {metrics.get('calls', 0)}")
                print(f"  ❌ Errors: {metrics.get('errors', 0)}")
                print(f"  💾 Cache Hits: {metrics.get('cache_hits', 0)}")
                print(f"  📈 Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.2%}")
                print(f"  ⚡ Error Rate: {metrics.get('error_rate', 0):.2%}")
                
                plugins_per_cap = metrics.get('plugins_per_capability', {})
                if plugins_per_cap:
                    print(f"  🔧 Capability Distribution:")
                    for cap, count in list(plugins_per_cap.items())[:5]:
                        print(f"    {cap}: {count} providers")
                
                await manager.stop()
            
            asyncio.run(get_metrics())
            return 0
            
        except Exception as e:
            self.print_error(f"Failed to get metrics: {e}")
            return 1
    
    def _list_plugins(self) -> int:
        """List all loaded plugins"""
        try:
            from core import Manager
            
            async def list_plugins():
                manager = Manager("plugins")
                await manager.start()
                
                plugins = manager.list_plugins()
                
                self.print_success(f"Loaded Plugins ({len(plugins)})")
                for plugin_id in plugins:
                    info = manager.get_plugin_info(plugin_id)
                    if info:
                        capabilities = list(info.get('capabilities', {}).keys())
                        print(f"  📦 {plugin_id}")
                        print(f"    🔧 Capabilities: {', '.join(capabilities[:3])}")
                        if len(capabilities) > 3:
                            print(f"    ... and {len(capabilities) - 3} more")
                
                await manager.stop()
            
            asyncio.run(list_plugins())
            return 0
            
        except Exception as e:
            self.print_error(f"Failed to list plugins: {e}")
            return 1
    
    def _list_capabilities(self) -> int:
        """List all available capabilities"""
        try:
            from core import Manager
            
            async def list_capabilities():
                manager = Manager("plugins")
                await manager.start()
                
                capabilities = manager.list_capabilities()
                
                self.print_success(f"Available Capabilities ({len(capabilities)})")
                for cap_name, providers in capabilities.items():
                    print(f"  🔧 {cap_name}")
                    print(f"    📦 Providers: {', '.join(providers)}")
                    
                    # Get help for this capability
                    help_text = manager.help(cap_name)
                    if "Description:" in help_text:
                        desc_line = [line for line in help_text.split('\n') if 'Description:' in line]
                        if desc_line:
                            desc = desc_line[0].split('Description:', 1)[1].strip()
                            print(f"    📝 {desc}")
                
                await manager.stop()
            
            asyncio.run(list_capabilities())
            return 0
            
        except Exception as e:
            self.print_error(f"Failed to list capabilities: {e}")
            return 1