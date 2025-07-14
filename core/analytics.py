import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
import numpy as np

@dataclass
class QueryMetrics:
    query_id: str
    timestamp: datetime
    question: str
    response: str
    context_length: int
    chunk_count: int
    search_time: float
    generation_time: float
    total_time: float
    sources: List[str]
    search_distances: List[float]
    user_rating: Optional[int] = None
    feedback: Optional[str] = None

class AnalyticsEngine:
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_metrics (
                query_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                question TEXT,
                response TEXT,
                context_length INTEGER,
                chunk_count INTEGER,
                search_time REAL,
                generation_time REAL,
                total_time REAL,
                sources TEXT,
                search_distances TEXT,
                user_rating INTEGER,
                feedback TEXT
            )
        ''')
        
        # Document metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_metrics (
                doc_id TEXT PRIMARY KEY,
                filename TEXT,
                file_size INTEGER,
                chunk_count INTEGER,
                avg_chunk_size REAL,
                upload_time DATETIME,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Performance trends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_trends (
                date DATE PRIMARY KEY,
                avg_response_time REAL,
                avg_context_length REAL,
                total_queries INTEGER,
                avg_rating REAL,
                success_rate REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_query(self, metrics: QueryMetrics):
        """Log query metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO query_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.query_id,
            metrics.timestamp,
            metrics.question,
            metrics.response,
            metrics.context_length,
            metrics.chunk_count,
            metrics.search_time,
            metrics.generation_time,
            metrics.total_time,
            json.dumps(metrics.sources),
            json.dumps(metrics.search_distances),
            metrics.user_rating,
            metrics.feedback
        ))
        
        conn.commit()
        conn.close()
    
    def log_document(self, doc_id: str, filename: str, file_size: int, 
                    chunk_count: int, avg_chunk_size: float):
        """Log document metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO document_metrics 
            (doc_id, filename, file_size, chunk_count, avg_chunk_size, upload_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (doc_id, filename, file_size, chunk_count, avg_chunk_size, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def update_user_feedback(self, query_id: str, rating: int, feedback: str = None):
        """Update user feedback for a query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE query_metrics SET user_rating = ?, feedback = ? WHERE query_id = ?
        ''', (rating, feedback, query_id))
        
        conn.commit()
        conn.close()
    
    def increment_document_usage(self, filenames: List[str]):
        """Increment usage count for documents used in queries"""
        if not filenames:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for filename in filenames:
            cursor.execute('''
                UPDATE document_metrics SET usage_count = usage_count + 1 WHERE filename = ?
            ''', (filename,))
        
        conn.commit()
        conn.close()
    
    def get_performance_insights(self, days: int = 7) -> Dict:
        """Get performance insights for last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Query performance metrics
        cursor.execute('''
            SELECT 
                AVG(total_time) as avg_response_time,
                AVG(context_length) as avg_context_length,
                COUNT(*) as total_queries,
                AVG(user_rating) as avg_rating,
                AVG(CASE WHEN LENGTH(response) > 50 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(search_time) as avg_search_time,
                AVG(generation_time) as avg_generation_time
            FROM query_metrics 
            WHERE timestamp > ?
        ''', (since_date,))
        
        result = cursor.fetchone()
        
        # Get top failing queries
        cursor.execute('''
            SELECT question, AVG(user_rating) as avg_rating, COUNT(*) as count
            FROM query_metrics 
            WHERE timestamp > ? AND user_rating IS NOT NULL
            GROUP BY question
            ORDER BY avg_rating ASC
            LIMIT 5
        ''', (since_date,))
        
        failing_queries = cursor.fetchall()
        
        # Get document usage stats
        cursor.execute('''
            SELECT filename, usage_count, chunk_count, avg_chunk_size
            FROM document_metrics
            ORDER BY usage_count DESC
            LIMIT 10
        ''')
        
        doc_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'performance': {
                'avg_response_time': result[0] or 0,
                'avg_context_length': result[1] or 0,
                'total_queries': result[2] or 0,
                'avg_rating': result[3] or 0,
                'success_rate': result[4] or 0,
                'avg_search_time': result[5] or 0,
                'avg_generation_time': result[6] or 0
            },
            'failing_queries': failing_queries,
            'document_stats': doc_stats
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get AI-powered optimization recommendations"""
        insights = self.get_performance_insights()
        recommendations = []
        
        perf = insights['performance']
        
        # Response time optimization
        if perf['avg_response_time'] > 5.0:
            recommendations.append("🚀 Consider reducing chunk size or context length for faster responses")
        
        # Context optimization
        if perf['avg_context_length'] > 8000:
            recommendations.append("📝 Context length is high - consider better chunk filtering")
        
        # Search optimization
        if perf['avg_search_time'] > 2.0:
            recommendations.append("🔍 Search time is slow - consider optimizing embeddings")
        
        # Rating optimization
        if perf['avg_rating'] and perf['avg_rating'] < 3.5:
            recommendations.append("⭐ Low user ratings - review prompt engineering")
        
        # Success rate optimization
        if perf['success_rate'] < 0.8:
            recommendations.append("✅ Low success rate - improve document chunking strategy")
        
        return recommendations

# Global analytics instance
analytics_engine = AnalyticsEngine()