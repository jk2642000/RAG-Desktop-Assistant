import sys
import os
import signal
import atexit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

# Initialize NLTK data if needed
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
except (ImportError, LookupError):
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
    except:
        pass  # Continue without NLTK if download fails

def signal_handler(signum, frame):
    """Handle system signals gracefully"""
    QApplication.quit()

def cleanup_on_exit():
    """Final cleanup on exit"""
    import gc
    gc.collect()

def main():
    # Register cleanup handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_on_exit)
    
    # Ensure NLTK data is available
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("[INFO] Downloading required NLTK data...")
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
        except Exception as e:
            print(f"[WARNING] Could not download NLTK data: {e}")
    
    # Set high DPI scaling before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    window = MainWindow()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass

if __name__ == "__main__":
    main()