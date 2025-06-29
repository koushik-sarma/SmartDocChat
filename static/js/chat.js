class PDFChatApp {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.loadStats();
        this.scrollToBottom();
    }
    
    initializeElements() {
        this.fileInput = document.getElementById('pdfUpload');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.uploadStatus = document.getElementById('uploadStatus');
        this.chatForm = document.getElementById('chatForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.documentsList = document.getElementById('documentsList');
        this.docCount = document.getElementById('docCount');
        this.clearSessionBtn = document.getElementById('clearSession');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.totalChunks = document.getElementById('totalChunks');
        this.sessionDocs = document.getElementById('sessionDocs');
    }
    
    setupEventListeners() {
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        this.clearSessionBtn.addEventListener('click', () => this.clearSession());
        
        // Enable input when documents are present
        this.updateInputState();
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        if (!file.type.includes('pdf')) {
            this.showUploadStatus('Only PDF files are allowed', 'error');
            return;
        }
        
        // Validate file size (50MB limit)
        if (file.size > 50 * 1024 * 1024) {
            this.showUploadStatus('File size must be less than 50MB', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        this.showUploadProgress(true);
        this.showUploadStatus('Uploading and processing PDF...', 'info');
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showUploadStatus(
                    `✅ ${result.message} (${result.chunks_processed} chunks processed)`, 
                    'success'
                );
                this.addDocumentToList(result.document);
                this.updateDocumentCount();
                this.updateInputState();
                this.loadStats();
            } else {
                this.showUploadStatus(`❌ ${result.error}`, 'error');
            }
        } catch (error) {
            this.showUploadStatus(`❌ Upload failed: ${error.message}`, 'error');
        } finally {
            this.showUploadProgress(false);
            this.fileInput.value = '';
        }
    }
    
    async handleChatSubmit(event) {
        event.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessageToChat('user', message);
        this.messageInput.value = '';
        this.showTyping(true);
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.addMessageToChat('assistant', result.response, result.sources);
            } else {
                this.addMessageToChat('assistant', `❌ Error: ${result.error}`, null);
            }
        } catch (error) {
            this.addMessageToChat('assistant', `❌ Failed to get response: ${error.message}`, null);
        } finally {
            this.showTyping(false);
        }
    }
    
    addMessageToChat(type, content, sources = null) {
        // Remove welcome message if present
        const welcomeMsg = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message mb-3`;
        
        const timestamp = new Date().toLocaleTimeString();
        const icon = type === 'user' ? 'fa-user' : 'fa-robot';
        const name = type === 'user' ? 'You' : 'Assistant';
        
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = '<div class="sources mt-2"><small class="text-muted">Sources:</small>';
            sources.forEach(source => {
                if (source.type === 'pdf') {
                    sourcesHtml += '<div class="source-item"><i class="fas fa-file-pdf text-danger"></i> PDF Document</div>';
                } else if (source.type === 'web') {
                    sourcesHtml += `<div class="source-item"><i class="fas fa-globe text-info"></i> ${source.title}</div>`;
                }
            });
            sourcesHtml += '</div>';
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <strong>
                        <i class="fas ${icon} me-1"></i>${name}
                    </strong>
                    <small class="text-muted">${timestamp}</small>
                </div>
                <div class="message-text">${this.formatMessageContent(content)}</div>
                ${sourcesHtml}
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessageContent(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/📘/g, '<i class="fas fa-book text-warning"></i>')
            .replace(/🌐/g, '<i class="fas fa-globe text-info"></i>')
            .replace(/\n/g, '<br>');
    }
    
    addDocumentToList(document) {
        const docDiv = document.createElement('div');
        docDiv.className = 'document-item mb-2 p-2 rounded';
        docDiv.dataset.docId = document.id;
        
        docDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-file-pdf text-danger me-2"></i>
                <div class="flex-grow-1">
                    <div class="small fw-bold text-truncate">${document.filename}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">
                        ${document.chunk_count} chunks
                    </div>
                </div>
            </div>
        `;
        
        this.documentsList.appendChild(docDiv);
    }
    
    updateDocumentCount() {
        const count = this.documentsList.children.length;
        this.docCount.textContent = count;
        this.sessionDocs.textContent = count;
    }
    
    updateInputState() {
        const hasDocuments = this.documentsList.children.length > 0;
        this.messageInput.disabled = !hasDocuments;
        this.sendButton.disabled = !hasDocuments;
        
        if (hasDocuments) {
            this.messageInput.placeholder = "Ask a question about your documents...";
        } else {
            this.messageInput.placeholder = "Upload a PDF document first...";
        }
    }
    
    showUploadProgress(show) {
        this.uploadProgress.style.display = show ? 'block' : 'none';
        if (show) {
            this.uploadProgress.querySelector('.progress-bar').style.width = '100%';
        }
    }
    
    showUploadStatus(message, type) {
        this.uploadStatus.innerHTML = message;
        this.uploadStatus.className = `mt-2 small ${this.getStatusClass(type)}`;
        
        // Clear status after 5 seconds for success/error messages
        if (type !== 'info') {
            setTimeout(() => {
                this.uploadStatus.innerHTML = '';
            }, 5000);
        }
    }
    
    getStatusClass(type) {
        switch (type) {
            case 'success': return 'text-success';
            case 'error': return 'text-danger';
            case 'info': return 'text-info';
            default: return 'text-muted';
        }
    }
    
    showTyping(show) {
        this.typingIndicator.style.display = show ? 'block' : 'none';
        this.sendButton.disabled = show;
        
        if (show) {
            this.scrollToBottom();
        }
    }
    
    async clearSession() {
        if (!confirm('Are you sure you want to clear all documents and chat history?')) {
            return;
        }
        
        try {
            const response = await fetch('/clear-session', {
                method: 'POST'
            });
            
            if (response.ok) {
                // Clear UI
                this.documentsList.innerHTML = '';
                this.chatMessages.innerHTML = `
                    <div class="welcome-message text-center text-muted">
                        <i class="fas fa-robot fa-3x mb-3"></i>
                        <h5>Welcome to PDF Chat!</h5>
                        <p>Upload a PDF document and start asking questions.</p>
                        <p>I'll search your documents and the web to provide comprehensive answers.</p>
                    </div>
                `;
                this.updateDocumentCount();
                this.updateInputState();
                this.loadStats();
                this.showUploadStatus('✅ Session cleared successfully', 'success');
            } else {
                const result = await response.json();
                this.showUploadStatus(`❌ ${result.error}`, 'error');
            }
        } catch (error) {
            this.showUploadStatus(`❌ Failed to clear session: ${error.message}`, 'error');
        }
    }
    
    async loadStats() {
        try {
            const response = await fetch('/stats');
            if (response.ok) {
                const stats = await response.json();
                this.totalChunks.textContent = stats.total_chunks;
                this.sessionDocs.textContent = stats.session_documents;
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PDFChatApp();
});
