#!/usr/bin/env python3
"""
Advanced Analytics Dashboard with ML Insights
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTextEdit, QLabel, 
                             QPushButton, QScrollArea, QFrame, QGridLayout,
                             QProgressBar, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import pandas as pd
import numpy as np
from core.ml_analytics import ml_analytics
from core.analytics import analytics_engine
import json

class AnalyticsWorker(QThread):
    """Background worker for ML analytics computation"""
    insights_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, days=30):
        super().__init__()
        self.days = days
    
    def run(self):
        try:
            insights = ml_analytics.get_query_insights(self.days)
            self.insights_ready.emit(insights)
        except Exception as e:
            self.error_occurred.emit(str(e))

class InsightCard(QFrame):
    """Card widget for displaying insights"""
    
    def __init__(self, title: str, content: str, color: str = "#f8f9fa"):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #495057; margin-bottom: 5px;")
        layout.addWidget(self.title_label)
        
        # Content
        self.content_label = QLabel(content)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #6c757d; line-height: 1.4;")
        layout.addWidget(self.content_label)
    
    def update_content(self, content: str):
        """Update the content of the card"""
        self.content_label.setText(content)

class ChartWidget(QWidget):
    """Widget for displaying matplotlib charts"""
    
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
    
    def plot_performance_trends(self, insights: dict):
        """Plot performance trends"""
        self.figure.clear()
        
        # Get performance data
        perf_data = analytics_engine.get_performance_insights(30)
        
        if 'performance' in perf_data:
            ax = self.figure.add_subplot(2, 2, 1)
            metrics = ['avg_response_time', 'avg_rating', 'success_rate']
            values = [perf_data['performance'].get(m, 0) for m in metrics]
            
            ax.bar(metrics, values, color=['#ff6b6b', '#4ecdc4', '#45b7d1'])
            ax.set_title('Performance Overview')
            ax.tick_params(axis='x', rotation=45)
        
        # Question patterns
        if 'question_patterns' in insights and 'clusters' in insights['question_patterns']:
            ax = self.figure.add_subplot(2, 2, 2)
            clusters = insights['question_patterns']['clusters']
            
            cluster_names = list(clusters.keys())
            cluster_sizes = [clusters[c]['size'] for c in cluster_names]
            
            ax.pie(cluster_sizes, labels=cluster_names, autopct='%1.1f%%')
            ax.set_title('Question Categories')
        
        # Response quality
        if 'response_quality' in insights:
            ax = self.figure.add_subplot(2, 2, 3)
            quality = insights['response_quality']
            
            if 'sentiment_stats' in quality:
                sentiment_data = quality['sentiment_stats']
                labels = ['Positive', 'Neutral', 'Negative']
                pos_ratio = sentiment_data.get('positive_ratio', 0)
                values = [pos_ratio, 1 - pos_ratio - 0.1, 0.1]  # Simplified
                
                ax.bar(labels, values, color=['#28a745', '#ffc107', '#dc3545'])
                ax.set_title('Response Sentiment')
        
        # Performance bottlenecks
        if 'performance_bottlenecks' in insights:
            ax = self.figure.add_subplot(2, 2, 4)
            bottlenecks = insights['performance_bottlenecks'].get('bottlenecks', [])
            
            if bottlenecks:
                types = [b['type'] for b in bottlenecks]
                counts = [b['count'] for b in bottlenecks]
                
                ax.bar(types, counts, color='#ff6b6b')
                ax.set_title('Performance Bottlenecks')
                ax.tick_params(axis='x', rotation=45)
        
        self.figure.tight_layout()
        self.canvas.draw()

class AnalyticsDashboard(QMainWindow):
    """Main analytics dashboard window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAG Analytics Dashboard - ML Insights")
        self.setGeometry(100, 100, 1400, 900)
        self.insights_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🧠 RAG System Analytics - ML Powered Insights")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 20px; background: #ecf0f1; border-radius: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.days_combo = QComboBox()
        self.days_combo.addItems(["7 days", "30 days", "90 days"])
        self.days_combo.setCurrentText("30 days")
        controls_layout.addWidget(QLabel("Analysis Period:"))
        controls_layout.addWidget(self.days_combo)
        
        self.refresh_btn = QPushButton("🔄 Refresh Analysis")
        self.refresh_btn.clicked.connect(self.refresh_analytics)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("📊 Export Report")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        controls_layout.addWidget(self.export_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_overview_tab()
        self.create_insights_tab()
        self.create_recommendations_tab()
        self.create_charts_tab()
        
        # Load basic metrics immediately on startup
        QTimer.singleShot(100, self.load_basic_metrics)
        # Auto-refresh full analytics after basic metrics
        QTimer.singleShot(1500, self.refresh_analytics)
    
    def load_basic_metrics(self):
        """Load basic metrics immediately without ML processing"""
        print("[DEBUG] load_basic_metrics called")
        try:
            self.update_overview_metrics()
        except Exception as e:
            print(f"[ERROR] Error loading basic metrics: {e}")
            import traceback
            traceback.print_exc()
    
    def create_overview_tab(self):
        """Create overview tab with key metrics"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Key metrics grid
        self.metrics_grid = QGridLayout()
        
        # Create metric cards that will be updated
        self.total_queries_card = InsightCard("Total Queries", "Loading...", "#e3f2fd")
        self.avg_rating_card = InsightCard("Average Rating", "Loading...", "#f3e5f5")
        self.avg_response_time_card = InsightCard("Avg Response Time", "Loading...", "#fff3e0")
        self.success_rate_card = InsightCard("Success Rate", "Loading...", "#e8f5e8")
        
        self.metrics_grid.addWidget(self.total_queries_card, 0, 0)
        self.metrics_grid.addWidget(self.avg_rating_card, 0, 1)
        self.metrics_grid.addWidget(self.avg_response_time_card, 1, 0)
        self.metrics_grid.addWidget(self.success_rate_card, 1, 1)
        
        layout.addLayout(self.metrics_grid)
        
        # Recent activity
        self.activity_text = QTextEdit()
        self.activity_text.setMaximumHeight(200)
        self.activity_text.setPlainText("Loading recent activity...")
        layout.addWidget(QLabel("Recent Activity:"))
        layout.addWidget(self.activity_text)
        
        self.tab_widget.addTab(tab, "📊 Overview")
    
    def create_insights_tab(self):
        """Create ML insights tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.insights_layout = QVBoxLayout(scroll_widget)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(tab, "🧠 ML Insights")
    
    def create_recommendations_tab(self):
        """Create recommendations tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setPlainText("Loading ML-powered recommendations...")
        layout.addWidget(self.recommendations_text)
        
        self.tab_widget.addTab(tab, "💡 Recommendations")
    
    def create_charts_tab(self):
        """Create charts tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.chart_widget = ChartWidget()
        layout.addWidget(self.chart_widget)
        
        self.tab_widget.addTab(tab, "📈 Charts")
    
    def update_overview_metrics(self):
        """Update overview tab with basic performance metrics"""
        print("[DEBUG] update_overview_metrics called")
        try:
            # Get performance data directly from analytics engine
            perf_data = analytics_engine.get_performance_insights(30)
            print(f"[DEBUG] Got performance data: {perf_data.get('performance', {}).get('total_queries', 'NO DATA')} queries")
            
            if 'performance' in perf_data:
                perf = perf_data['performance']
                
                # Update metric cards
                print(f"[DEBUG] Updating total queries card with: {int(perf.get('total_queries', 0))}")
                self.total_queries_card.update_content(
                    f"{int(perf.get('total_queries', 0))} queries in last 30 days"
                )
                
                avg_rating = perf.get('avg_rating', 0)
                rating_text = f"{avg_rating:.1f}/5.0" if avg_rating else "No ratings yet"
                stars = '*' * int(avg_rating) if avg_rating else ''
                self.avg_rating_card.update_content(f"{rating_text}\n{stars}")
                
                avg_time = perf.get('avg_response_time', 0)
                self.avg_response_time_card.update_content(f"{avg_time:.2f} seconds")
                
                success_rate = perf.get('success_rate', 0)
                self.success_rate_card.update_content(f"{success_rate*100:.1f}%")
                
                # Update activity text
                activity_text = f"""Performance Summary (Last 30 days):

- Total Queries: {int(perf.get('total_queries', 0))}
- Average Response Time: {perf.get('avg_response_time', 0):.2f}s
- Average Search Time: {perf.get('avg_search_time', 0):.2f}s
- Average Generation Time: {perf.get('avg_generation_time', 0):.2f}s
- Average Context Length: {int(perf.get('avg_context_length', 0))} chars
- Success Rate: {perf.get('success_rate', 0)*100:.1f}%
- Average Rating: {perf.get('avg_rating', 0):.1f}/5.0

Document Usage:"""
                
                if 'document_stats' in perf_data:
                    for doc_stat in perf_data['document_stats'][:5]:
                        filename, usage_count, chunk_count, avg_chunk_size = doc_stat
                        activity_text += f"\n- {filename}: {usage_count} uses, {chunk_count} chunks"
                
                if 'failing_queries' in perf_data and perf_data['failing_queries']:
                    activity_text += "\n\n[!] Low-rated queries:"
                    for query_data in perf_data['failing_queries'][:3]:
                        question, rating, count = query_data
                        activity_text += f"\n- '{question}' - {rating}/5 ({count} times)"
                
                self.activity_text.setPlainText(activity_text)
            
        except Exception as e:
            error_msg = f"Error loading metrics: {str(e)}"
            self.activity_text.setPlainText(error_msg)
            print(f"[ERROR] update_overview_metrics: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_analytics(self):
        """Refresh analytics data"""
        days_text = self.days_combo.currentText()
        days = int(days_text.split()[0])
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.refresh_btn.setEnabled(False)
        
        # Start background worker
        self.worker = AnalyticsWorker(days)
        self.worker.insights_ready.connect(self.on_insights_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_insights_ready(self, insights):
        """Handle insights data"""
        self.insights_data = insights
        self.update_overview_metrics()  # Update overview first
        self.update_ui_with_insights(insights)
        
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
    
    def on_error(self, error_msg):
        """Handle errors"""
        QMessageBox.warning(self, "Analysis Error", f"Failed to generate insights: {error_msg}")
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
    
    def update_ui_with_insights(self, insights):
        """Update UI with ML insights"""
        # Clear previous insights
        for i in reversed(range(self.insights_layout.count())):
            self.insights_layout.itemAt(i).widget().setParent(None)
        
        # Add new insights
        if 'error' in insights:
            self.insights_layout.addWidget(
                InsightCard("Error", insights['error'], "#ffebee")
            )
            return
        
        # Question patterns
        if 'question_patterns' in insights:
            patterns = insights['question_patterns']
            if 'clusters' in patterns:
                content = f"Found {len(patterns['clusters'])} question categories:\n"
                for cluster_id, data in patterns['clusters'].items():
                    content += f"• {cluster_id}: {data['size']} questions, keywords: {', '.join(data['keywords'][:3])}\n"
                
                self.insights_layout.addWidget(
                    InsightCard("🔍 Question Pattern Analysis", content, "#e3f2fd")
                )
        
        # Response quality
        if 'response_quality' in insights:
            quality = insights['response_quality']
            content = "Response Quality Analysis:\n"
            
            if 'sentiment_stats' in quality:
                sentiment = quality['sentiment_stats']
                content += f"• Average sentiment: {sentiment.get('avg_sentiment', 0):.2f}\n"
                content += f"• Positive responses: {sentiment.get('positive_ratio', 0)*100:.1f}%\n"
            
            if 'improvement_suggestions' in quality:
                content += f"• Suggestions: {', '.join(quality['improvement_suggestions'])}\n"
            
            self.insights_layout.addWidget(
                InsightCard("📝 Response Quality Insights", content, "#f3e5f5")
            )
        
        # Performance bottlenecks
        if 'performance_bottlenecks' in insights:
            bottlenecks = insights['performance_bottlenecks']
            content = "Performance Analysis:\n"
            
            if 'bottlenecks' in bottlenecks:
                for bottleneck in bottlenecks['bottlenecks']:
                    content += f"• {bottleneck['type']}: {bottleneck['count']} instances\n"
            
            if 'optimization_recommendations' in bottlenecks:
                content += f"\nOptimizations:\n"
                for rec in bottlenecks['optimization_recommendations']:
                    content += f"• {rec}\n"
            
            self.insights_layout.addWidget(
                InsightCard("⚡ Performance Bottlenecks", content, "#fff3e0")
            )
        
        # Satisfaction patterns
        if 'satisfaction_patterns' in insights:
            satisfaction = insights['satisfaction_patterns']
            content = f"User Satisfaction Analysis:\n"
            content += f"• Overall satisfaction: {satisfaction.get('overall_satisfaction', 0):.1f}/5\n"
            
            if 'satisfaction_by_type' in satisfaction:
                content += "• By question type:\n"
                for qtype, rating in satisfaction['satisfaction_by_type'].items():
                    content += f"  - {qtype}: {rating:.1f}/5\n"
            
            self.insights_layout.addWidget(
                InsightCard("😊 User Satisfaction Patterns", content, "#e8f5e8")
            )
        
        # Update recommendations
        self.update_recommendations(insights)
        
        # Update charts
        self.chart_widget.plot_performance_trends(insights)
    
    def update_recommendations(self, insights):
        """Update recommendations text"""
        recommendations = []
        
        # Collect all recommendations
        for category, data in insights.items():
            if isinstance(data, dict):
                if 'recommendations' in data:
                    recommendations.extend(data['recommendations'])
                if 'improvement_suggestions' in data:
                    recommendations.extend(data['improvement_suggestions'])
                if 'optimization_recommendations' in data:
                    recommendations.extend(data['optimization_recommendations'])
        
        if recommendations:
            rec_text = "🤖 ML-Powered Recommendations:\n\n"
            for i, rec in enumerate(recommendations, 1):
                rec_text += f"{i}. {rec}\n\n"
        else:
            rec_text = "No specific recommendations at this time. System is performing well!"
        
        self.recommendations_text.setPlainText(rec_text)
    
    def export_report(self):
        """Export analytics report"""
        if not self.insights_data:
            QMessageBox.information(self, "Export", "No data to export. Please refresh analytics first.")
            return
        
        try:
            # Export to JSON
            filename = f"rag_analytics_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.insights_data, f, indent=2, default=str)
            
            QMessageBox.information(self, "Export Complete", f"Report exported to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export report: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    dashboard = AnalyticsDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()