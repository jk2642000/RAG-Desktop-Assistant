from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QProgressBar, QFileDialog,
                             QListWidgetItem, QMessageBox, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon
import os
import hashlib
from core.logger import rag_logger

class DocumentProcessingThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished_processing = pyqtSignal(list)
    file_status_update = pyqtSignal(str, str)  # filename, status
    error_occurred = pyqtSignal(str, str)  # filename, error
    
    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths
        self._stop_requested = False
        
    def run(self):
        from core.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        processed_docs = []
        total_files = len(self.file_paths)
        
        for i, file_path in enumerate(self.file_paths):
            if self._stop_requested:
                break
                
            filename = os.path.basename(file_path)
            self.status_update.emit(f"Processing {filename}...")
            self.file_status_update.emit(filename, "processing")
            
            try:
                doc_data = processor.process_document(file_path)
                processed_docs.append(doc_data)
                self.file_status_update.emit(filename, "processed")
                progress = int((i + 1) / total_files * 100)
                self.progress_update.emit(progress)
            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                self.status_update.emit(error_msg)
                self.file_status_update.emit(filename, "error")
                self.error_occurred.emit(filename, str(e))
        
        if not self._stop_requested:
            self.finished_processing.emit(processed_docs)
    
    def stop(self):
        self._stop_requested = True
        self.quit()
        self.wait(1000)

class DocumentPanel(QWidget):
    documents_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.documents = []
        self.processing_thread = None
        self.failed_files = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Document Library")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Upload button
        self.upload_btn = QPushButton("Upload Documents")
        self.upload_btn.clicked.connect(self.upload_documents)
        layout.addWidget(self.upload_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Document list with context menu
        self.document_list = QListWidget()
        self.document_list.setAcceptDrops(True)
        self.document_list.dragEnterEvent = self.drag_enter_event
        self.document_list.dropEvent = self.drop_event
        self.document_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.document_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.document_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        self.reindex_btn = QPushButton("Re-index Selected")
        self.reindex_btn.clicked.connect(self.reindex_selected)
        self.reindex_btn.setEnabled(False)
        button_layout.addWidget(self.reindex_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_documents)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # Connect selection change
        self.document_list.itemSelectionChanged.connect(self.on_selection_changed)
        
    def upload_documents(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", 
            "Documents (*.pdf *.txt *.docx *.xlsx *.xls *.csv *.pptx);;PDF Files (*.pdf);;Text Files (*.txt);;Word Documents (*.docx);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;PowerPoint Files (*.pptx);;All Files (*)"
        )
        
        if file_paths:
            self.process_documents(file_paths)
    
    def process_documents(self, file_paths):
        self.upload_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            
        self.processing_thread = DocumentProcessingThread(file_paths)
        self.processing_thread.progress_update.connect(self.progress_bar.setValue)
        self.processing_thread.finished_processing.connect(self.on_processing_finished)
        self.processing_thread.file_status_update.connect(self.update_file_status)
        self.processing_thread.error_occurred.connect(self.handle_processing_error)
        self.processing_thread.start()
    
    def on_processing_finished(self, processed_docs):
        self.documents.extend(processed_docs)
        
        # Update UI
        for doc in processed_docs:
            item = QListWidgetItem(f"✓ {doc['filename']}")
            item.setData(Qt.UserRole, doc)  # Store document data
            self.document_list.addItem(item)
        
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(True)
        
        # Emit signal to update chat widget
        self.documents_updated.emit(self.documents)
        
    def clear_documents(self):
        from core.rag_engine import RAGEngine
        
        # Clear from UI
        self.documents.clear()
        self.document_list.clear()
        
        # Clear from vector store
        try:
            rag = RAGEngine()
            rag.clear_documents()
        except Exception as e:
            print(f"Error clearing vector store: {e}")
        
        self.documents_updated.emit(self.documents)
    
    def drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def drop_event(self, event: QDropEvent):
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.pdf', '.txt', '.docx', '.xlsx', '.xls', '.csv', '.pptx')):
                file_paths.append(file_path)
        
        if file_paths:
            self.process_documents(file_paths)
    
    def show_context_menu(self, position):
        """Show context menu for document list"""
        item = self.document_list.itemAt(position)
        if item:
            menu = QMenu()
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_selected)
            menu.addAction(delete_action)
            
            reindex_action = QAction("Re-index", self)
            reindex_action.triggered.connect(self.reindex_selected)
            menu.addAction(reindex_action)
            
            menu.exec_(self.document_list.mapToGlobal(position))
    
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = bool(self.document_list.selectedItems())
        self.delete_btn.setEnabled(has_selection)
        self.reindex_btn.setEnabled(has_selection)
    
    def delete_selected(self):
        """Delete selected documents"""
        selected_items = self.document_list.selectedItems()
        if not selected_items:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Delete Documents", 
                                   f"Delete {len(selected_items)} selected document(s)?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            from core.rag_engine import RAGEngine
            
            for item in selected_items:
                doc_data = item.data(Qt.UserRole)
                if doc_data:
                    # Remove from vector store
                    try:
                        rag = RAGEngine()
                        rag.vector_store.remove_document(doc_data['file_hash'])
                    except Exception as e:
                        rag_logger.error(f"Error removing document from vector store: {e}")
                    
                    # Remove from documents list
                    self.documents = [d for d in self.documents if d['file_hash'] != doc_data['file_hash']]
                
                # Remove from UI
                row = self.document_list.row(item)
                self.document_list.takeItem(row)
            
            self.documents_updated.emit(self.documents)
    
    def reindex_selected(self):
        """Re-index selected documents"""
        selected_items = self.document_list.selectedItems()
        if not selected_items:
            return
        
        file_paths = []
        for item in selected_items:
            doc_data = item.data(Qt.UserRole)
            if doc_data and os.path.exists(doc_data['filepath']):
                # Check if file has changed
                current_hash = self._get_file_hash(doc_data['filepath'])
                if current_hash != doc_data['file_hash']:
                    file_paths.append(doc_data['filepath'])
                    # Update status
                    item.setText(f"🔄 {doc_data['filename']}")
        
        if file_paths:
            self.process_documents(file_paths)
        else:
            QMessageBox.information(self, "Re-index", "No files need re-indexing.")
    
    def update_file_status(self, filename: str, status: str):
        """Update file status in the list"""
        for i in range(self.document_list.count()):
            item = self.document_list.item(i)
            if filename in item.text():
                if status == "processing":
                    item.setText(f"🔄 {filename}")
                elif status == "processed":
                    item.setText(f"✓ {filename}")
                elif status == "error":
                    item.setText(f"❌ {filename}")
                break
    
    def handle_processing_error(self, filename: str, error: str):
        """Handle processing errors with prominent display"""
        self.failed_files.append((filename, error))
        
        # Show error dialog for critical errors
        if "permission" in error.lower() or "not found" in error.lower():
            QMessageBox.critical(self, "Processing Error", 
                               f"Failed to process {filename}:\n{error}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file to detect changes"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def cleanup_thread(self):
        """Clean up processing thread"""
        if hasattr(self, 'processing_thread') and self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()