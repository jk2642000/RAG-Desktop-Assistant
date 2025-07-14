#!/usr/bin/env python3
"""
Quick Gemini API test script
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_gemini():
    print("[*] Testing Gemini API...")
    
    # Load environment
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    print(f"[*] API Key present: {bool(api_key)}")
    if api_key:
        print(f"[*] API Key starts with: {api_key[:10]}...")
    
    if not api_key:
        print("[ERROR] No GEMINI_API_KEY found in .env file")
        return False
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        print("[OK] Gemini configured")
        
        # Test simple generation
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content("Say 'Hello from Gemini!'")
        
        if response.text:
            print(f"[OK] Gemini response: {response.text}")
            return True
        else:
            print("[ERROR] Empty response from Gemini")
            return False
            
    except Exception as e:
        print(f"[ERROR] Gemini test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini()
    print(f"\n[RESULT] Gemini API {'Working' if success else 'Failed'}")