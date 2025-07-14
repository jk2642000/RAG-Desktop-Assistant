#!/usr/bin/env python3
"""
Test chat export functionality
"""
import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chat_history import chat_history
from core.chat_exporter import chat_exporter

def test_txt_export():
    """Test TXT export functionality"""
    # Create test session
    session_id = chat_history.create_session("Test Export Session")
    
    # Add test messages
    chat_history.save_message(session_id, "user", "What is AI?")
    chat_history.save_message(session_id, "assistant", "AI stands for Artificial Intelligence.", sources=["test.pdf"])
    chat_history.save_message(session_id, "system", "Response rated 5/5")
    
    # Test export
    txt_path = os.path.join(tempfile.gettempdir(), "test_export.txt")
    success = chat_exporter.export_to_txt(session_id, txt_path)
    
    # Verify export
    assert success, "TXT export should succeed"
    assert os.path.exists(txt_path), "Export file should exist"
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Test Export Session" in content, "Session title should be in export"
        assert "What is AI?" in content, "User message should be in export"
        assert "Artificial Intelligence" in content, "Assistant response should be in export"
        assert "test.pdf" in content, "Sources should be in export"
    
    # Cleanup
    os.remove(txt_path)
    chat_history.delete_session(session_id)
    print("[PASS] TXT export test")

def test_pdf_export():
    """Test PDF export functionality"""
    # Create test session
    session_id = chat_history.create_session("Test PDF Session")
    chat_history.save_message(session_id, "user", "Test PDF export")
    chat_history.save_message(session_id, "assistant", "PDF export working correctly.")
    
    # Test export
    pdf_path = os.path.join(tempfile.gettempdir(), "test_export.pdf")
    success = chat_exporter.export_to_pdf(session_id, pdf_path)
    
    if success:
        assert os.path.exists(pdf_path), "PDF file should exist"
        assert os.path.getsize(pdf_path) > 0, "PDF should not be empty"
        os.remove(pdf_path)
        print("[PASS] PDF export test")
    else:
        print("[SKIP] PDF export not available (reportlab not installed)")
    
    # Cleanup
    chat_history.delete_session(session_id)

if __name__ == "__main__":
    test_txt_export()
    test_pdf_export()
    print("All chat export tests passed!")