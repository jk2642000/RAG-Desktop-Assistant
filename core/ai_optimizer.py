"""
AI-Powered RAG System Optimizer
Automatically improves system performance based on usage patterns
"""

import numpy as np
from typing import Dict, List, Tuple
from .analytics import analytics_engine
from .logger import rag_logger
import json
import sqlite3
from datetime import datetime, timedelta

class AIOptimizer:
    def __init__(self):
        self.optimization_history = []
        
    def analyze_performance_patterns(self) -> Dict:
        """Analyze system performance patterns using AI techniques"""
        insights = analytics_engine.get_performance_insights(days=30)
        
        # Get detailed query data for analysis
        conn = sqlite3.connect(analytics_engine.db_path)
        cursor = conn.cursor()
        
        # Analyze response time patterns
        cursor.execute('''
            SELECT search_time, generation_time, context_length, chunk_count, user_rating
            FROM query_metrics 
            WHERE timestamp > datetime('now', '-30 days')
            AND user_rating IS NOT NULL
        ''')
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return {"status": "insufficient_data"}
        
        # Convert to numpy arrays for analysis
        search_times = np.array([row[0] for row in data])
        gen_times = np.array([row[1] for row in data])
        context_lengths = np.array([row[2] for row in data])
        chunk_counts = np.array([row[3] for row in data])
        ratings = np.array([row[4] for row in data])
        
        # AI-powered pattern analysis
        patterns = {
            'optimal_context_length': self._find_optimal_context_length(context_lengths, ratings),
            'optimal_chunk_count': self._find_optimal_chunk_count(chunk_counts, ratings),
            'performance_bottlenecks': self._identify_bottlenecks(search_times, gen_times, ratings),
            'quality_factors': self._analyze_quality_factors(context_lengths, chunk_counts, ratings)
        }
        
        return patterns
    
    def _find_optimal_context_length(self, context_lengths: np.ndarray, ratings: np.ndarray) -> Dict:
        """Find optimal context length using correlation analysis"""
        if len(context_lengths) < 10:
            return {"status": "insufficient_data"}
        
        # Bin context lengths and calculate average ratings
        bins = np.linspace(context_lengths.min(), context_lengths.max(), 10)
        bin_indices = np.digitize(context_lengths, bins)
        
        bin_ratings = []
        bin_centers = []
        
        for i in range(1, len(bins)):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                bin_ratings.append(np.mean(ratings[mask]))
                bin_centers.append((bins[i-1] + bins[i]) / 2)
        
        if not bin_ratings:
            return {"status": "no_data"}
        
        # Find optimal range
        best_idx = np.argmax(bin_ratings)
        optimal_length = bin_centers[best_idx]
        
        return {
            "optimal_length": int(optimal_length),
            "confidence": bin_ratings[best_idx],
            "current_avg": int(np.mean(context_lengths)),
            "recommendation": "increase" if optimal_length > np.mean(context_lengths) else "decrease"
        }
    
    def _find_optimal_chunk_count(self, chunk_counts: np.ndarray, ratings: np.ndarray) -> Dict:
        """Find optimal chunk count using statistical analysis"""
        if len(chunk_counts) < 10:
            return {"status": "insufficient_data"}
        
        # Group by chunk count and analyze ratings
        unique_counts = np.unique(chunk_counts)
        count_ratings = []
        
        for count in unique_counts:
            mask = chunk_counts == count
            if np.sum(mask) >= 3:  # Need at least 3 samples
                avg_rating = np.mean(ratings[mask])
                count_ratings.append((count, avg_rating, np.sum(mask)))
        
        if not count_ratings:
            return {"status": "no_data"}
        
        # Find best performing chunk count
        best_count, best_rating, sample_size = max(count_ratings, key=lambda x: x[1])
        
        return {
            "optimal_count": int(best_count),
            "confidence": best_rating,
            "sample_size": sample_size,
            "current_avg": int(np.mean(chunk_counts))
        }
    
    def _identify_bottlenecks(self, search_times: np.ndarray, gen_times: np.ndarray, ratings: np.ndarray) -> Dict:
        """Identify performance bottlenecks using correlation analysis"""
        total_times = search_times + gen_times
        
        # Calculate correlations with ratings
        search_corr = np.corrcoef(search_times, ratings)[0, 1] if len(search_times) > 1 else 0
        gen_corr = np.corrcoef(gen_times, ratings)[0, 1] if len(gen_times) > 1 else 0
        
        bottlenecks = []
        
        # Identify bottlenecks
        if np.mean(search_times) > 2.0:
            bottlenecks.append({
                "type": "search",
                "severity": "high" if np.mean(search_times) > 5.0 else "medium",
                "avg_time": float(np.mean(search_times)),
                "correlation_with_rating": float(search_corr)
            })
        
        if np.mean(gen_times) > 3.0:
            bottlenecks.append({
                "type": "generation",
                "severity": "high" if np.mean(gen_times) > 8.0 else "medium",
                "avg_time": float(np.mean(gen_times)),
                "correlation_with_rating": float(gen_corr)
            })
        
        return {
            "bottlenecks": bottlenecks,
            "search_time_stats": {
                "mean": float(np.mean(search_times)),
                "std": float(np.std(search_times)),
                "p95": float(np.percentile(search_times, 95))
            },
            "generation_time_stats": {
                "mean": float(np.mean(gen_times)),
                "std": float(np.std(gen_times)),
                "p95": float(np.percentile(gen_times, 95))
            }
        }
    
    def _analyze_quality_factors(self, context_lengths: np.ndarray, chunk_counts: np.ndarray, ratings: np.ndarray) -> Dict:
        """Analyze factors affecting response quality"""
        
        # Calculate correlations
        context_quality_corr = np.corrcoef(context_lengths, ratings)[0, 1] if len(context_lengths) > 1 else 0
        chunk_quality_corr = np.corrcoef(chunk_counts, ratings)[0, 1] if len(chunk_counts) > 1 else 0
        
        # Identify high and low quality patterns
        high_quality_mask = ratings >= 4.0
        low_quality_mask = ratings <= 2.0
        
        quality_analysis = {
            "context_length_correlation": float(context_quality_corr),
            "chunk_count_correlation": float(chunk_quality_corr),
        }
        
        if np.sum(high_quality_mask) > 0:
            quality_analysis["high_quality_patterns"] = {
                "avg_context_length": float(np.mean(context_lengths[high_quality_mask])),
                "avg_chunk_count": float(np.mean(chunk_counts[high_quality_mask]))
            }
        
        if np.sum(low_quality_mask) > 0:
            quality_analysis["low_quality_patterns"] = {
                "avg_context_length": float(np.mean(context_lengths[low_quality_mask])),
                "avg_chunk_count": float(np.mean(chunk_counts[low_quality_mask]))
            }
        
        return quality_analysis
    
    def generate_optimization_plan(self) -> List[Dict]:
        """Generate AI-powered optimization plan"""
        patterns = self.analyze_performance_patterns()
        
        if patterns.get("status") == "insufficient_data":
            return [{"type": "info", "message": "Collecting more data for AI optimization..."}]
        
        optimizations = []
        
        # Context length optimization
        if "optimal_context_length" in patterns:
            ctx_opt = patterns["optimal_context_length"]
            if ctx_opt.get("status") != "insufficient_data":
                if abs(ctx_opt["optimal_length"] - ctx_opt["current_avg"]) > 500:
                    optimizations.append({
                        "type": "context_length",
                        "action": ctx_opt["recommendation"],
                        "current": ctx_opt["current_avg"],
                        "recommended": ctx_opt["optimal_length"],
                        "confidence": ctx_opt["confidence"],
                        "priority": "high" if abs(ctx_opt["optimal_length"] - ctx_opt["current_avg"]) > 1000 else "medium"
                    })
        
        # Chunk count optimization
        if "optimal_chunk_count" in patterns:
            chunk_opt = patterns["optimal_chunk_count"]
            if chunk_opt.get("status") != "insufficient_data":
                if abs(chunk_opt["optimal_count"] - chunk_opt["current_avg"]) > 1:
                    optimizations.append({
                        "type": "chunk_count",
                        "current": chunk_opt["current_avg"],
                        "recommended": chunk_opt["optimal_count"],
                        "confidence": chunk_opt["confidence"],
                        "priority": "medium"
                    })
        
        # Performance bottleneck fixes
        if "performance_bottlenecks" in patterns:
            bottlenecks = patterns["performance_bottlenecks"]["bottlenecks"]
            for bottleneck in bottlenecks:
                optimizations.append({
                    "type": "performance",
                    "bottleneck_type": bottleneck["type"],
                    "severity": bottleneck["severity"],
                    "avg_time": bottleneck["avg_time"],
                    "priority": "high" if bottleneck["severity"] == "high" else "medium"
                })
        
        return optimizations
    
    def apply_optimizations(self, optimizations: List[Dict]) -> Dict:
        """Apply AI-recommended optimizations"""
        applied = []
        failed = []
        
        for opt in optimizations:
            try:
                if opt["type"] == "context_length":
                    # This would require updating the RAG engine configuration
                    rag_logger.info(f"AI Optimization: Recommend {opt['action']} context length to {opt['recommended']}")
                    applied.append(opt)
                
                elif opt["type"] == "chunk_count":
                    rag_logger.info(f"AI Optimization: Recommend using {opt['recommended']} chunks per query")
                    applied.append(opt)
                
                elif opt["type"] == "performance":
                    rag_logger.warning(f"AI Optimization: {opt['bottleneck_type']} bottleneck detected (avg: {opt['avg_time']:.2f}s)")
                    applied.append(opt)
                    
            except Exception as e:
                rag_logger.error(f"Failed to apply optimization {opt['type']}: {e}")
                failed.append(opt)
        
        return {
            "applied": applied,
            "failed": failed,
            "timestamp": datetime.now().isoformat()
        }

# Global optimizer instance
ai_optimizer = AIOptimizer()