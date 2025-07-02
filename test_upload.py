"""
Test script to check what's happening during file upload
"""

import requests
import os

# Test the upload endpoint directly
def test_upload():
    url = "http://localhost:5000/upload"
    
    # Create a small test file
    test_content = "This is a simple test document for upload testing."
    
    with open("test_upload.txt", "w") as f:
        f.write(test_content)
    
    # Try uploading
    try:
        with open("test_upload.txt", "rb") as f:
            files = {'file': ('test_upload.txt', f, 'text/plain')}
            response = requests.post(url, files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Cleanup
    if os.path.exists("test_upload.txt"):
        os.remove("test_upload.txt")

if __name__ == "__main__":
    test_upload()