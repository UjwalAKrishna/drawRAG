"""
Data Source Plugin Base Class
"""

from abc import abstractmethod
from typing import Dict, List, Any, Optional, AsyncIterator
from .base_plugin import BasePlugin


class BaseDataSourcePlugin(BasePlugin):
    """Base class for data source plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.plugin_type = "datasource"
    
    @abstractmethod
    async def get_documents(self) -> List[Dict[str, Any]]:
        """Retrieve documents from the data source
        
        Returns:
            List[Dict[str, Any]]: List of documents with id, content, and metadata
        """
        pass
    
    async def get_documents_streaming(self) -> AsyncIterator[Dict[str, Any]]:
        """Stream documents from the data source (optional)
        
        Yields:
            Dict[str, Any]: Individual document with id, content, and metadata
        """
        documents = await self.get_documents()
        for doc in documents:
            yield doc
    
    async def query_documents(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query documents with a search term (optional)
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Filtered documents
        """
        # Default implementation: return all documents and let vector DB handle filtering
        documents = await self.get_documents()
        if limit:
            documents = documents[:limit]
        return documents
    
    async def get_document_count(self) -> int:
        """Get total number of documents available
        
        Returns:
            int: Total document count
        """
        documents = await self.get_documents()
        return len(documents)
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get data source metadata
        
        Returns:
            Dict[str, Any]: Metadata about the data source
        """
        return {
            "type": "datasource",
            "total_documents": await self.get_document_count(),
            "supports_streaming": hasattr(self, 'get_documents_streaming'),
            "supports_querying": hasattr(self, 'query_documents')
        }
    
    def validate_document_format(self, document: Dict[str, Any]) -> bool:
        """Validate document format
        
        Args:
            document: Document to validate
            
        Returns:
            bool: True if document format is valid
        """
        required_fields = ["id", "content"]
        return all(field in document for field in required_fields)
    
    async def test_connection(self) -> bool:
        """Test data source connection"""
        if not self.initialized:
            return False
        
        try:
            # Try to get a small sample of documents
            documents = await self.get_documents()
            return len(documents) >= 0  # Even empty is valid
        except Exception:
            return False