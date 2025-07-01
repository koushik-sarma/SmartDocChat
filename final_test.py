#!/usr/bin/env python3
"""
Comprehensive test of all PDF Chat functionality
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_complete_workflow():
    """Test the complete workflow from upload to chat"""
    print("🧪 COMPREHENSIVE WORKFLOW TEST")
    print("=" * 50)
    
    # Create a test session
    session = requests.Session()
    
    # Step 1: Visit home page to establish session
    try:
        response = session.get(BASE_URL)
        print(f"✅ Home page loads: {response.status_code}")
        
        if "PDF Chat" in response.text:
            print("   📄 Page content correct")
        else:
            print("   ❌ Page content missing")
            
    except Exception as e:
        print(f"❌ Home page error: {e}")
        return False
    
    # Step 2: Test profile endpoint
    try:
        response = session.get(f"{BASE_URL}/profile")
        print(f"✅ Profile endpoint: {response.status_code}")
        if response.status_code == 200:
            profile = response.json()
            print(f"   👤 AI Role: {profile.get('ai_role', 'Unknown')[:50]}...")
    except Exception as e:
        print(f"❌ Profile error: {e}")
    
    # Step 3: Test documents endpoint (should be empty initially)
    try:
        response = session.get(f"{BASE_URL}/documents")
        print(f"✅ Documents endpoint: {response.status_code}")
        if response.status_code == 200:
            docs = response.json()
            print(f"   📚 Initial documents: {len(docs)}")
    except Exception as e:
        print(f"❌ Documents error: {e}")
    
    # Step 4: Test file upload
    test_files = [
        "attached_assets/10-Physical-Science-EM-2024-25_1751377752447.pdf"
    ]
    
    uploaded = False
    for pdf_file in test_files:
        if Path(pdf_file).exists():
            print(f"📄 Testing upload: {Path(pdf_file).name}")
            
            try:
                with open(pdf_file, 'rb') as f:
                    files = {'file': (Path(pdf_file).name, f, 'application/pdf')}
                    response = session.post(f"{BASE_URL}/upload", files=files)
                
                print(f"✅ Upload response: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   📄 Filename: {result.get('filename', 'Unknown')}")
                    print(f"   📊 Chunks: {result.get('chunk_count', 0)}")
                    uploaded = True
                    break
                else:
                    print(f"   ❌ Upload failed: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Upload error: {e}")
    
    if not uploaded:
        print("❌ No files could be uploaded - skipping chat test")
        return False
    
    # Step 5: Test documents endpoint after upload
    try:
        response = session.get(f"{BASE_URL}/documents")
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Documents after upload: {len(docs)}")
            for doc in docs:
                print(f"   📄 {doc.get('filename', 'Unknown')} - {doc.get('chunk_count', 0)} chunks")
    except Exception as e:
        print(f"❌ Documents check error: {e}")
    
    # Step 6: Test chat functionality
    try:
        chat_response = session.post(f"{BASE_URL}/chat", 
                                   json={"message": "What is this document about?"})
        print(f"✅ Chat response: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            response_text = chat_result.get('response', '')
            sources = chat_result.get('sources', [])
            
            print(f"   💬 Response length: {len(response_text)} characters")
            print(f"   📚 Sources found: {len(sources)}")
            print(f"   🔍 Response preview: {response_text[:100]}...")
            
            if sources:
                for i, source in enumerate(sources):
                    source_type = source.get('type', 'Unknown')
                    print(f"   📖 Source {i+1}: {source_type}")
        else:
            print(f"   ❌ Chat failed: {chat_response.text}")
            
    except Exception as e:
        print(f"❌ Chat error: {e}")
    
    # Step 7: Test clear chat
    try:
        response = session.post(f"{BASE_URL}/clear-chat")
        print(f"✅ Clear chat: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   🧹 {result.get('message', 'Chat cleared')}")
    except Exception as e:
        print(f"❌ Clear chat error: {e}")
    
    # Step 8: Test clear session
    try:
        response = session.post(f"{BASE_URL}/clear-session")
        print(f"✅ Clear session: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   🗑️ {result.get('message', 'Session cleared')}")
    except Exception as e:
        print(f"❌ Clear session error: {e}")
    
    print("\n🎉 WORKFLOW TEST COMPLETE!")
    return True

if __name__ == "__main__":
    test_complete_workflow()