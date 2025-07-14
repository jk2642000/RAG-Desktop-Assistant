import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any
from .analytics import analytics_engine, QueryMetrics

class RAGLogger:
    def __init__(self):
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('RAG_Debug')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with UTF-8 encoding
        log_file = f"logs/rag_debug_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def metric(self, metric_name: str, value: Any, context: Dict = None):
        """Log performance metrics"""
        context_str = f" | Context: {context}" if context else ""
        self.info(f"METRIC: {metric_name} = {value}{context_str}")
    
    def error(self, msg):
        self.logger.error(msg)
    
    def log_query_start(self, question: str) -> str:
        """Start logging a query and return query_id"""
        query_id = str(uuid.uuid4())
        self.info(f"Query started: {query_id} - '{question}'")
        return query_id
    
    def log_query_complete(self, query_id: str, question: str, response: str, 
                          context_length: int, chunk_count: int, search_time: float,
                          generation_time: float, total_time: float, sources: list,
                          search_distances: list):
        """Log complete query metrics"""
        metrics = QueryMetrics(
            query_id=query_id,
            timestamp=datetime.now(),
            question=question,
            response=response,
            context_length=context_length,
            chunk_count=chunk_count,
            search_time=search_time,
            generation_time=generation_time,
            total_time=total_time,
            sources=sources,
            search_distances=search_distances
        )
        
        analytics_engine.log_query(metrics)
        self.info(f"Query completed: {query_id} - Time: {total_time:.2f}s, Context: {context_length} chars")
    
    def log_document_processed(self, doc_id: str, filename: str, file_size: int,
                              chunk_count: int, avg_chunk_size: float):
        """Log document processing metrics"""
        analytics_engine.log_document(doc_id, filename, file_size, chunk_count, avg_chunk_size)
        self.info(f"Document processed: {filename} - {chunk_count} chunks, avg size: {avg_chunk_size:.0f} chars")

# Global logger instance
rag_logger = RAGLogger()