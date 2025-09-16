#!/usr/bin/env python3
"""
RAG Plugin CLI - Command line tool for plugin development
"""

import argparse
import sys
import os
from pathlib import Path
import json
import yaml
from typing import Dict, Any, Optional

try:
    from .commands import InitCommand, ValidateCommand, TestCommand, BuildCommand, DevServerCommand
except ImportError:
    # Fallback for direct execution
    from commands import InitCommand, ValidateCommand, TestCommand, BuildCommand, DevServerCommand


class PluginCLI:
    """Main CLI application for RAG plugin development"""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.commands = {
            'init': InitCommand(),
            'validate': ValidateCommand(),
            'test': TestCommand(),
            'build': BuildCommand(),
            'dev-server': DevServerCommand()
        }
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser"""
        parser = argparse.ArgumentParser(
            prog='rag-plugin',
            description='RAG Plugin Development CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  rag-plugin init my-vectordb --type vectordb
  rag-plugin validate
  rag-plugin test --local
  rag-plugin build
  rag-plugin dev-server --port 8080
            """
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='RAG Plugin CLI 1.0.0'
        )
        
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Init command
        init_parser = subparsers.add_parser(
            'init',
            help='Initialize a new plugin project'
        )
        init_parser.add_argument('name', help='Plugin name')
        init_parser.add_argument(
            '--type',
            choices=['datasource', 'vectordb', 'llm', 'utility'],
            required=True,
            help='Plugin type'
        )
        init_parser.add_argument(
            '--template',
            choices=['basic', 'advanced', 'custom'],
            default='basic',
            help='Template to use'
        )
        init_parser.add_argument(
            '--author',
            help='Plugin author name'
        )
        init_parser.add_argument(
            '--description',
            help='Plugin description'
        )
        
        # Validate command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate plugin configuration and code'
        )
        validate_parser.add_argument(
            '--path',
            default='.',
            help='Path to plugin directory'
        )
        validate_parser.add_argument(
            '--strict',
            action='store_true',
            help='Enable strict validation mode'
        )
        
        # Test command
        test_parser = subparsers.add_parser(
            'test',
            help='Run plugin tests'
        )
        test_parser.add_argument(
            '--local',
            action='store_true',
            help='Run tests in local environment'
        )
        test_parser.add_argument(
            '--coverage',
            action='store_true',
            help='Generate test coverage report'
        )
        test_parser.add_argument(
            '--path',
            default='.',
            help='Path to plugin directory'
        )
        
        # Build command
        build_parser = subparsers.add_parser(
            'build',
            help='Build plugin package'
        )
        build_parser.add_argument(
            '--output',
            '-o',
            help='Output directory for built package'
        )
        build_parser.add_argument(
            '--format',
            choices=['zip', 'tar.gz'],
            default='zip',
            help='Package format'
        )
        
        # Dev server command
        dev_parser = subparsers.add_parser(
            'dev-server',
            help='Start development server for testing'
        )
        dev_parser.add_argument(
            '--port',
            '-p',
            type=int,
            default=8080,
            help='Server port'
        )
        dev_parser.add_argument(
            '--host',
            default='localhost',
            help='Server host'
        )
        
        return parser
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI application"""
        try:
            parsed_args = self.parser.parse_args(args)
            
            if not parsed_args.command:
                self.parser.print_help()
                return 0
            
            command = self.commands.get(parsed_args.command)
            if not command:
                print(f"Error: Unknown command '{parsed_args.command}'")
                return 1
            
            return command.execute(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
    
    def get_plugin_info(self, path: str = ".") -> Optional[Dict[str, Any]]:
        """Get plugin information from manifest"""
        manifest_file = self._find_manifest_file(path)
        if not manifest_file:
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                if manifest_file.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception:
            return None
    
    def _find_manifest_file(self, path: str) -> Optional[Path]:
        """Find plugin manifest file"""
        plugin_dir = Path(path)
        for filename in ['plugin.yaml', 'plugin.yml', 'plugin.json']:
            manifest_path = plugin_dir / filename
            if manifest_path.exists():
                return manifest_path
        return None


def main():
    """Main entry point for CLI"""
    cli = PluginCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()