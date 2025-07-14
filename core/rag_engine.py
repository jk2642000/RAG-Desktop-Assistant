import os
import re
import time
from typing import List, Dict, Tuple
from .vector_store import VectorStore
from .gemini_processor import GeminiProcessor
from .nlp_processor import NLPProcessor
from .logger import rag_logger
from .analytics import analytics_engine
from .memory_manager import memory_manager
import atexit
import gc

class RAGEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        
        # Try to initialize Gemini, fallback to NLP processor
        rag_logger.info("Initializing RAG Engine...")
        try:
            self.processor = GeminiProcessor()
            self.using_gemini = True
            rag_logger.info("RAG Engine initialized with Google Gemini")
            print("[OK] RAG Engine initialized with Google Gemini")
        except Exception as e:
            error_msg = f"Gemini initialization failed: {str(e)}"
            rag_logger.warning(error_msg)
            print(f"[WARNING] {error_msg}")
            print("✓ Falling back to local NLP processor")
            rag_logger.info("Falling back to local NLP processor")
            self.processor = NLPProcessor()
            self.using_gemini = False
        
        self._active = True
        atexit.register(self.cleanup)
    
    def add_documents(self, documents: List[Dict]):
        """Add documents to the RAG system"""
        rag_logger.info(f"Adding {len(documents)} documents to RAG system")
        for doc in documents:
            rag_logger.info(f"Document: {doc['filename']} ({doc['chunk_count']} chunks)")
        self.vector_store.add_documents(documents)
    
    def query(self, question: str, documents: List[Dict] = None) -> Tuple[str, List[str], str]:
        """Query the RAG system with comprehensive metrics tracking"""
        # Start timing and logging
        start_time = time.time()
        query_id = rag_logger.log_query_start(question)
        
        if documents:
            rag_logger.info(f"Adding {len(documents)} new documents with query")
            self.add_documents(documents)
        
        # Search for relevant context using vector similarity
        search_start = time.time()
        n_results = 8 if any(word in question.lower() for word in ['total', 'overall', 'summary', 'all', 'entire']) else 5
        search_results = self.vector_store.search(question, n_results=n_results)
        search_time = time.time() - search_start
        
        if not search_results:
            return "I don't have any relevant information to answer your question. Please upload some documents first.", []
        
        # Prepare context and sources with better organization
        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"[Context {i+1}]: {result['text']}")
        context = "\n\n".join(context_parts)
        sources = list(set([result['metadata']['filename'] for result in search_results]))
        
        # Use processor (Gemini or NLP fallback) to generate response
        generation_start = time.time()
        processor_type = "Gemini" if self.using_gemini else "Local NLP"
        rag_logger.info(f"Using {processor_type} processor for response generation")
        
        if hasattr(self.processor, 'process_question') and 'stream_callback' in self.processor.process_question.__code__.co_varnames:
            # Gemini with streaming support
            stream_callback = documents[0].get('stream_callback') if documents and len(documents) > 0 else None
            response = self.processor.process_question(question, context, search_results, stream_callback)
        else:
            # Fallback or NLP processor
            response = self.processor.process_question(question, context, search_results)
        generation_time = time.time() - generation_start
        
        rag_logger.info(f"{processor_type} response generated in {generation_time:.2f}s")
        
        # Calculate total time and metrics
        total_time = time.time() - start_time
        search_distances = [r.get('distance', 0) for r in search_results]
        
        # Log comprehensive metrics
        rag_logger.log_query_complete(
            query_id=query_id,
            question=question,
            response=response,
            context_length=len(context),
            chunk_count=len(search_results),
            search_time=search_time,
            generation_time=generation_time,
            total_time=total_time,
            sources=sources,
            search_distances=search_distances
        )
        
        # Increment document usage count
        if sources:
            analytics_engine.increment_document_usage(sources)
        
        # Log performance metrics
        rag_logger.metric("search_time", search_time, {"n_results": n_results})
        rag_logger.metric("generation_time", generation_time, {"context_length": len(context)})
        rag_logger.metric("total_response_time", total_time)
        rag_logger.metric("context_efficiency", len(context) / len(search_results) if search_results else 0)
        
        return response, sources, query_id
    

    
    def clear_documents(self):
        """Clear all documents from the system"""
        rag_logger.info("Clearing all documents from RAG system")
        self.vector_store.clear()
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        model_info = {
            'document_chunks': self.vector_store.get_document_count(),
            'model_type': f'Google Gemini Pro ({"Active" if self.using_gemini else "Failed"})' if hasattr(self, 'using_gemini') else 'Local NLP Engine',
            'features': [
                'Semantic Vector Search',
                'AI-Powered Response Generation' if self.using_gemini else 'Pattern-based NLP',
                'Multi-Document Context',
                'Source Citation',
                'Real-time Processing'
            ]
        }
        # Add memory usage info
        memory_info = memory_manager.get_memory_usage()
        model_info['memory_usage_mb'] = round(memory_info['rss_mb'], 1)
        model_info['memory_percent'] = round(memory_info['percent'], 1)
        
        return model_info
    
    def cleanup(self):
        """Clean up all resources"""
        if hasattr(self, '_active') and self._active:
            self._active = False
            if hasattr(self, 'vector_store'):
                self.vector_store.cleanup()
            if hasattr(self, 'processor'):
                if hasattr(self.processor, 'cleanup'):
                    self.processor.cleanup()
            
            # Force memory cleanup
            memory_manager.force_cleanup()
            gc.collect()
    
    def __del__(self):
        self.cleanup()