#!/usr/bin/env python3
"""
Test vector store functionality
"""
import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vector_store import VectorStore
from core.document_processor import DocumentProcessor

def test_document_addition():
    """Test adding documents to vector store"""
    vector_store = VectorStore()
    
    # Create test document
    test_content = "This is a test document about artificial intelligence and machine learning."
    test_doc = {
        'filename': 'test_doc.txt',
        'filepath': '/tmp/test_doc.txt',
        'text': test_content,
        'chunks': [test_content],
        'file_hash': 'test_hash_123',
        'chunk_count': 1
    }
    
    # Add document
    vector_store.add_documents([test_doc])
    
    # Verify document was added
    doc_count = vector_store.get_document_count()
    assert doc_count > 0, "Document should be added to vector store"
    
    print(f"[PASS] Document addition test - {doc_count} documents in store")

def test_document_search():
    """Test searching documents in vector store"""
    vector_store = VectorStore()
    
    # Create test documents
    docs = [
        {
            'filename': 'ai_doc.txt',
            'filepath': '/tmp/ai_doc.txt',
            'text': 'Artificial intelligence is transforming technology.',
            'chunks': ['Artificial intelligence is transforming technology.'],
            'file_hash': 'ai_hash_123',
            'chunk_count': 1
        },
        {
            'filename': 'ml_doc.txt',
            'filepath': '/tmp/ml_doc.txt', 
            'text': 'Machine learning algorithms process data patterns.',
            'chunks': ['Machine learning algorithms process data patterns.'],
            'file_hash': 'ml_hash_456',
            'chunk_count': 1
        }
    ]
    
    # Add documents
    vector_store.add_documents(docs)
    
    # Test search
    results = vector_store.search("artificial intelligence", n_results=2)
    
    assert len(results) > 0, "Search should return results"
    assert any('artificial' in result['text'].lower() for result in results), "Results should be relevant"
    
    # Check metadata
    for result in results:
        assert 'metadata' in result, "Results should have metadata"
        assert 'filename' in result['metadata'], "Metadata should include filename"
    
    print(f"[PASS] Document search test - {len(results)} results found")

def test_document_processor_integration():
    """Test document processor with vector store"""
    # Create temporary text file
    test_file = os.path.join(tempfile.gettempdir(), "test_integration.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("This is a test document for integration testing. It contains information about RAG systems.")
    
    try:
        # Process document
        processor = DocumentProcessor()
        doc_data = processor.process_document(test_file)
        
        # Verify processing
        assert doc_data['chunk_count'] > 0, "Document should be chunked"
        assert len(doc_data['text']) > 0, "Document should have text content"
        
        # Add to vector store
        vector_store = VectorStore()
        vector_store.add_documents([doc_data])
        
        # Search processed document
        results = vector_store.search("RAG systems", n_results=1)
        assert len(results) > 0, "Should find processed document"
        
        print("[PASS] Document processor integration test")
        
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_document_addition()
    test_document_search()
    test_document_processor_integration()
    print("All vector store tests passed!")