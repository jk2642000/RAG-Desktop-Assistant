import sys
import os
import signal
import atexit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

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