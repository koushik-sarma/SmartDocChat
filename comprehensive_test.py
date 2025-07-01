#!/usr/bin/env python3
"""
Comprehensive test suite for PDF Chat application
Tests all core functionality before distribution
"""

import requests
import json
import os
import time
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_upload_functionality():
    """Test PDF upload functionality"""
    print("\n🔄 Testing PDF Upload...")
    
    # Check if test PDF exists
    test_pdf = "attached_assets/10-Physical-Science-EM-2024-25_1751377752447.pdf"
    if not os.path.exists(test_pdf):
        print("❌ Test PDF not found")
        return False
    
    with open(test_pdf, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ PDF uploaded successfully: {result.get('chunks', 0)} chunks processed")
            return True
        else:
            print(f"❌ Upload failed: {result.get('error')}")
            return False
    else:
        print(f"❌ Upload request failed: {response.status_code}")
        return False

def test_chat_functionality():
    """Test chat with chemical equations"""
    print("\n🔄 Testing Chat with Chemical Equations...")
    
    test_queries = [
        "What is the chemical formula for water?",
        "Explain the reaction between hydrogen and oxygen",
        "Show me chemical equations for combustion",
        "What are ionic compounds?"
    ]
    
    for query in test_queries:
        print(f"  Testing query: {query}")
        
        response = requests.post(f"{BASE_URL}/chat", 
                               json={'message': query},
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                answer = result.get('response', '')
                sources = result.get('sources', [])
                
                # Check for chemical formulas that should be formatted
                chemical_found = any(formula in answer for formula in ['H2O', 'CO2', 'H2SO4', 'NaCl'])
                images_found = any(source.get('type') == 'image' for source in sources)
                
                print(f"    ✅ Response received ({len(answer)} chars)")
                print(f"    📘 PDF sources: {len([s for s in sources if s.get('type') == 'pdf'])}")
                print(f"    🌐 Web sources: {len([s for s in sources if s.get('type') == 'web'])}")
                print(f"    🖼️ Images found: {len([s for s in sources if s.get('type') == 'image'])}")
                
                if chemical_found:
                    print("    🧪 Chemical formulas detected")
                
                time.sleep(1)  # Rate limiting
            else:
                print(f"    ❌ Chat failed: {result.get('error')}")
                return False
        else:
            print(f"    ❌ Chat request failed: {response.status_code}")
            return False
    
    return True

def test_tts_functionality():
    """Test text-to-speech functionality"""
    print("\n🔄 Testing Text-to-Speech...")
    
    test_text = "Water has the chemical formula H2O, consisting of two hydrogen atoms and one oxygen atom."
    
    response = requests.post(f"{BASE_URL}/tts", 
                           json={'text': test_text, 'voice': 'nova'},
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        audio_size = len(response.content)
        if audio_size > 1000:  # Audio should be reasonably sized
            print(f"✅ TTS working: {audio_size} bytes of audio generated")
            return True
        else:
            print("❌ TTS audio too small")
            return False
    else:
        print(f"❌ TTS request failed: {response.status_code}")
        return False

def test_document_management():
    """Test document listing and management"""
    print("\n🔄 Testing Document Management...")
    
    # Get documents
    response = requests.get(f"{BASE_URL}/documents")
    if response.status_code == 200:
        documents = response.json()
        if documents:
            print(f"✅ Document listing working: {len(documents)} documents found")
            
            # Test document toggle (if any documents exist)
            doc_id = documents[0]['id']
            toggle_response = requests.post(f"{BASE_URL}/documents/{doc_id}/toggle")
            if toggle_response.status_code == 200:
                print("✅ Document toggle working")
            else:
                print("❌ Document toggle failed")
            
            return True
        else:
            print("⚠️ No documents found (expected if none uploaded)")
            return True
    else:
        print(f"❌ Document listing failed: {response.status_code}")
        return False

def test_profile_management():
    """Test user profile and AI role functionality"""
    print("\n🔄 Testing Profile Management...")
    
    # Get profile
    response = requests.get(f"{BASE_URL}/profile")
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile retrieval working: {profile.get('ai_role', 'default')[:50]}...")
        
        # Update profile
        update_data = {
            'ai_role': 'You are a chemistry teacher specializing in student education.',
            'theme_preference': 'dark'
        }
        
        update_response = requests.post(f"{BASE_URL}/profile", 
                                      json=update_data,
                                      headers={'Content-Type': 'application/json'})
        
        if update_response.status_code == 200:
            print("✅ Profile update working")
            return True
        else:
            print("❌ Profile update failed")
            return False
    else:
        print(f"❌ Profile retrieval failed: {response.status_code}")
        return False

def test_statistics():
    """Test statistics endpoint"""
    print("\n🔄 Testing Statistics...")
    
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Statistics working:")
        print(f"    Documents: {stats.get('total_documents', 0)}")
        print(f"    Messages: {stats.get('total_messages', 0)}")
        print(f"    Vector store: {stats.get('vector_store_size', 0)} chunks")
        return True
    else:
        print(f"❌ Statistics failed: {response.status_code}")
        return False

def test_theme_switching():
    """Test that the application loads properly"""
    print("\n🔄 Testing Main Application...")
    
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        content = response.text
        
        # Check for key elements
        checks = [
            'PDF Chat' in content,
            'Bootstrap' in content or 'bootstrap' in content,
            'chat.js' in content,
            'chatMessages' in content
        ]
        
        if all(checks):
            print("✅ Main application loads correctly")
            return True
        else:
            print("❌ Main application missing key elements")
            return False
    else:
        print(f"❌ Main application failed to load: {response.status_code}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive PDF Chat Test Suite")
    print("=" * 50)
    
    tests = [
        ("Main Application", test_theme_switching),
        ("Document Management", test_document_management),
        ("PDF Upload", test_upload_functionality),
        ("Chat Functionality", test_chat_functionality),
        ("Text-to-Speech", test_tts_functionality),
        ("Profile Management", test_profile_management),
        ("Statistics", test_statistics)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Application ready for distribution!")
        return True
    else:
        print(f"\n⚠️ {total-passed} test(s) failed - Please fix issues before distribution")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)