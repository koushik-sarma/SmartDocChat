#!/usr/bin/env python3
"""
Test frontend functionality with file upload
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_file_upload():
    """Test file upload functionality"""
    print("🔧 Testing File Upload Functionality")
    print("=" * 50)
    
    # Test file path
    test_files = [
        "attached_assets/10-Physical-Science-EM-2024-25_1751377752447.pdf",
        "attached_assets/Screenshot_2025-06-30-15-08-40-22_dce875ef40efa4e902b2719365b6f678_1751277079023.jpg",
        "attached_assets/Screenshot_2025-06-30-15-27-57-40_40deb401b9ffe8e1df2f1cc5ba480b12_1751277535864.jpg"
    ]
    
    # Try to upload the PDF file
    pdf_file = test_files[0]
    if Path(pdf_file).exists():
        print(f"📄 Testing upload of: {pdf_file}")
        
        try:
            # Create a session first
            session = requests.Session()
            
            # Visit home page to establish session
            response = session.get(BASE_URL)
            print(f"✅ Session established: {response.status_code}")
            
            # Upload file
            with open(pdf_file, 'rb') as f:
                files = {'file': (Path(pdf_file).name, f, 'application/pdf')}
                response = session.post(f"{BASE_URL}/upload", files=files)
                
            print(f"✅ File upload: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   📄 Uploaded: {result.get('filename', 'Unknown')}")
                print(f"   📊 Chunks: {result.get('chunk_count', 0)}")
                
                # Test documents endpoint after upload
                docs_response = session.get(f"{BASE_URL}/documents")
                if docs_response.status_code == 200:
                    docs = docs_response.json()
                    print(f"   📚 Documents in session: {len(docs)}")
                    
                    # Test chat functionality
                    if docs:
                        chat_response = session.post(f"{BASE_URL}/chat", 
                                                   json={"message": "What is this document about?"})
                        print(f"✅ Chat test: {chat_response.status_code}")
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            print(f"   💬 Response received: {len(chat_result.get('response', ''))} chars")
                        
            else:
                print(f"❌ Upload failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
    else:
        print(f"❌ Test file not found: {pdf_file}")

if __name__ == "__main__":
    test_file_upload()