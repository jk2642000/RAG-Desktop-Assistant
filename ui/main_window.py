from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QTextEdit, QLineEdit, QPushButton, 
                             QListWidget, QLabel, QProgressBar, QStatusBar,
                             QMenuBar, QAction, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QCloseEvent, QKeySequence, QResizeEvent
from .document_panel import DocumentPanel
from .chat_widget import ChatWidget
from core.config_manager import config_manager
from core.memory_manager import memory_manager
import sys
import gc

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAG Desktop Assistant")
        self.load_window_settings()
        self.setup_menu_bar()
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Document management
        self.document_panel = DocumentPanel()
        splitter.addWidget(self.document_panel)
        
        # Right panel - Chat interface
        self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        # Set splitter proportions from config
        left_width = config_manager.get('splitter.left_width', 300)
        right_width = config_manager.get('splitter.right_width', 900)
        splitter.setSizes([left_width, right_width])
        
        # Save splitter changes
        splitter.splitterMoved.connect(self.save_splitter_settings)
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect signals
        self.document_panel.documents_updated.connect(self.chat_widget.update_documents)
        self.chat_widget.status_update.connect(self.status_bar.showMessage)
    
    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        clear_action = QAction('Clear Documents', self)
        clear_action.setShortcut(QKeySequence.New)
        clear_action.triggered.connect(self.clear_all_documents)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        memory_action = QAction('Memory Usage', self)
        memory_action.triggered.connect(self.show_memory_info)
        tools_menu.addAction(memory_action)
        
        cleanup_action = QAction('Free Memory', self)
        cleanup_action.triggered.connect(self.force_memory_cleanup)
        tools_menu.addAction(cleanup_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_window_settings(self):
        """Load window geometry from config"""
        width = config_manager.get('window.width', 1200)
        height = config_manager.get('window.height', 800)
        x = config_manager.get('window.x', 100)
        y = config_manager.get('window.y', 100)
        self.setGeometry(x, y, width, height)
    
    def save_window_settings(self):
        """Save window geometry to config"""
        geometry = self.geometry()
        config_manager.set('window.width', geometry.width())
        config_manager.set('window.height', geometry.height())
        config_manager.set('window.x', geometry.x())
        config_manager.set('window.y', geometry.y())
        config_manager.save_config()
    
    def save_splitter_settings(self, pos, index):
        """Save splitter position"""
        splitter = self.sender()
        sizes = splitter.sizes()
        if len(sizes) >= 2:
            config_manager.set('splitter.left_width', sizes[0])
            config_manager.set('splitter.right_width', sizes[1])
    
    def clear_all_documents(self):
        """Clear all documents"""
        self.document_panel.clear_documents()
    
    def show_memory_info(self):
        """Show memory usage information"""
        memory_info = memory_manager.get_memory_usage()
        info_text = f"""Memory Usage:
        
RAM Usage: {memory_info['rss_mb']:.1f} MB
Virtual Memory: {memory_info['vms_mb']:.1f} MB
Memory Percentage: {memory_info['percent']:.1f}%
        
Loaded Models: {len(memory_manager.loaded_models)}"""
        
        QMessageBox.information(self, "Memory Information", info_text)
    
    def force_memory_cleanup(self):
        """Force memory cleanup"""
        memory_manager.force_cleanup()
        self.status_bar.showMessage("Memory cleanup completed", 3000)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """RAG Desktop Assistant
        
A portable document Q&A system powered by:
• Google Gemini AI
• ChromaDB Vector Store
• Advanced NLP Processing
        
Features:
• Document upload and processing
• Intelligent question answering
• Function calling capabilities
• Memory management
• Streaming responses"""
        
        QMessageBox.about(self, "About RAG Desktop Assistant", about_text)
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle window resize to save settings"""
        super().resizeEvent(event)
        # Debounce saving to avoid too frequent writes
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.save_window_settings)
        self._resize_timer.start(500)  # Save after 500ms of no resize
    
    def closeEvent(self, event: QCloseEvent):
        """Handle application close with proper cleanup"""
        self.status_bar.showMessage("Closing application...")
        
        # Stop all threads
        self.chat_widget.cleanup_all_threads()
        self.document_panel.cleanup_thread()
        
        # Force garbage collection
        gc.collect()
        
        # Accept close event
        event.accept()
        
        # Save settings before exit
        self.save_window_settings()
        
        # Force exit to prevent assertion errors
        QTimer.singleShot(100, lambda: sys.exit(0))