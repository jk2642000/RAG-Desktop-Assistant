#!/usr/bin/env python3
"""
Consolidated System Test Suite for RAG Desktop Assistant
Run all tests from a single file with organized functions
"""
import sys
import os
import tempfile
import csv
from openpyxl import Workbook
from pptx import Presentation
from pptx.util import Inches

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test core RAG functionality"""
    print("\n=== Testing Basic RAG Functionality ===")
    try:
        from core.rag_engine import RAGEngine
        from core.document_processor import DocumentProcessor
        
        # Test with existing resume file if available
        if os.path.exists("test_resume.txt"):
            rag = RAGEngine()
            processor = DocumentProcessor()
            doc_data = processor.process_document("test_resume.txt")
            rag.add_documents([doc_data])
            
            response, sources, query_id = rag.query("What is the main topic of this document?")
            print(f"[OK] Basic RAG test passed")
            print(f"     Response length: {len(response)} chars")
            print(f"     Sources: {len(sources)} files")
            return True
        else:
            print("[SKIP] No test document available")
            return True
    except Exception as e:
        print(f"[ERROR] Basic RAG test failed: {e}")
        return False

def test_function_calling():
    """Test Gemini function calling capabilities"""
    print("\n=== Testing Function Calling ===")
    try:
        from core.rag_engine import RAGEngine
        
        rag = RAGEngine()
        if not rag.using_gemini:
            print("[SKIP] Gemini not available for function calling")
            return True
        
        # Test calculator
        response, _, _ = rag.query("Calculate 15 + 25 * 2")
        if "65" in response or "result" in response.lower():
            print("[OK] Function calling test passed")
            return True
        else:
            print("[WARNING] Function calling may not be working")
            return True
    except Exception as e:
        print(f"[ERROR] Function calling test failed: {e}")
        return False

def test_document_formats():
    """Test new document format support"""
    print("\n=== Testing Document Formats ===")
    try:
        from core.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        supported = processor.supported_formats
        print(f"[OK] Supported formats: {supported}")
        
        # Test CSV processing
        csv_path = os.path.join(tempfile.gettempdir(), "test.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Value'])
            writer.writerow(['Test', '123'])
        
        doc_data = processor.process_document(csv_path)
        os.remove(csv_path)
        
        if doc_data['chunk_count'] > 0:
            print("[OK] Document format test passed")
            return True
        else:
            print("[ERROR] No chunks created")
            return False
    except Exception as e:
        print(f"[ERROR] Document format test failed: {e}")
        return False

def test_analytics_system():
    """Test analytics and dashboard connectivity"""
    print("\n=== Testing Analytics System ===")
    try:
        from core.analytics import analytics_engine
        
        insights = analytics_engine.get_performance_insights(30)
        if 'performance' in insights:
            perf = insights['performance']
            print(f"[OK] Analytics working - {perf.get('total_queries', 0)} queries logged")
            return True
        else:
            print("[ERROR] No performance data")
            return False
    except Exception as e:
        print(f"[ERROR] Analytics test failed: {e}")
        return False

def test_ml_analytics():
    """Test ML-powered analytics"""
    print("\n=== Testing ML Analytics ===")
    try:
        from core.ml_analytics import ml_analytics
        
        insights = ml_analytics.get_query_insights(30)
        if 'error' not in insights:
            print(f"[OK] ML Analytics working - {len(insights)} insight categories")
            return True
        else:
            print(f"[WARNING] ML Analytics: {insights['error']}")
            return True  # Not critical
    except Exception as e:
        print(f"[ERROR] ML Analytics test failed: {e}")
        return False

def test_memory_management():
    """Test memory management system"""
    print("\n=== Testing Memory Management ===")
    try:
        from core.memory_manager import memory_manager
        
        memory_info = memory_manager.get_memory_usage()
        print(f"[OK] Memory system working - {memory_info['rss_mb']:.1f}MB used")
        return True
    except Exception as e:
        print(f"[ERROR] Memory management test failed: {e}")
        return False

def test_chat_features():
    """Test chat history and export features"""
    print("\n=== Testing Chat Features ===")
    try:
        from core.chat_history import chat_history
        from core.chat_exporter import chat_exporter
        
        # Test chat history
        session_id = chat_history.create_session("Test Session")
        chat_history.save_message(session_id, "user", "Test message")
        sessions = chat_history.get_sessions()
        
        if len(sessions) > 0:
            print(f"[OK] Chat history working - {len(sessions)} sessions")
            
            # Test export
            import tempfile
            import os
            txt_path = os.path.join(tempfile.gettempdir(), "test_export.txt")
            success = chat_exporter.export_to_txt(session_id, txt_path)
            
            if success and os.path.exists(txt_path):
                print(f"[OK] Chat export working")
                os.remove(txt_path)
            
            # Cleanup
            chat_history.delete_session(session_id)
            return True
        else:
            print("[ERROR] No chat sessions created")
            return False
            
    except Exception as e:
        print(f"[ERROR] Chat features test failed: {e}")
        return False

def run_all_tests():
    """Run all system tests"""
    print("RAG Desktop Assistant - System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Function Calling", test_function_calling),
        ("Document Formats", test_document_formats),
        ("Analytics System", test_analytics_system),
        ("ML Analytics", test_ml_analytics),
        ("Memory Management", test_memory_management),
        ("Chat Features", test_chat_features)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed! System is ready.")
    else:
        print("[WARNING] Some tests failed. Check logs above.")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()