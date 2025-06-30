#!/usr/bin/env python3
"""
Comprehensive test suite for PDF Chat application
Tests upload, processing, chat functionality, and edge cases
"""

import requests
import os
import json
import time

BASE_URL = "http://localhost:5000"

def test_upload_valid_pdf():
    """Test uploading a valid PDF file"""
    print("Testing valid PDF upload...")
    
    # Use existing test PDF
    test_file = "uploads/test_doc.pdf"
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return False
    
    with open(test_file, 'rb') as f:
        files = {'file': ('test_upload.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful: {result.get('message', 'No message')}")
        print(f"   Chunks processed: {result.get('chunks_processed', 0)}")
        return True
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return False

def test_upload_invalid_file():
    """Test uploading a non-PDF file"""
    print("Testing invalid file upload...")
    
    # Create a temporary text file
    with open("temp_test.txt", "w") as f:
        f.write("This is not a PDF file")
    
    try:
        with open("temp_test.txt", 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 400:
            result = response.json()
            print(f"✅ Correctly rejected invalid file: {result.get('error')}")
            return True
        else:
            print(f"❌ Should have rejected invalid file but got: {response.status_code}")
            return False
    finally:
        if os.path.exists("temp_test.txt"):
            os.remove("temp_test.txt")

def test_chat_functionality():
    """Test chat with uploaded documents"""
    print("Testing chat functionality...")
    
    chat_data = {
        'message': 'What is this document about?'
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Chat response received: {result.get('response', 'No response')[:100]}...")
        if result.get('sources'):
            print(f"   Sources: {len(result['sources'])} found")
        return True
    else:
        print(f"❌ Chat failed: {response.status_code} - {response.text}")
        return False

def test_get_documents():
    """Test retrieving uploaded documents"""
    print("Testing document retrieval...")
    
    response = requests.get(f"{BASE_URL}/documents")
    
    if response.status_code == 200:
        documents = response.json()
        print(f"✅ Retrieved {len(documents)} documents")
        for doc in documents[:3]:  # Show first 3
            print(f"   - {doc.get('filename')} ({doc.get('chunk_count')} chunks)")
        return True
    else:
        print(f"❌ Document retrieval failed: {response.status_code}")
        return False

def test_stats_endpoint():
    """Test statistics endpoint"""
    print("Testing stats endpoint...")
    
    response = requests.get(f"{BASE_URL}/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Stats retrieved:")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Session docs: {stats.get('session_docs', 0)}")
        return True
    else:
        print(f"❌ Stats failed: {response.status_code}")
        return False

def test_tts_functionality():
    """Test text-to-speech functionality"""
    print("Testing TTS functionality...")
    
    tts_data = {
        'text': 'Hello, this is a test of the text to speech system.',
        'voice': 'nova'
    }
    
    response = requests.post(f"{BASE_URL}/tts", json=tts_data)
    
    if response.status_code == 200:
        print(f"✅ TTS generated audio ({len(response.content)} bytes)")
        return True
    else:
        print(f"❌ TTS failed: {response.status_code}")
        return False

def test_large_file_upload():
    """Test uploading a larger PDF file"""
    print("Testing large file upload...")
    
    # Use existing larger PDF
    large_files = [f for f in os.listdir("uploads/") if f.endswith('.pdf') and os.path.getsize(f"uploads/{f}") > 1000000]
    
    if not large_files:
        print("⚠️  No large PDF files found for testing")
        return True
    
    test_file = f"uploads/{large_files[0]}"
    file_size = os.path.getsize(test_file)
    print(f"   Using file: {large_files[0]} ({file_size:,} bytes)")
    
    start_time = time.time()
    
    with open(test_file, 'rb') as f:
        files = {'file': (large_files[0], f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/upload", files=files, timeout=120)
    
    upload_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Large file upload successful in {upload_time:.1f}s")
        print(f"   Chunks processed: {result.get('chunks_processed', 0)}")
        return True
    else:
        print(f"❌ Large file upload failed: {response.status_code}")
        return False

def run_all_tests():
    """Run all test cases"""
    print("🚀 Starting comprehensive PDF Chat application tests\n")
    
    tests = [
        test_upload_valid_pdf,
        test_upload_invalid_file,
        test_get_documents,
        test_stats_endpoint,
        test_chat_functionality,
        test_tts_functionality,
        test_large_file_upload,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
            print()
    
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Application is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == "__main__":
    run_all_tests()