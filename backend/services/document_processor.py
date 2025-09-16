"""
Document Processor - Handles document ingestion and processing
"""

import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from .text_splitter import TextSplitter

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes and manages document ingestion for RAG pipelines"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_documents: Dict[str, Dict[str, Any]] = {}
        self.text_splitter = TextSplitter()
    
    async def process_file_upload(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded files and extract text content"""
        try:
            filename = file_data.get("filename", f"upload_{uuid.uuid4()}")
            content = file_data.get("content", "")
            file_type = file_data.get("type", "text/plain")
            
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Process based on file type
            if file_type.startswith("text/"):
                extracted_text = await self._process_text_file(content)
            elif file_type == "application/pdf":
                extracted_text = await self._process_pdf_file(content)
            elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                extracted_text = await self._process_docx_file(content)
            else:
                extracted_text = str(content)  # Fallback to string conversion
            
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
            
            logger.info(f"Processed document: {filename} ({len(extracted_text)} chars)")
            
            return {
                "document_id": doc_id,
                "filename": filename,
                "status": "processed",
                "word_count": document_info["word_count"],
                "char_count": document_info["char_count"],
                "content_preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to process document"
            }
    
    async def _process_text_file(self, content: str) -> str:
        """Process plain text files"""
        return content.strip()
    
    async def _process_pdf_file(self, content: bytes) -> str:
        """Process PDF files and extract text"""
        try:
            # For MVP, return mock extraction
            # In production, would use libraries like PyPDF2, pdfplumber, or pymupdf
            return f"[PDF Content Extracted - {len(content)} bytes]\nMock PDF text extraction for development."
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return f"[PDF Processing Error: {str(e)}]"
    
    async def _process_docx_file(self, content: bytes) -> str:
        """Process DOCX files and extract text"""
        try:
            # For MVP, return mock extraction
            # In production, would use python-docx library
            return f"[DOCX Content Extracted - {len(content)} bytes]\nMock DOCX text extraction for development."
        except Exception as e:
            logger.error(f"DOCX processing failed: {e}")
            return f"[DOCX Processing Error: {str(e)}]"
    
    async def batch_process_documents(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple documents in batch"""
        results = {
            "processed": [],
            "failed": [],
            "summary": {
                "total": len(files),
                "success": 0,
                "failed": 0
            }
        }
        
        for file_data in files:
            try:
                result = await self.process_file_upload(file_data)
                if result.get("status") == "processed":
                    results["processed"].append(result)
                    results["summary"]["success"] += 1
                else:
                    results["failed"].append(result)
                    results["summary"]["failed"] += 1
            except Exception as e:
                results["failed"].append({
                    "filename": file_data.get("filename", "unknown"),
                    "error": str(e)
                })
                results["summary"]["failed"] += 1
        
        return results
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get processed document by ID"""
        return self.processed_documents.get(doc_id)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all processed documents"""
        return [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "file_type": doc["file_type"],
                "word_count": doc["word_count"],
                "char_count": doc["char_count"],
                "processed_at": doc["processed_at"]
            }
            for doc in self.processed_documents.values()
        ]
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a processed document"""
        if doc_id in self.processed_documents:
            del self.processed_documents[doc_id]
            logger.info(f"Deleted document: {doc_id}")
            return True
        return False
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get document processing statistics"""
        if not self.processed_documents:
            return {
                "total_documents": 0,
                "total_words": 0,
                "total_chars": 0,
                "file_types": {}
            }
        
        total_words = sum(doc["word_count"] for doc in self.processed_documents.values())
        total_chars = sum(doc["char_count"] for doc in self.processed_documents.values())
        
        file_types = {}
        for doc in self.processed_documents.values():
            file_type = doc["file_type"]
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_documents": len(self.processed_documents),
            "total_words": total_words,
            "total_chars": total_chars,
            "file_types": file_types,
            "average_words_per_doc": total_words / len(self.processed_documents),
            "average_chars_per_doc": total_chars / len(self.processed_documents)
        }
    
    async def extract_embeddings_data(self, doc_id: str) -> Optional[List[Dict[str, Any]]]:
        """Extract data suitable for embedding generation"""
        document = self.get_document(doc_id)
        if not document:
            return None
        
        content = document["content"]
        
        # Split content into chunks for embedding
        chunks = self.text_splitter.split_text(content)
        
        return self.text_splitter.create_chunked_documents(document, chunks)