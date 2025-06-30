// Debug script to test upload functionality
console.log('Testing PDF upload functionality...');

// Test basic upload function
function testUpload() {
    const formData = new FormData();
    
    // Create a minimal test file (will fail validation but test the JS)
    const testFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    formData.append('file', testFile);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(result => {
        console.log('Upload test result:', result);
    })
    .catch(error => {
        console.error('Upload test error:', error);
    });
}

// Run test
testUpload();