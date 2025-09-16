"""
Setup script for RAG Plugin CLI
"""

from setuptools import setup, find_packages

setup(
    name="rag-plugin-cli",
    version="1.0.0",
    description="Command line tool for RAG Builder plugin development",
    author="RAG Builder Team",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0",
        "pytest>=7.0",
        "pytest-asyncio>=0.21.0",
    ],
    entry_points={
        "console_scripts": [
            "rag-plugin=cli.rag_plugin_cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)