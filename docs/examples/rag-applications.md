# 🤖 RAG Application Examples

Complete examples of building Retrieval-Augmented Generation applications with RAG Builder v2.0.

## 📚 Document Q&A System

A complete RAG system for answering questions about your documents.

### 1. **Document Ingestion Plugin**

```python
# plugins/document_ingestion.py

import os
import hashlib
from typing import List, Dict, Any
from datetime import datetime
import PyPDF2
import docx
from sdk.data_source_plugin import DataSourcePlugin

class DocumentIngestor(DataSourcePlugin):
    """Plugin for ingesting and processing documents."""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['.pdf', '.txt', '.docx', '.md']
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word document."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + self.chunk_size // 2:
                    chunk_text = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunk_id = hashlib.md5(chunk_text.encode()).hexdigest()
            
            chunks.append({
                'id': chunk_id,
                'text': chunk_text.strip(),
                'start_pos': start,
                'end_pos': end,
                'length': len(chunk_text)
            })
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif file_ext in ['.txt', '.md']:
            text = self.extract_text_from_txt(file_path)
        
        # Get file metadata
        stat = os.stat(file_path)
        file_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Create chunks
        chunks = self.chunk_text(text)
        
        return {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': stat.st_size,
            'file_hash': file_hash,
            'processed_at': datetime.utcnow().isoformat(),
            'text_length': len(text),
            'chunk_count': len(chunks),
            'chunks': chunks
        }
    
    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all supported documents in a directory."""
        results = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in self.supported_formats:
                    try:
                        result = self.process_document(file_path)
                        results.append(result)
                        self.logger.info(f"Processed: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Error processing {file_path}: {str(e)}")
                        results.append({
                            'file_path': file_path,
                            'error': str(e),
                            'processed_at': datetime.utcnow().isoformat()
                        })
        
        return results
```

### 2. **Embedding Generation Plugin**

```python
# plugins/embedding_generator.py

import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sdk.llm_plugin import LLMPlugin

class EmbeddingGenerator(LLMPlugin):
    """Plugin for generating text embeddings."""
    
    def __init__(self):
        super().__init__()
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None
        self.embedding_dimension = 384
    
    def load_model(self):
        """Load the embedding model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            return self.model
        except Exception as e:
            raise Exception(f"Error loading embedding model: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if self.model is None:
            self.model = self.load_model()
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = self.generate_embeddings([text])
        return embeddings[0]
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar embeddings to query."""
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.compute_similarity(query_embedding, candidate)
            similarities.append({
                'index': i,
                'similarity': similarity
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
```

### 3. **Vector Database Plugin**

```python
# plugins/vector_database.py

import json
import pickle
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sdk.vector_db_plugin import VectorDBPlugin

class ChromaVectorDB(VectorDBPlugin):
    """Vector database plugin using ChromaDB."""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.collection = None
        self.collection_name = "document_chunks"
    
    def initialize_index(self):
        """Initialize ChromaDB client and collection."""
        try:
            self.client = chromadb.PersistentClient(
                path="./vector_db",
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Document chunks for RAG"}
            )
            
            return self.collection
        except Exception as e:
            raise Exception(f"Error initializing vector database: {str(e)}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents with embeddings to the vector database."""
        if self.collection is None:
            self.initialize_index()
        
        try:
            ids = []
            embeddings = []
            documents_list = []
            metadatas = []
            
            for doc in documents:
                chunk_id = doc['id']
                embedding = doc['embedding']
                text = doc['text']
                metadata = {
                    'file_path': doc.get('file_path', ''),
                    'file_name': doc.get('file_name', ''),
                    'chunk_index': doc.get('chunk_index', 0),
                    'start_pos': doc.get('start_pos', 0),
                    'end_pos': doc.get('end_pos', 0)
                }
                
                ids.append(chunk_id)
                embeddings.append(embedding)
                documents_list.append(text)
                metadatas.append(metadata)
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_list,
                metadatas=metadatas
            )
            
            return True
        except Exception as e:
            raise Exception(f"Error adding documents: {str(e)}")
    
    def search_similar(self, query_embedding: List[float], 
                      top_k: int = 5, 
                      filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.collection is None:
            self.initialize_index()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            search_results = []
            
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                search_results.append(result)
            
            return search_results
        except Exception as e:
            raise Exception(f"Error searching documents: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        if self.collection is None:
            self.initialize_index()
        
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'status': 'active'
            }
        except Exception as e:
            return {
                'collection_name': self.collection_name,
                'error': str(e),
                'status': 'error'
            }
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs."""
        if self.collection is None:
            self.initialize_index()
        
        try:
            self.collection.delete(ids=document_ids)
            return True
        except Exception as e:
            raise Exception(f"Error deleting documents: {str(e)}")
```

### 4. **Question Answering Plugin**

```python
# plugins/question_answering.py

from typing import List, Dict, Any
import openai
from sdk.llm_plugin import LLMPlugin

class QuestionAnswering(LLMPlugin):
    """Plugin for answering questions using retrieved context."""
    
    def __init__(self):
        super().__init__()
        self.model_name = "gpt-3.5-turbo"
        self.max_context_length = 4000
        self.temperature = 0.1
    
    def load_model(self):
        """Initialize OpenAI client."""
        api_key = self.config.get('openai_api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found in configuration")
        
        return openai.OpenAI(api_key=api_key)
    
    def create_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Create context from retrieved documents."""
        context_parts = []
        current_length = 0
        
        for doc in retrieved_docs:
            doc_text = doc['text']
            # Add document source info
            source_info = f"[Source: {doc['metadata'].get('file_name', 'Unknown')}]"
            doc_with_source = f"{source_info}\n{doc_text}\n"
            
            if current_length + len(doc_with_source) > self.max_context_length:
                break
            
            context_parts.append(doc_with_source)
            current_length += len(doc_with_source)
        
        return "\n".join(context_parts)
    
    def generate_answer(self, question: str, context: str) -> Dict[str, Any]:
        """Generate answer using LLM with context."""
        if self.model is None:
            self.model = self.load_model()
        
        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        Follow these guidelines:
        1. Only answer based on the information in the context
        2. If the context doesn't contain enough information, say so
        3. Cite the source when possible
        4. Be concise but comprehensive
        5. If multiple sources contradict each other, mention this"""
        
        user_prompt = f"""Context:
{context}

Question: {question}

Please provide a detailed answer based on the context above."""
        
        try:
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            return {
                'answer': answer,
                'model': self.model_name,
                'context_length': len(context),
                'tokens_used': response.usage.total_tokens
            }
        except Exception as e:
            raise Exception(f"Error generating answer: {str(e)}")
    
    def answer_question(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete question answering pipeline."""
        # Create context from retrieved documents
        context = self.create_context(retrieved_docs)
        
        if not context.strip():
            return {
                'answer': "I couldn't find relevant information to answer your question.",
                'context_length': 0,
                'sources': []
            }
        
        # Generate answer
        result = self.generate_answer(question, context)
        
        # Add source information
        sources = []
        for doc in retrieved_docs:
            source = {
                'file_name': doc['metadata'].get('file_name', 'Unknown'),
                'similarity': doc.get('similarity', 0),
                'text_preview': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
            }
            sources.append(source)
        
        result['sources'] = sources
        result['question'] = question
        
        return result
```

### 5. **Complete RAG System Plugin**

```python
# plugins/rag_system.py

from typing import List, Dict, Any
from sdk.base_plugin import BasePlugin

class RAGSystem(BasePlugin):
    """Complete RAG system that orchestrates all components."""
    
    def __init__(self):
        super().__init__()
        # Initialize components (would be injected in real implementation)
        self.document_ingestor = None
        self.embedding_generator = None
        self.vector_db = None
        self.qa_system = None
        
        # Load components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all RAG components."""
        from .document_ingestion import DocumentIngestor
        from .embedding_generator import EmbeddingGenerator
        from .vector_database import ChromaVectorDB
        from .question_answering import QuestionAnswering
        
        self.document_ingestor = DocumentIngestor()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_db = ChromaVectorDB()
        self.qa_system = QuestionAnswering()
    
    def ingest_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Ingest documents into the RAG system."""
        results = {
            'processed_files': [],
            'failed_files': [],
            'total_chunks': 0,
            'success_count': 0,
            'error_count': 0
        }
        
        for file_path in file_paths:
            try:
                # Process document
                doc_result = self.document_ingestor.process_document(file_path)
                
                # Generate embeddings for chunks
                chunk_texts = [chunk['text'] for chunk in doc_result['chunks']]
                embeddings = self.embedding_generator.generate_embeddings(chunk_texts)
                
                # Prepare documents for vector DB
                vector_docs = []
                for i, chunk in enumerate(doc_result['chunks']):
                    vector_doc = {
                        'id': chunk['id'],
                        'text': chunk['text'],
                        'embedding': embeddings[i],
                        'file_path': doc_result['file_path'],
                        'file_name': doc_result['file_name'],
                        'chunk_index': i,
                        'start_pos': chunk['start_pos'],
                        'end_pos': chunk['end_pos']
                    }
                    vector_docs.append(vector_doc)
                
                # Add to vector database
                self.vector_db.add_documents(vector_docs)
                
                results['processed_files'].append({
                    'file_path': file_path,
                    'chunks': len(doc_result['chunks']),
                    'status': 'success'
                })
                
                results['total_chunks'] += len(doc_result['chunks'])
                results['success_count'] += 1
                
            except Exception as e:
                results['failed_files'].append({
                    'file_path': file_path,
                    'error': str(e),
                    'status': 'failed'
                })
                results['error_count'] += 1
        
        return results
    
    def ask_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Ask a question and get an answer from the RAG system."""
        try:
            # Generate embedding for the question
            question_embedding = self.embedding_generator.generate_single_embedding(question)
            
            # Search for relevant documents
            retrieved_docs = self.vector_db.search_similar(
                query_embedding=question_embedding,
                top_k=top_k
            )
            
            if not retrieved_docs:
                return {
                    'question': question,
                    'answer': "I couldn't find any relevant documents to answer your question.",
                    'sources': [],
                    'status': 'no_results'
                }
            
            # Generate answer
            answer_result = self.qa_system.answer_question(question, retrieved_docs)
            answer_result['status'] = 'success'
            
            return answer_result
            
        except Exception as e:
            return {
                'question': question,
                'error': str(e),
                'status': 'error'
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        try:
            vector_stats = self.vector_db.get_collection_stats()
            
            return {
                'vector_db': vector_stats,
                'embedding_model': self.embedding_generator.model_name,
                'qa_model': self.qa_system.model_name,
                'status': 'operational'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def search_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search documents without generating an answer."""
        try:
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            results = self.vector_db.search_similar(
                query_embedding=query_embedding,
                top_k=top_k
            )
            return results
        except Exception as e:
            raise Exception(f"Error searching documents: {str(e)}")
```

## 🎯 Usage Examples

### Setup and Document Ingestion

```python
# Example: Setting up and using the RAG system

# Initialize the RAG system
rag = RAGSystem()

# Ingest documents
document_paths = [
    "documents/company_handbook.pdf",
    "documents/product_guide.docx",
    "documents/faq.txt"
]

# Process documents
ingestion_result = rag.ingest_documents(document_paths)
print(f"Processed {ingestion_result['success_count']} files successfully")
print(f"Total chunks created: {ingestion_result['total_chunks']}")

# Ask questions
questions = [
    "What is the company's vacation policy?",
    "How do I reset my password?",
    "What are the product specifications?"
]

for question in questions:
    result = rag.ask_question(question)
    print(f"\nQ: {question}")
    print(f"A: {result['answer']}")
    print(f"Sources: {len(result['sources'])} documents")
```

### API Integration Example

```python
# Example API endpoint for the RAG system
from flask import Flask, request, jsonify

app = Flask(__name__)
rag_system = RAGSystem()

@app.route('/api/ingest', methods=['POST'])
def ingest_documents():
    data = request.json
    file_paths = data.get('file_paths', [])
    
    result = rag_system.ingest_documents(file_paths)
    return jsonify(result)

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    top_k = data.get('top_k', 5)
    
    result = rag_system.ask_question(question, top_k)
    return jsonify(result)

@app.route('/api/search', methods=['POST'])
def search_documents():
    data = request.json
    query = data.get('query', '')
    top_k = data.get('top_k', 10)
    
    results = rag_system.search_documents(query, top_k)
    return jsonify({'results': results})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = rag_system.get_system_stats()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

This complete RAG application example demonstrates how to build a production-ready document Q&A system using RAG Builder's plugin architecture. Each component is modular and can be easily extended or replaced.