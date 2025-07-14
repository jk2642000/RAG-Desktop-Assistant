import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
import re
from typing import Dict, List, Tuple
from collections import Counter
from .analytics import analytics_engine
import json

class MLAnalytics:
    """Advanced ML-powered analytics for RAG system optimization"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        
    def get_query_insights(self, days: int = 30) -> Dict:
        """Get ML-powered insights from query patterns"""
        conn = sqlite3.connect(analytics_engine.db_path)
        
        # Get recent queries
        query = """
        SELECT question, response, user_rating, total_time, context_length, 
               chunk_count, search_distances, sources
        FROM query_metrics 
        WHERE timestamp > datetime('now', '-{} days')
        """.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {"error": "No data available"}
        
        insights = {}
        
        # 1. Question Pattern Analysis
        insights['question_patterns'] = self._analyze_question_patterns(df)
        
        # 2. Response Quality Analysis
        insights['response_quality'] = self._analyze_response_quality(df)
        
        # 3. Performance Bottlenecks
        insights['performance_bottlenecks'] = self._identify_bottlenecks(df)
        
        # 4. Context Optimization
        insights['context_optimization'] = self._analyze_context_usage(df)
        
        # 5. User Satisfaction Patterns
        insights['satisfaction_patterns'] = self._analyze_satisfaction(df)
        
        # 6. Failure Pattern Analysis
        insights['failure_patterns'] = self._analyze_failures(df)
        
        return insights
    
    def _analyze_question_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze question patterns using NLP clustering"""
        questions = df['question'].dropna().tolist()
        if len(questions) < 5:
            return {"error": "Insufficient data"}
        
        try:
            # TF-IDF vectorization
            tfidf_matrix = self.vectorizer.fit_transform(questions)
            
            # Clustering
            n_clusters = min(5, len(questions) // 2)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Analyze clusters
            cluster_analysis = {}
            feature_names = self.vectorizer.get_feature_names_out()
            
            for i in range(n_clusters):
                cluster_questions = [q for j, q in enumerate(questions) if clusters[j] == i]
                cluster_center = kmeans.cluster_centers_[i]
                top_features = np.argsort(cluster_center)[-5:][::-1]
                
                cluster_analysis[f'cluster_{i}'] = {
                    'size': len(cluster_questions),
                    'keywords': [feature_names[idx] for idx in top_features],
                    'sample_questions': cluster_questions[:3],
                    'avg_performance': self._get_cluster_performance(df, cluster_questions)
                }
            
            # Question complexity analysis
            complexity_analysis = self._analyze_question_complexity(questions)
            
            return {
                'clusters': cluster_analysis,
                'complexity': complexity_analysis,
                'recommendations': self._generate_question_recommendations(cluster_analysis)
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_response_quality(self, df: pd.DataFrame) -> Dict:
        """Analyze response quality using sentiment and coherence"""
        responses = df['response'].dropna().tolist()
        ratings = df['user_rating'].dropna().tolist()
        
        if not responses:
            return {"error": "No response data"}
        
        # Sentiment analysis
        sentiments = []
        coherence_scores = []
        
        for response in responses:
            # Sentiment
            blob = TextBlob(response)
            sentiments.append(blob.sentiment.polarity)
            
            # Coherence (simple metric based on sentence structure)
            sentences = response.split('.')
            coherence = len([s for s in sentences if len(s.strip()) > 10]) / max(len(sentences), 1)
            coherence_scores.append(coherence)
        
        # Response length analysis
        lengths = [len(r) for r in responses]
        
        # Quality patterns
        quality_patterns = self._identify_quality_patterns(df, sentiments, coherence_scores)
        
        return {
            'sentiment_stats': {
                'avg_sentiment': np.mean(sentiments),
                'sentiment_std': np.std(sentiments),
                'positive_ratio': len([s for s in sentiments if s > 0.1]) / len(sentiments)
            },
            'coherence_stats': {
                'avg_coherence': np.mean(coherence_scores),
                'coherence_std': np.std(coherence_scores)
            },
            'length_stats': {
                'avg_length': np.mean(lengths),
                'optimal_length_range': self._find_optimal_length(df, lengths),
            },
            'quality_patterns': quality_patterns,
            'improvement_suggestions': self._generate_quality_improvements(quality_patterns)
        }
    
    def _identify_bottlenecks(self, df: pd.DataFrame) -> Dict:
        """Identify performance bottlenecks using statistical analysis"""
        # Response time analysis
        times = df['total_time'].dropna()
        context_lengths = df['context_length'].dropna()
        chunk_counts = df['chunk_count'].dropna()
        
        # Correlation analysis
        correlations = {}
        if len(times) > 5:
            correlations['time_vs_context'] = np.corrcoef(times, context_lengths)[0,1] if len(context_lengths) == len(times) else 0
            correlations['time_vs_chunks'] = np.corrcoef(times, chunk_counts)[0,1] if len(chunk_counts) == len(times) else 0
        
        # Bottleneck identification
        bottlenecks = []
        
        # High response time threshold
        time_threshold = np.percentile(times, 90) if len(times) > 0 else 5.0
        slow_queries = df[df['total_time'] > time_threshold]
        
        if len(slow_queries) > 0:
            bottlenecks.append({
                'type': 'slow_response',
                'count': len(slow_queries),
                'avg_time': slow_queries['total_time'].mean(),
                'common_patterns': self._extract_slow_query_patterns(slow_queries)
            })
        
        # Context size issues
        large_context = df[df['context_length'] > 5000]
        if len(large_context) > 0:
            bottlenecks.append({
                'type': 'large_context',
                'count': len(large_context),
                'avg_context': large_context['context_length'].mean(),
                'impact_on_time': large_context['total_time'].mean()
            })
        
        return {
            'correlations': correlations,
            'bottlenecks': bottlenecks,
            'optimization_recommendations': self._generate_performance_recommendations(bottlenecks, correlations)
        }
    
    def _analyze_context_usage(self, df: pd.DataFrame) -> Dict:
        """Analyze how context is being used and optimized"""
        context_data = df[['context_length', 'chunk_count', 'user_rating', 'total_time']].dropna()
        
        if context_data.empty:
            return {"error": "No context data"}
        
        # Optimal context analysis
        context_efficiency = context_data['context_length'] / context_data['chunk_count']
        
        # Find sweet spot for context length vs performance
        context_bins = pd.cut(context_data['context_length'], bins=5)
        context_performance = context_data.groupby(context_bins).agg({
            'user_rating': 'mean',
            'total_time': 'mean',
            'chunk_count': 'mean'
        })
        
        return {
            'context_efficiency': {
                'avg_chars_per_chunk': context_efficiency.mean(),
                'efficiency_std': context_efficiency.std()
            },
            'optimal_ranges': self._find_optimal_context_ranges(context_performance),
            'context_recommendations': self._generate_context_recommendations(context_data)
        }
    
    def _analyze_satisfaction(self, df: pd.DataFrame) -> Dict:
        """Analyze user satisfaction patterns"""
        rated_queries = df[df['user_rating'].notna()]
        
        if rated_queries.empty:
            return {"error": "No rating data"}
        
        # Satisfaction by question type
        satisfaction_by_type = self._categorize_questions_by_satisfaction(rated_queries)
        
        # Time vs satisfaction correlation
        time_satisfaction_corr = np.corrcoef(
            rated_queries['total_time'], 
            rated_queries['user_rating']
        )[0,1] if len(rated_queries) > 5 else 0
        
        return {
            'overall_satisfaction': rated_queries['user_rating'].mean(),
            'satisfaction_distribution': rated_queries['user_rating'].value_counts().to_dict(),
            'satisfaction_by_type': satisfaction_by_type,
            'time_impact': time_satisfaction_corr,
            'improvement_areas': self._identify_satisfaction_improvements(rated_queries)
        }
    
    def _analyze_failures(self, df: pd.DataFrame) -> Dict:
        """Analyze failure patterns and common issues"""
        # Low-rated responses (1-2 stars)
        failures = df[df['user_rating'] <= 2]
        
        if failures.empty:
            return {"message": "No significant failures detected"}
        
        # Common failure patterns
        failure_questions = failures['question'].tolist()
        failure_responses = failures['response'].tolist()
        
        # Pattern extraction
        common_failure_words = self._extract_failure_keywords(failure_questions, failure_responses)
        
        return {
            'failure_rate': len(failures) / len(df),
            'common_failure_patterns': common_failure_words,
            'failure_characteristics': {
                'avg_response_time': failures['total_time'].mean(),
                'avg_context_length': failures['context_length'].mean(),
                'common_response_patterns': self._analyze_failure_responses(failure_responses)
            },
            'prevention_strategies': self._generate_failure_prevention_strategies(failures)
        }
    
    def _generate_question_recommendations(self, cluster_analysis: Dict) -> List[str]:
        """Generate recommendations based on question patterns"""
        recommendations = []
        
        for cluster_id, data in cluster_analysis.items():
            if data['avg_performance']['avg_rating'] < 3.5:
                recommendations.append(
                    f"Improve handling of '{', '.join(data['keywords'][:2])}' type questions"
                )
        
        return recommendations
    
    def _generate_quality_improvements(self, quality_patterns: Dict) -> List[str]:
        """Generate response quality improvement suggestions"""
        improvements = []
        
        if quality_patterns.get('low_coherence_count', 0) > 0:
            improvements.append("Improve response structure and coherence")
        
        if quality_patterns.get('negative_sentiment_ratio', 0) > 0.3:
            improvements.append("Reduce negative sentiment in responses")
        
        return improvements
    
    def _generate_performance_recommendations(self, bottlenecks: List, correlations: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'slow_response':
                recommendations.append("Optimize response generation for complex queries")
            elif bottleneck['type'] == 'large_context':
                recommendations.append("Implement better context chunking and filtering")
        
        if correlations.get('time_vs_context', 0) > 0.7:
            recommendations.append("Strong correlation between context size and response time - optimize context selection")
        
        return recommendations
    
    # Helper methods (simplified implementations)
    def _get_cluster_performance(self, df: pd.DataFrame, questions: List[str]) -> Dict:
        cluster_data = df[df['question'].isin(questions)]
        return {
            'avg_rating': cluster_data['user_rating'].mean() if not cluster_data['user_rating'].isna().all() else 0,
            'avg_time': cluster_data['total_time'].mean()
        }
    
    def _analyze_question_complexity(self, questions: List[str]) -> Dict:
        complexities = []
        for q in questions:
            # Simple complexity metric
            complexity = len(q.split()) + len(re.findall(r'[?]', q)) * 2
            complexities.append(complexity)
        
        return {
            'avg_complexity': np.mean(complexities),
            'complexity_distribution': np.histogram(complexities, bins=3)[0].tolist()
        }
    
    def _identify_quality_patterns(self, df: pd.DataFrame, sentiments: List, coherence: List) -> Dict:
        return {
            'low_coherence_count': len([c for c in coherence if c < 0.5]),
            'negative_sentiment_ratio': len([s for s in sentiments if s < -0.1]) / len(sentiments)
        }
    
    def _find_optimal_length(self, df: pd.DataFrame, lengths: List) -> Tuple[int, int]:
        # Find length range with highest ratings
        if df['user_rating'].isna().all():
            return (100, 500)  # Default range
        
        df_with_length = df.copy()
        df_with_length['response_length'] = lengths[:len(df)]
        
        # Group by length ranges and find optimal
        length_bins = pd.cut(df_with_length['response_length'], bins=5)
        length_performance = df_with_length.groupby(length_bins)['user_rating'].mean()
        
        best_bin = length_performance.idxmax()
        return (int(best_bin.left), int(best_bin.right))
    
    def _extract_slow_query_patterns(self, slow_queries: pd.DataFrame) -> List[str]:
        questions = slow_queries['question'].tolist()
        # Extract common words in slow queries
        all_words = ' '.join(questions).lower().split()
        common_words = [word for word, count in Counter(all_words).most_common(5)]
        return common_words
    
    def _find_optimal_context_ranges(self, context_performance: pd.DataFrame) -> Dict:
        if context_performance.empty:
            return {}
        
        best_rating_range = context_performance['user_rating'].idxmax()
        best_time_range = context_performance['total_time'].idxmin()
        
        return {
            'best_for_rating': str(best_rating_range),
            'best_for_speed': str(best_time_range)
        }
    
    def _generate_context_recommendations(self, context_data: pd.DataFrame) -> List[str]:
        recommendations = []
        
        avg_context = context_data['context_length'].mean()
        if avg_context > 3000:
            recommendations.append("Consider reducing average context length for better performance")
        
        return recommendations
    
    def _categorize_questions_by_satisfaction(self, rated_queries: pd.DataFrame) -> Dict:
        # Simple categorization by question words
        categories = {}
        
        for _, row in rated_queries.iterrows():
            question = row['question'].lower()
            rating = row['user_rating']
            
            if 'calculate' in question or 'math' in question:
                category = 'calculation'
            elif 'what' in question or 'who' in question:
                category = 'factual'
            elif 'how' in question:
                category = 'procedural'
            else:
                category = 'other'
            
            if category not in categories:
                categories[category] = []
            categories[category].append(rating)
        
        # Calculate averages
        return {cat: np.mean(ratings) for cat, ratings in categories.items()}
    
    def _identify_satisfaction_improvements(self, rated_queries: pd.DataFrame) -> List[str]:
        improvements = []
        
        low_rated = rated_queries[rated_queries['user_rating'] <= 2]
        if len(low_rated) > 0:
            avg_time = low_rated['total_time'].mean()
            if avg_time > 3.0:
                improvements.append("Reduce response time for better satisfaction")
        
        return improvements
    
    def _extract_failure_keywords(self, questions: List[str], responses: List[str]) -> List[str]:
        # Extract common words in failed queries
        all_text = ' '.join(questions + responses).lower()
        words = re.findall(r'\b\w+\b', all_text)
        common_words = [word for word, count in Counter(words).most_common(10) 
                       if word not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']]
        return common_words[:5]
    
    def _analyze_failure_responses(self, responses: List[str]) -> Dict:
        return {
            'avg_length': np.mean([len(r) for r in responses]),
            'common_phrases': self._extract_common_phrases(responses)
        }
    
    def _extract_common_phrases(self, responses: List[str]) -> List[str]:
        # Simple phrase extraction
        phrases = []
        for response in responses:
            if "I don't" in response or "I can't" in response:
                phrases.append("inability_phrases")
            if "error" in response.lower():
                phrases.append("error_responses")
        
        return list(set(phrases))
    
    def _generate_failure_prevention_strategies(self, failures: pd.DataFrame) -> List[str]:
        strategies = []
        
        if failures['context_length'].mean() < 500:
            strategies.append("Increase context retrieval for better answers")
        
        if failures['total_time'].mean() > 5.0:
            strategies.append("Optimize processing speed to reduce user frustration")
        
        return strategies

# Global ML analytics instance
ml_analytics = MLAnalytics()