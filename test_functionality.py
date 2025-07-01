#!/usr/bin/env python3
"""
Test script to verify PDF Chat functionality
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_endpoints():
    """Test all critical endpoints"""
    print("🔧 Testing PDF Chat Application Endpoints")
    print("=" * 50)
    
    # Test 1: Home page
    try:
        response = requests.get(BASE_URL)
        print(f"✅ Home page: {response.status_code}")
    except Exception as e:
        print(f"❌ Home page error: {e}")
    
    # Test 2: Documents endpoint
    try:
        response = requests.get(f"{BASE_URL}/documents")
        print(f"✅ Documents endpoint: {response.status_code}")
        if response.status_code == 200:
            docs = response.json()
            print(f"   📄 Found {len(docs)} documents")
    except Exception as e:
        print(f"❌ Documents endpoint error: {e}")
    
    # Test 3: Clear session endpoint
    try:
        response = requests.post(f"{BASE_URL}/clear-session")
        print(f"✅ Clear session: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   🧹 {result.get('message', 'Session cleared')}")
    except Exception as e:
        print(f"❌ Clear session error: {e}")
    
    # Test 4: Clear chat endpoint
    try:
        response = requests.post(f"{BASE_URL}/clear-chat")
        print(f"✅ Clear chat: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   💬 {result.get('message', 'Chat cleared')}")
    except Exception as e:
        print(f"❌ Clear chat error: {e}")
    
    # Test 5: Profile endpoint
    try:
        response = requests.get(f"{BASE_URL}/profile")
        print(f"✅ Profile endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Profile endpoint error: {e}")
    
    # Test 6: Stats endpoint
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"✅ Stats endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")

if __name__ == "__main__":
    test_endpoints()