class PDFChatApp {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.loadStats();
        this.scrollToBottom();
        this.currentAudio = null; // Track current playing audio
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
        
        // Mobile elements
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.sidebar = document.getElementById('sidebar');
        this.mobileOverlay = document.getElementById('mobileOverlay');
    }
    
    setupEventListeners() {
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        this.clearSessionBtn.addEventListener('click', () => this.clearSession());
        
        // TTS event listeners using event delegation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tts-play-btn') || e.target.closest('.tts-play-btn')) {
                this.handleTTSPlay(e);
            }
        });
        
        // Mobile sidebar controls
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        if (this.mobileOverlay) {
            this.mobileOverlay.addEventListener('click', () => this.closeSidebar());
        }
        
        // Close sidebar on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.sidebar.classList.contains('show')) {
                this.closeSidebar();
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 768) {
                this.closeSidebar();
            }
        });
        
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
        
        let ttsControlsHtml = '';
        if (type === 'assistant') {
            ttsControlsHtml = `
                <div class="message-actions mt-2">
                    <button class="btn btn-sm btn-outline-primary tts-play-btn" 
                            data-message="${content.replace(/"/g, '&quot;')}" 
                            title="Play with voice">
                        <i class="fas fa-play me-1"></i>Play
                    </button>
                    <select class="form-select form-select-sm d-inline-block w-auto ms-2 voice-select">
                        <option value="nova" selected>Nova (Recommended for Students)</option>
                        <option value="alloy">Alloy (Clear & Neutral)</option>
                        <option value="shimmer">Shimmer (Friendly Female)</option>
                        <option value="echo">Echo (Male Teacher)</option>
                        <option value="fable">Fable (British Accent)</option>
                        <option value="onyx">Onyx (Deep Male)</option>
                    </select>
                </div>
            `;
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
                ${ttsControlsHtml}
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
    
    async handleTTSPlay(e) {
        e.preventDefault();
        const button = e.target.closest('.tts-play-btn');
        const messageText = button.dataset.message;
        const voiceSelect = button.parentElement.querySelector('.voice-select');
        const selectedVoice = voiceSelect.value;
        
        // Stop current audio if playing
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            this.currentAudio = null;
            // Reset all play buttons
            document.querySelectorAll('.tts-play-btn').forEach(btn => {
                btn.innerHTML = '<i class="fas fa-play me-1"></i>Play';
                btn.disabled = false;
            });
        }
        
        // Update button state
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        button.disabled = true;
        
        try {
            const response = await fetch('/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: messageText,
                    voice: selectedVoice,
                    emotion: 'explanatory'
                })
            });
            
            if (!response.ok) {
                throw new Error('TTS request failed');
            }
            
            // Create audio element and play
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            this.currentAudio = new Audio(audioUrl);
            
            button.innerHTML = '<i class="fas fa-pause me-1"></i>Playing...';
            
            this.currentAudio.addEventListener('ended', () => {
                button.innerHTML = '<i class="fas fa-play me-1"></i>Play';
                button.disabled = false;
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
            });
            
            this.currentAudio.addEventListener('error', () => {
                button.innerHTML = '<i class="fas fa-play me-1"></i>Play';
                button.disabled = false;
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                console.error('Audio playback error');
            });
            
            await this.currentAudio.play();
            
        } catch (error) {
            console.error('TTS Error:', error);
            button.innerHTML = '<i class="fas fa-play me-1"></i>Play';
            button.disabled = false;
            
            // Show error message
            this.showUploadStatus('Voice playback failed. Please try again.', 'error');
        }
    }
    
    toggleSidebar() {
        if (this.sidebar.classList.contains('show')) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }
    
    openSidebar() {
        this.sidebar.classList.add('show');
        this.mobileOverlay.classList.add('show');
        document.body.classList.add('sidebar-open');
    }
    
    closeSidebar() {
        this.sidebar.classList.remove('show');
        this.mobileOverlay.classList.remove('show');
        document.body.classList.remove('sidebar-open');
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
