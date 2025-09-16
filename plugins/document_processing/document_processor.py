"""
Document Processing Plugin - Handles document upload and processing
"""

import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Import the core plugin interface
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from core.plugin_framework import PluginInterface

logger = logging.getLogger(__name__)


class DocumentProcessorPlugin(PluginInterface):
    """Document processing plugin for RAG Builder"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.upload_dir = Path(config.get("upload_dir", "uploads"))
        self.max_file_size = config.get("max_file_size", 10 * 1024 * 1024)  # 10MB
        self.processed_documents: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> bool:
        """Initialize the document processor"""
        try:
            self.upload_dir.mkdir(exist_ok=True, parents=True)
            self.initialized = True
            logger.info("Document processor plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize document processor: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        self.processed_documents.clear()
        self.initialized = False
    
    def get_capabilities(self) -> List[str]:
        """Get plugin capabilities"""
        return ["process_documents", "extract_text", "batch_processing"]
    
    async def execute(self, input_data: Dict[str, Any], config: Dict[str, Any], 
                     previous_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document processing"""
        if "files" in input_data:
            return await self.process_files(input_data["files"])
        elif "file" in input_data:
            return await self.process_file(input_data["file"])
        else:
            return {"error": "No files provided for processing"}
    
    async def process_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single file"""
        try:
            filename = file_data.get("filename", f"upload_{uuid.uuid4()}")
            content = file_data.get("content", "")
            file_type = file_data.get("type", "text/plain")
            
            # Validate file size
            if len(str(content)) > self.max_file_size:
                return {
                    "status": "error",
                    "error": "File size exceeds maximum allowed size"
                }
            
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Process based on file type
            extracted_text = await self._extract_text(content, file_type)
            
            # Store document metadata
            document_info = {
                "id": doc_id,
                "filename": filename,
                "file_type": file_type,
                "content": extracted_text,
                "processed_at": datetime.now(),
                "word_count": len(extracted_text.split()),
                "char_count": len(extracted_text)
            }
            
            self.processed_documents[doc_id] = document_info
            
            return {
                "status": "success",
                "document_id": doc_id,
                "filename": filename,
                "word_count": document_info["word_count"],
                "char_count": document_info["char_count"],
                "content": extracted_text
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> DocumentProcessorPlugin:
    """Create plugin instance"""
    return DocumentProcessorPlugin(config)