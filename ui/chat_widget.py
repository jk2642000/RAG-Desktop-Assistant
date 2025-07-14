from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QScrollArea, QLabel,
                             QMenuBar, QMenu, QAction, QFileDialog, QMessageBox,
                             QListWidget, QListWidgetItem, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QKeySequence
from core.analytics import analytics_engine
from core.chat_history import chat_history
from core.chat_exporter import chat_exporter
import datetime
import os

class ChatThread(QThread):
    response_ready = pyqtSignal(str, list)
    response_chunk = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, question, documents, stream_callback=None):
        super().__init__()
        self.question = question
        self.documents = documents
        self._stop_requested = False
        self.query_id = None
        self.stream_callback = stream_callback
        
    def run(self):
        try:
            if self._stop_requested:
                return
                
            from core.rag_engine import RAGEngine
            rag = RAGEngine()
            
            if self._stop_requested:
                return
            
            if not self.documents:
                response = "Please upload some documents first to ask questions about them."
                sources = []
                query_id = None
            else:
                # Add stream callback to documents if available
                if self.stream_callback:
                    docs_with_stream = [dict(doc, stream_callback=self.stream_callback) for doc in self.documents]
                    response, sources, query_id = rag.query(self.question, docs_with_stream)
                else:
                    response, sources, query_id = rag.query(self.question, self.documents)
            
            if not self._stop_requested:
                self.response_ready.emit(response, sources)
                # Store query_id in parent widget
                if query_id and hasattr(self, 'parent_widget'):
                    self.parent_widget.last_query_id = query_id
                
        except Exception as e:
            if not self._stop_requested:
                self.error_occurred.emit(str(e))
    
    def stop(self):
        self._stop_requested = True
        self.quit()
        self.wait(1000)  # Wait max 1 second

class ChatWidget(QWidget):
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.documents = []
        self.active_threads = []
        self.last_query_id = None
        self.current_session_id = None
        self.setup_ui()
        self.start_new_session()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("Chat with Documents")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Chat controls
        self.new_chat_btn = QPushButton("New Chat")
        self.new_chat_btn.clicked.connect(self.start_new_session)
        self.new_chat_btn.setToolTip("Start a new chat session (Ctrl+N)")
        header_layout.addWidget(self.new_chat_btn)
        
        self.history_btn = QPushButton("History")
        self.history_btn.clicked.connect(self.show_chat_history)
        header_layout.addWidget(self.history_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_current_chat)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Rating buttons (initially hidden)
        self.rating_widget = QWidget()
        rating_layout = QHBoxLayout(self.rating_widget)
        rating_layout.addWidget(QLabel("Rate this response:"))
        
        self.rating_buttons = []
        ratings = [("👍 Excellent", 5), ("👌 Good", 4), ("😐 OK", 3), ("👎 Poor", 2), ("❌ Bad", 1)]
        
        for text, rating in ratings:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, r=rating: self.rate_response(r))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 5px 10px;
                    margin: 2px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)
            rating_layout.addWidget(btn)
            self.rating_buttons.append(btn)
        
        self.rating_widget.setVisible(False)
        layout.addWidget(self.rating_widget)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question about your documents...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Welcome message
        self.add_system_message("Welcome! Upload documents using the panel on the left, then ask questions about them.")
    
    def start_new_session(self):
        """Start a new chat session"""
        self.current_session_id = chat_history.create_session()
        self.chat_display.clear()
        self.add_system_message("New chat session started. Upload documents and ask questions!")
        self.rating_widget.setVisible(False)
    
    def show_chat_history(self):
        """Show chat history dialog"""
        dialog = ChatHistoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_session = dialog.get_selected_session()
            if selected_session:
                self.load_session(selected_session)
    
    def load_session(self, session_id: str):
        """Load a chat session"""
        self.current_session_id = session_id
        self.chat_display.clear()
        
        messages = chat_history.get_session_messages(session_id)
        for msg in messages:
            timestamp = datetime.datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
            
            if msg['type'] == 'user':
                self.chat_display.append(f"<div style='margin: 10px 0;'><b style='color: #007acc;'>[{timestamp}] You:</b><br>{msg['content']}</div>")
            elif msg['type'] == 'assistant':
                html = f"<div style='margin: 10px 0;'><b style='color: #28a745;'>[{timestamp}] Assistant:</b><br>{msg['content']}"
                if msg['sources']:
                    html += "<br><br><i>Sources:</i><ul>"
                    for source in msg['sources'][:3]:
                        html += f"<li>{source}</li>"
                    html += "</ul>"
                html += "</div>"
                self.chat_display.append(html)
            elif msg['type'] == 'system':
                self.chat_display.append(f"<div style='margin: 10px 0; color: #666; font-style: italic;'>[{timestamp}] {msg['content']}</div>")
        
        self.scroll_to_bottom()
    
    def export_current_chat(self):
        """Export current chat session"""
        if not self.current_session_id:
            QMessageBox.information(self, "Export Chat", "No active chat session to export.")
            return
        
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "Export Chat", f"chat_export_{self.current_session_id}.txt",
            "Text Files (*.txt);;PDF Files (*.pdf)"
        )
        
        if file_path:
            format_type = 'pdf' if file_path.lower().endswith('.pdf') else 'txt'
            success = chat_exporter.export_session(self.current_session_id, file_path, format_type)
            
            if success:
                QMessageBox.information(self, "Export Complete", f"Chat exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export chat. Please try again.")
        
    def send_message(self):
        question = self.input_field.text().strip()
        if not question:
            return
            
        # Add user message to chat
        self.add_user_message(question)
        self.input_field.clear()
        
        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.status_update.emit("Processing your question...")
        
        # Start chat thread with streaming
        self.current_response = ""
        self.chat_thread = ChatThread(question, self.documents, self.on_stream_chunk)
        self.chat_thread.parent_widget = self  # Set parent reference
        self.chat_thread.response_ready.connect(self.on_response_ready)
        self.chat_thread.response_chunk.connect(self.on_stream_chunk)
        self.chat_thread.error_occurred.connect(self.on_error)
        self.chat_thread.finished.connect(lambda: self.cleanup_thread(self.chat_thread))
        self.active_threads.append(self.chat_thread)
        
        # Add streaming placeholder
        self.add_assistant_message_start()
        self.chat_thread.start()
    
    def on_response_ready(self, response, sources):
        self.add_assistant_message(response, sources)
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_update.emit("Ready")
        
        # Show rating buttons if we have a query to rate
        if hasattr(self, 'last_query_id') and self.last_query_id:
            self.rating_widget.setVisible(True)
        
    def on_error(self, error_msg):
        self.add_system_message(f"Error: {error_msg}")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_update.emit("Error occurred")
    
    def add_user_message(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.chat_display.append(f"<div style='margin: 10px 0;'><b style='color: #007acc;'>[{timestamp}] You:</b><br>{message}</div>")
        self.scroll_to_bottom()
        
        # Save to chat history
        if self.current_session_id:
            chat_history.save_message(self.current_session_id, "user", message)
        
    def add_assistant_message_start(self):
        """Start streaming assistant message"""
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.streaming_html = f"<div style='margin: 10px 0;'><b style='color: #28a745;'>[{timestamp}] Assistant:</b><br>"
        self.chat_display.append(self.streaming_html)
        self.scroll_to_bottom()
    
    def on_stream_chunk(self, chunk):
        """Handle streaming response chunks"""
        self.current_response += chunk
        # Update the last message with accumulated response
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfBlock)
        cursor.movePosition(cursor.End, cursor.KeepAnchor)
        cursor.removeSelectedText()
        
        updated_html = self.streaming_html + self.current_response + "</div>"
        cursor.insertHtml(updated_html)
        self.scroll_to_bottom()
    
    def add_assistant_message(self, message, sources=None):
        if hasattr(self, 'current_response'):
            # Streaming mode - finalize message
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.End)
            cursor.movePosition(cursor.StartOfBlock)
            cursor.movePosition(cursor.End, cursor.KeepAnchor)
            cursor.removeSelectedText()
            
            html = self.streaming_html + message
            if sources:
                html += "<br><br><i>Sources:</i><ul>"
                for source in sources[:3]:
                    html += f"<li>{source}</li>"
                html += "</ul>"
            html += "</div>"
            cursor.insertHtml(html)
            self.current_response = ""
        else:
            # Non-streaming mode
            timestamp = datetime.datetime.now().strftime("%H:%M")
            html = f"<div style='margin: 10px 0;'><b style='color: #28a745;'>[{timestamp}] Assistant:</b><br>{message}"
            
            if sources:
                html += "<br><br><i>Sources:</i><ul>"
                for source in sources[:3]:
                    html += f"<li>{source}</li>"
                html += "</ul>"
            
            html += "</div>"
            self.chat_display.append(html)
        
        self.scroll_to_bottom()
        
        # Save to chat history
        if self.current_session_id:
            chat_history.save_message(self.current_session_id, "assistant", message, sources)
    
    def rate_response(self, rating: int):
        """Handle user feedback rating"""
        if hasattr(self, 'last_query_id') and self.last_query_id:
            try:
                analytics_engine.update_user_feedback(self.last_query_id, rating)
                self.add_system_message(f"Thank you for your feedback! (Rating: {rating}/5)")
                self.rating_widget.setVisible(False)  # Hide buttons after rating
                self.last_query_id = None  # Clear query ID
            except Exception as e:
                self.add_system_message(f"Error saving feedback: {e}")
        else:
            self.add_system_message("No recent response to rate.")
        
    def add_system_message(self, message):
        self.chat_display.append(f"<div style='margin: 10px 0; color: #666; font-style: italic;'>{message}</div>")
        self.scroll_to_bottom()
        
        # Save to chat history
        if self.current_session_id:
            chat_history.save_message(self.current_session_id, "system", message)
        
    def scroll_to_bottom(self):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        
    def update_documents(self, documents):
        self.documents = documents
        doc_count = len(documents)
        if doc_count > 0:
            self.add_system_message(f"Updated document library: {doc_count} documents loaded.")
        else:
            self.add_system_message("Document library cleared.")
    
    def cleanup_thread(self, thread):
        """Remove finished thread from active list"""
        if thread in self.active_threads:
            self.active_threads.remove(thread)
    
    def cleanup_all_threads(self):
        """Stop all active threads"""
        for thread in self.active_threads[:]:
            if thread.isRunning():
                thread.stop()
        self.active_threads.clear()

class ChatHistoryDialog(QDialog):
    """Dialog for browsing chat history"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chat History")
        self.setGeometry(200, 200, 500, 400)
        self.selected_session = None
        self.setup_ui()
        self.load_sessions()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Session list
        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self.on_session_selected)
        layout.addWidget(QLabel("Select a chat session:"))
        layout.addWidget(self.session_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected_session)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def load_sessions(self):
        """Load chat sessions into list"""
        sessions = chat_history.get_sessions()
        self.session_list.clear()
        
        for session in sessions:
            created = datetime.datetime.fromisoformat(session['created_at']).strftime('%Y-%m-%d %H:%M')
            item_text = f"{session['title']} ({created})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, session['session_id'])
            self.session_list.addItem(item)
    
    def on_session_selected(self, item):
        """Handle session selection"""
        self.selected_session = item.data(Qt.UserRole)
        self.accept()
    
    def delete_selected_session(self):
        """Delete selected session"""
        current_item = self.session_list.currentItem()
        if not current_item:
            return
        
        session_id = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete Session", 
                                   "Are you sure you want to delete this chat session?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            chat_history.delete_session(session_id)
            self.load_sessions()
    
    def get_selected_session(self):
        """Get selected session ID"""
        current_item = self.session_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return self.selected_session