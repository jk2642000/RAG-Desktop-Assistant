import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import os
import atexit
import gc
from .logger import rag_logger
from .memory_manager import memory_manager

class VectorStore:
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Lazy load embedding model
        self.embedding_model: Optional[SentenceTransformer] = None
        self._active = True
        atexit.register(self.cleanup)
        
        # Log initialization
        rag_logger.info(f"VectorStore initialized. Current document count: {self.get_document_count()}")
    
    def add_documents(self, documents: List[Dict]):
        """Add documents to the vector store"""
        texts = []
        metadatas = []
        ids = []
        
        # Get existing IDs to avoid duplicates
        try:
            existing_data = self.collection.get()
            existing_ids = set(existing_data['ids'])
            rag_logger.debug(f"Found {len(existing_ids)} existing documents in vector store")
            rag_logger.debug(f"Existing files: {set([meta.get('filename', 'unknown') for meta in existing_data.get('metadatas', [])])}")
        except Exception as e:
            existing_ids = set()
            rag_logger.warning(f"Could not get existing IDs: {e}")
        
        new_docs_added = 0
        skipped_docs = 0
        
        for doc in documents:
            rag_logger.info(f"Processing document: {doc['filename']} with {len(doc['chunks'])} chunks")
            for i, chunk in enumerate(doc['chunks']):
                chunk_id = f"{doc['file_hash']}_{i}"
                
                # Skip if already exists
                if chunk_id in existing_ids:
                    skipped_docs += 1
                    continue
                    
                texts.append(chunk)
                metadatas.append({
                    'filename': doc['filename'],
                    'filepath': doc['filepath'],
                    'chunk_index': i,
                    'file_hash': doc['file_hash']
                })
                ids.append(chunk_id)
                new_docs_added += 1
        
        rag_logger.info(f"New chunks to add: {new_docs_added}, Skipped duplicates: {skipped_docs}")
        
        if texts:
            # Process in batches to handle ChromaDB limits
            batch_size = 100  # Safe batch size
            total_added = 0
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                try:
                    # Generate embeddings for batch
                    batch_embeddings = self._get_embedding_model().encode(batch_texts).tolist()
                    
                    # Add batch to ChromaDB
                    self.collection.add(
                        embeddings=batch_embeddings,
                        documents=batch_texts,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                    total_added += len(batch_texts)
                    rag_logger.info(f"Added batch {i//batch_size + 1}: {len(batch_texts)} chunks")
                    
                except Exception as e:
                    rag_logger.error(f"Failed to add batch {i//batch_size + 1}: {e}")
                    # Try smaller batch size on failure
                    if batch_size > 10:
                        rag_logger.info(f"Retrying with smaller batch size...")
                        smaller_batch_size = batch_size // 2
                        for j in range(i, min(i + batch_size, len(texts)), smaller_batch_size):
                            small_batch_texts = texts[j:j + smaller_batch_size]
                            small_batch_metadatas = metadatas[j:j + smaller_batch_size]
                            small_batch_ids = ids[j:j + smaller_batch_size]
                            
                            try:
                                small_batch_embeddings = self._get_embedding_model().encode(small_batch_texts).tolist()
                                self.collection.add(
                                    embeddings=small_batch_embeddings,
                                    documents=small_batch_texts,
                                    metadatas=small_batch_metadatas,
                                    ids=small_batch_ids
                                )
                                total_added += len(small_batch_texts)
                            except Exception as small_e:
                                rag_logger.error(f"Failed to add small batch: {small_e}")
            
            rag_logger.info(f"Successfully added {total_added} total chunks to vector store")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant documents"""
        rag_logger.debug(f"Searching for: '{query}' (requesting {n_results} results)")
        
        # Generate query embedding with lazy loading
        query_embedding = self._get_embedding_model().encode([query]).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        # Format results
        search_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                search_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
        
        # Log search results
        found_files = list(set([r['metadata']['filename'] for r in search_results]))
        rag_logger.info(f"Search found {len(search_results)} chunks from files: {found_files}")
        
        for i, result in enumerate(search_results[:3]):  # Log first 3 results
            # Clean text for logging to avoid unicode errors
            clean_text = result['text'][:100].encode('ascii', 'ignore').decode('ascii')
            rag_logger.debug(f"Result {i+1}: {clean_text}... (distance: {result['distance']:.3f})")
        
        return search_results
    
    def clear(self):
        """Clear all documents from the vector store"""
        try:
            old_count = self.get_document_count()
            # Delete and recreate collection
            self.client.delete_collection("documents")
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            rag_logger.info(f"Cleared vector store. Removed {old_count} documents")
        except Exception as e:
            rag_logger.error(f"Error clearing vector store: {e}")
    
    def get_document_count(self) -> int:
        """Get total number of document chunks"""
        return self.collection.count()
    
    def remove_document(self, file_hash: str):
        """Remove all chunks of a specific document"""
        # Get all IDs for this document
        results = self.collection.get(
            where={"file_hash": file_hash}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
    
    def _get_embedding_model(self) -> SentenceTransformer:
        """Lazy load embedding model"""
        if self.embedding_model is None:
            # Check memory before loading
            if memory_manager.should_unload_models():
                memory_manager.cleanup_unused_models()
            
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            memory_manager.register_model('sentence_transformer', self.embedding_model, 90)  # ~90MB
            rag_logger.info("Embedding model loaded on demand")
        
        return self.embedding_model
    
    def unload_embedding_model(self):
        """Unload embedding model to free memory"""
        if self.embedding_model is not None:
            memory_manager.unload_model('sentence_transformer')
            self.embedding_model = None
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, '_active') and self._active:
            self._active = False
            try:
                if hasattr(self, 'client'):
                    self.client = None
                self.unload_embedding_model()
            except:
                pass
            gc.collect()
    
    def __del__(self):
        self.cleanup()