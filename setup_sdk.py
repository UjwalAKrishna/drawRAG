"""
Setup script for RAG Builder SDK
"""

from setuptools import setup, find_packages

setup(
    name="rag-builder-sdk",
    version="1.0.0",
    description="Software Development Kit for RAG Builder plugins",
    author="RAG Builder Team",
    packages=find_packages(include=['sdk', 'sdk.*']),
    install_requires=[
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "flake8>=4.0",
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