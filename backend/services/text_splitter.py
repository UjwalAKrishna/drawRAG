"""
Text Splitter - Handles text chunking for document processing
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class TextSplitter:
    """Splits text into chunks for embedding and processing"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence break
                sentence_break = text.rfind('.', start, end)
                if sentence_break > start + self.chunk_size // 2:
                    end = sentence_break + 1
                else:
                    # Look for word break
                    word_break = text.rfind(' ', start, end)
                    if word_break > start + self.chunk_size // 2:
                        end = word_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap if end < len(text) else end
        
        return chunks
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                if len(paragraph) <= self.chunk_size:
                    current_chunk = paragraph
                else:
                    # Split large paragraph
                    sub_chunks = self.split_text(paragraph)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences, respecting chunk size"""
        import re
        
        # Simple sentence splitting (can be improved with proper NLP)
        sentences = re.split(r'[.!?]+\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                if len(sentence) <= self.chunk_size:
                    current_chunk = sentence
                else:
                    # Split long sentence
                    word_chunks = self.split_text(sentence)
                    chunks.extend(word_chunks[:-1])
                    current_chunk = word_chunks[-1] if word_chunks else ""
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def create_chunked_documents(self, document: dict, chunks: List[str]) -> List[dict]:
        """Create document chunks with metadata"""
        chunked_docs = []
        
        for i, chunk in enumerate(chunks):
            chunked_doc = {
                "id": f"{document.get('id', 'doc')}_chunk_{i}",
                "content": chunk,
                "metadata": {
                    **document.get("metadata", {}),
                    "document_id": document.get("id"),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk),
                    "original_filename": document.get("filename")
                }
            }
            chunked_docs.append(chunked_doc)
        
        return chunked_docs
    
    def get_optimal_chunk_size(self, text: str, target_chunks: int = 10) -> int:
        """Calculate optimal chunk size for a given text and target number of chunks"""
        text_length = len(text)
        if target_chunks <= 0:
            return self.chunk_size
        
        optimal_size = max(text_length // target_chunks, 100)  # Minimum 100 chars
        return min(optimal_size, self.chunk_size * 2)  # Maximum 2x default chunk size
    
    def analyze_text_structure(self, text: str) -> dict:
        """Analyze text structure to recommend splitting strategy"""
        lines = text.split('\n')
        paragraphs = text.split('\n\n')
        
        # Count sentences (rough estimate)
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        
        return {
            "total_chars": len(text),
            "total_words": len(text.split()),
            "total_lines": len(lines),
            "total_paragraphs": len([p for p in paragraphs if p.strip()]),
            "estimated_sentences": len([s for s in sentences if s.strip()]),
            "average_paragraph_length": sum(len(p) for p in paragraphs if p.strip()) / max(len([p for p in paragraphs if p.strip()]), 1),
            "recommended_strategy": self._recommend_splitting_strategy(text)
        }
    
    def _recommend_splitting_strategy(self, text: str) -> str:
        """Recommend the best splitting strategy for the text"""
        lines = text.split('\n')
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        avg_paragraph_length = sum(len(p) for p in paragraphs) / max(len(paragraphs), 1)
        
        if avg_paragraph_length < self.chunk_size * 0.5:
            return "paragraphs"
        elif len(lines) > len(paragraphs) * 2:
            return "sentences"
        else:
            return "sliding_window"