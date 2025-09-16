"""
Dev Server Command - Start development server for testing
"""

import asyncio
import threading
import time
from pathlib import Path
from .base_command import BaseCommand


class DevServerCommand(BaseCommand):
    """Start development server for testing plugins"""
    
    def execute(self, args) -> int:
        """Execute dev server command"""
        host = args.host
        port = args.port
        
        self.print_info(f"Starting development server at {host}:{port}")
        
        # Validate plugin directory
        if not self._validate_plugin_directory():
            return 1
        
        try:
            # Start the development server
            self._start_dev_server(host, port)
            return 0
            
        except KeyboardInterrupt:
            self.print_info("Development server stopped")
            return 0
        except Exception as e:
            self.print_error(f"Failed to start development server: {e}")
            return 1
    
    def _validate_plugin_directory(self) -> bool:
        """Validate current directory is a plugin project"""
        if not self.find_manifest_file():
            self.print_error("Not a plugin directory (no plugin.yaml/plugin.json found)")
            return False
        
        if not Path("src").exists():
            self.print_error("Source directory (src/) not found")
            return False
        
        return True
    
    def _start_dev_server(self, host: str, port: int):
        """Start the development server"""
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import json
        
        manifest = self.load_manifest()
        
        class PluginDevHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/api/plugin/info":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(manifest).encode())
                elif self.path == "/api/plugin/status":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    status = {"status": "running", "plugin": manifest.get("name", "Unknown")}
                    self.wfile.write(json.dumps(status).encode())
                else:
                    # Serve static files or development UI
                    super().do_GET()
        
        server = HTTPServer((host, port), PluginDevHandler)
        
        self.print_success(f"Development server running at http://{host}:{port}")
        self.print_info("Available endpoints:")
        print(f"  GET /api/plugin/info - Plugin information")
        print(f"  GET /api/plugin/status - Server status")
        print(f"")
        print(f"Press Ctrl+C to stop the server")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
            self.print_info("Server stopped")