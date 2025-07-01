class PDFChatApp {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.loadStats();
        this.scrollToBottom();
        this.currentAudio = null; // Track current playing audio
    }
    
    initializeElements() {
        // Core elements with null checks
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
        
        // Validate critical elements
        if (!this.fileInput || !this.uploadStatus || !this.chatMessages) {
            console.error('Critical DOM elements missing');
            this.showError('Application initialization failed - please refresh the page');
        }
    }
    
    showError(message) {
        console.error(message);
        if (this.uploadStatus) {
            this.uploadStatus.innerHTML = `<div class="text-danger">${message}</div>`;
        } else if (this.chatMessages) {
            this.chatMessages.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        }
    }
    
    setupEventListeners() {
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        this.clearSessionBtn.addEventListener('click', () => this.clearSession());
        
        // TTS event listeners using event delegation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tts-btn') || e.target.closest('.tts-btn')) {
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
        
        // Phase 2 Settings Event Listeners
        this.setupPhase2Features();
        
        // Enable input when documents are present
        this.updateInputState();
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        console.log('File selected:', file.name, 'Type:', file.type, 'Size:', file.size);
        
        // Validate file type - be more specific about PDF validation
        if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
            this.showUploadStatus('Only PDF files are allowed', 'error');
            return;
        }
        
        // Validate file size (50MB limit)
        if (file.size > 50 * 1024 * 1024) {
            this.showUploadStatus('File size must be less than 50MB', 'error');
            return;
        }
        
        // Validate file is not empty
        if (file.size === 0) {
            this.showUploadStatus('File cannot be empty', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        this.showUploadProgress(true);
        this.showUploadStatus('Uploading and processing PDF...', 'info');
        
        try {
            console.log('Starting upload request...');
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            console.log('Upload response status:', response.status);
            
            let result;
            try {
                result = await response.json();
                console.log('Upload result:', result);
            } catch (parseError) {
                console.error('Failed to parse response JSON:', parseError);
                throw new Error('Invalid server response');
            }
            
            if (response.ok && result && result.message) {
                this.showUploadStatus(
                    `✅ ${result.message} (${result.chunks_processed || 0} chunks processed)`, 
                    'success'
                );
                
                if (result.document) {
                    try {
                        // Check if documentsList exists
                        if (!this.documentsList) {
                            console.error('Documents list element not found');
                            this.documentsList = document.getElementById('documentsList');
                        }
                        
                        if (this.documentsList) {
                            this.addDocumentToList(result.document);
                            this.updateDocumentCount();
                            this.updateInputState();
                            this.loadStats();
                        } else {
                            console.error('Cannot find documents list container');
                        }
                    } catch (uiError) {
                        console.error('UI update error:', uiError);
                        // Don't fail the upload if UI update fails - just log the error
                        console.log('Document data:', result.document);
                        console.log('DocumentsList element:', this.documentsList);
                    }
                }
            } else {
                const errorMsg = (result && result.error) || `HTTP ${response.status}: ${response.statusText}`;
                this.showUploadStatus(`❌ ${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('Upload error details:', error);
            
            // Handle different types of errors
            let errorMessage = 'Upload failed';
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = 'Network error - please check your connection';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            this.showUploadStatus(`❌ ${errorMessage}`, 'error');
        } finally {
            this.showUploadProgress(false);
            if (this.fileInput) {
                this.fileInput.value = '';
            }
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
                <div class="tts-controls mt-2" data-message="${content.replace(/"/g, '&quot;')}">
                    <div class="d-flex flex-wrap align-items-center gap-2">
                        <button class="btn btn-sm btn-outline-primary tts-btn tts-play-btn" 
                                title="Play with voice">
                            <i class="fas fa-play me-1"></i>Play
                        </button>
                        <button class="btn btn-sm btn-outline-success tts-btn tts-download-btn" 
                                title="Download audio">
                            <i class="fas fa-download me-1"></i>Download
                        </button>
                        <select class="form-select form-select-sm voice-select" style="min-width: 180px;">
                            <option value="nova_indian" selected>Nova (Indian English)</option>
                            <option value="shimmer_tenglish">Shimmer (Tenglish)</option>
                            <option value="echo_hindi">Echo (Hindi-English)</option>
                            <option value="alloy_english">Alloy (American English)</option>
                            <option value="fable_tamil">Fable (Tamil-English)</option>
                            <option value="onyx_formal">Onyx (Formal English)</option>
                        </select>
                    </div>
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
    
    addDocumentToList(docData) {
        const docDiv = document.createElement('div');
        docDiv.className = 'document-item mb-2 p-2 rounded border';
        docDiv.dataset.docId = docData.id;
        
        const isActive = docData.is_active !== false;
        const activeClass = isActive ? 'border-success' : 'border-secondary opacity-50';
        docDiv.classList.add(activeClass);
        
        docDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="form-check me-2">
                    <input class="form-check-input doc-toggle" type="checkbox" 
                           ${isActive ? 'checked' : ''} 
                           data-doc-id="${docData.id}"
                           title="Include in context">
                </div>
                <i class="fas fa-file-pdf text-danger me-2"></i>
                <div class="flex-grow-1">
                    <div class="small fw-bold text-truncate">${docData.filename}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">
                        ${docData.chunk_count} chunks • ${this.formatFileSize(docData.file_size)}
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger ms-2 delete-doc-btn" 
                        data-doc-id="${docData.id}" 
                        title="Delete document">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        this.documentsList.appendChild(docDiv);
        
        // Add event listeners for the new controls
        const toggleCheckbox = docDiv.querySelector('.doc-toggle');
        const deleteButton = docDiv.querySelector('.delete-doc-btn');
        
        toggleCheckbox.addEventListener('change', (e) => this.toggleDocumentActive(e));
        deleteButton.addEventListener('click', (e) => this.deleteDocument(e));
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
        const button = e.target.closest('.tts-btn');
        const isDownloadButton = button.classList.contains('tts-download-btn');
        const controlsDiv = button.closest('.tts-controls');
        const messageText = controlsDiv.dataset.message;
        const voiceSelect = controlsDiv.querySelector('.voice-select');
        const selectedVoice = voiceSelect ? voiceSelect.value : 'nova_indian';
        
        if (isDownloadButton) {
            // Handle download
            await this.downloadTTSAudio(messageText, selectedVoice, button);
            return;
        }
        
        // Check if this button is currently playing
        const isCurrentlyPlaying = button.innerHTML.includes('fa-pause');
        
        // If audio is playing and this is the playing button, pause it
        if (this.currentAudio && !this.currentAudio.paused && isCurrentlyPlaying) {
            this.currentAudio.pause();
            button.innerHTML = '<i class="fas fa-play me-1"></i>Play';
            return;
        }
        
        // Stop any currently playing audio
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            // Reset the previous playing button
            const previousButton = document.querySelector('.tts-play-btn:not([disabled]) i.fa-pause');
            if (previousButton) {
                previousButton.closest('.tts-play-btn').innerHTML = '<i class="fas fa-play me-1"></i>Play';
            }
        }
        
        // Update button state to loading
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
                    download: false
                })
            });
            
            if (!response.ok) {
                throw new Error('TTS request failed');
            }
            
            // Create audio element and play
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            this.currentAudio = new Audio(audioUrl);
            
            // Update button to show pause state
            button.innerHTML = '<i class="fas fa-pause me-1"></i>Pause';
            button.disabled = false;
            
            this.currentAudio.addEventListener('ended', () => {
                button.innerHTML = '<i class="fas fa-play me-1"></i>Play';
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
    
    async downloadTTSAudio(messageText, selectedVoice, button) {
        this.updateDownloadButtonState(button, 'loading');
        
        try {
            const response = await fetch('/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: messageText,
                    voice: selectedVoice,
                    download: true
                })
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                
                // Create download link
                const downloadLink = document.createElement('a');
                downloadLink.href = audioUrl;
                downloadLink.download = `tts_audio_${selectedVoice}_${Date.now()}.mp3`;
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                URL.revokeObjectURL(audioUrl);
                this.updateDownloadButtonState(button, 'success');
                
                setTimeout(() => {
                    this.updateDownloadButtonState(button, 'download');
                }, 2000);
            } else {
                throw new Error('Failed to download audio');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.updateDownloadButtonState(button, 'error');
            setTimeout(() => {
                this.updateDownloadButtonState(button, 'download');
            }, 2000);
        }
    }
    
    updateTTSButtonState(button, state) {
        if (!button) return;
        
        button.disabled = false;
        switch (state) {
            case 'play':
                button.innerHTML = '<i class="fas fa-play me-1"></i>Play';
                break;
            case 'pause':
                button.innerHTML = '<i class="fas fa-pause me-1"></i>Pause';
                break;
            case 'loading':
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
                button.disabled = true;
                break;
            case 'error':
                button.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
                button.disabled = true;
                break;
        }
    }
    
    updateDownloadButtonState(button, state) {
        if (!button) return;
        
        button.disabled = false;
        switch (state) {
            case 'download':
                button.innerHTML = '<i class="fas fa-download me-1"></i>Download';
                break;
            case 'loading':
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Downloading...';
                button.disabled = true;
                break;
            case 'success':
                button.innerHTML = '<i class="fas fa-check me-1"></i>Downloaded';
                button.disabled = true;
                break;
            case 'error':
                button.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
                button.disabled = true;
                break;
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
    
    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    async toggleDocumentActive(e) {
        const docId = e.target.dataset.docId;
        const isChecked = e.target.checked;
        
        try {
            const response = await fetch(`/toggle-document/${docId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                const docDiv = e.target.closest('.document-item');
                
                // Update visual styling
                if (isChecked) {
                    docDiv.classList.remove('border-secondary', 'opacity-50');
                    docDiv.classList.add('border-success');
                } else {
                    docDiv.classList.remove('border-success');
                    docDiv.classList.add('border-secondary', 'opacity-50');
                }
                
                this.showUploadStatus(`📄 ${result.message}`, 'info');
            } else {
                // Revert checkbox if request failed
                e.target.checked = !isChecked;
                const errorData = await response.json();
                this.showUploadStatus(`❌ ${errorData.error}`, 'error');
            }
        } catch (error) {
            // Revert checkbox if request failed
            e.target.checked = !isChecked;
            console.error('Toggle error:', error);
            this.showUploadStatus('❌ Failed to update document status', 'error');
        }
    }
    
    async deleteDocument(e) {
        const docId = e.target.closest('.delete-doc-btn').dataset.docId;
        const docDiv = e.target.closest('.document-item');
        const filename = docDiv.querySelector('.fw-bold').textContent;
        
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }
        
        try {
            const button = e.target.closest('.delete-doc-btn');
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            const response = await fetch(`/delete-document/${docId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Remove from DOM
                docDiv.remove();
                
                // Update counts
                this.updateDocumentCount();
                this.updateInputState();
                this.loadStats();
                
                this.showUploadStatus(`🗑️ ${result.message}`, 'success');
                
                // If no documents left, show appropriate message
                if (result.remaining_documents === 0) {
                    this.showUploadStatus('📋 All documents removed. Upload a PDF to get started.', 'info');
                }
            } else {
                const errorData = await response.json();
                this.showUploadStatus(`❌ ${errorData.error}`, 'error');
                // Restore button
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-trash"></i>';
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showUploadStatus('❌ Failed to delete document', 'error');
            // Restore button
            const button = e.target.closest('.delete-doc-btn');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-trash"></i>';
        }
    }
    
    setupPhase2Features() {
        // AI Role Selection
        const aiRoleSelect = document.getElementById('aiRole');
        const customRoleTextarea = document.getElementById('customRole');
        
        if (aiRoleSelect) {
            aiRoleSelect.addEventListener('change', (e) => {
                if (e.target.value === 'custom') {
                    customRoleTextarea.style.display = 'block';
                    customRoleTextarea.focus();
                } else {
                    customRoleTextarea.style.display = 'none';
                    this.updateProfile({ ai_role: e.target.value });
                }
            });
        }
        
        if (customRoleTextarea) {
            customRoleTextarea.addEventListener('blur', () => {
                if (customRoleTextarea.value.trim()) {
                    this.updateProfile({ ai_role: customRoleTextarea.value.trim() });
                }
            });
        }
        
        // Theme Toggle
        const darkTheme = document.getElementById('darkTheme');
        const lightTheme = document.getElementById('lightTheme');
        
        if (darkTheme && lightTheme) {
            darkTheme.addEventListener('change', () => {
                if (darkTheme.checked) {
                    this.setTheme('dark');
                    this.updateProfile({ theme_preference: 'dark' });
                }
            });
            
            lightTheme.addEventListener('change', () => {
                if (lightTheme.checked) {
                    this.setTheme('light');
                    this.updateProfile({ theme_preference: 'light' });
                }
            });
        }
        
        // Voice Input Toggle
        const voiceInput = document.getElementById('voiceInput');
        if (voiceInput) {
            voiceInput.addEventListener('change', (e) => {
                this.updateProfile({ voice_enabled: e.target.checked });
                if (e.target.checked) {
                    this.initializeVoiceInput();
                } else {
                    this.disableVoiceInput();
                }
            });
        }
        
        // Load current profile settings
        this.loadProfile();
    }
    
    async loadProfile() {
        try {
            const response = await fetch('/profile');
            if (response.ok) {
                const profile = await response.json();
                
                // Set AI role
                const aiRoleSelect = document.getElementById('aiRole');
                const customRoleTextarea = document.getElementById('customRole');
                
                if (aiRoleSelect && profile.ai_role) {
                    const matchingOption = Array.from(aiRoleSelect.options).find(
                        option => option.value === profile.ai_role
                    );
                    
                    if (matchingOption) {
                        aiRoleSelect.value = profile.ai_role;
                    } else {
                        aiRoleSelect.value = 'custom';
                        customRoleTextarea.style.display = 'block';
                        customRoleTextarea.value = profile.ai_role;
                    }
                }
                
                // Set theme
                if (profile.theme_preference === 'light') {
                    document.getElementById('lightTheme').checked = true;
                    this.setTheme('light');
                } else {
                    document.getElementById('darkTheme').checked = true;
                    this.setTheme('dark');
                }
                
                // Set voice input
                const voiceInput = document.getElementById('voiceInput');
                if (voiceInput && profile.voice_enabled) {
                    voiceInput.checked = true;
                    this.initializeVoiceInput();
                }
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    }
    
    async updateProfile(updates) {
        try {
            const response = await fetch('/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Profile updated:', result.message);
            } else {
                console.error('Failed to update profile');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
        }
    }
    
    setTheme(theme) {
        const body = document.body;
        const html = document.documentElement;
        
        if (theme === 'light') {
            html.setAttribute('data-bs-theme', 'light');
            body.classList.remove('dark-theme');
            body.classList.add('light-theme');
        } else {
            html.setAttribute('data-bs-theme', 'dark');
            body.classList.remove('light-theme');
            body.classList.add('dark-theme');
        }
    }
    
    initializeVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showUploadStatus('🎤 Voice input not supported in this browser', 'info');
            return;
        }
        
        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.messageInput.value = transcript;
                this.messageInput.focus();
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.showUploadStatus('🎤 Voice input error. Please try again.', 'error');
            };
            
            // Add voice button to input area
            this.addVoiceButton();
            
        } catch (error) {
            console.error('Voice recognition setup error:', error);
            this.showUploadStatus('🎤 Voice input setup failed', 'error');
        }
    }
    
    addVoiceButton() {
        // Add voice button next to send button
        const chatForm = document.getElementById('chatForm');
        if (chatForm && !document.getElementById('voiceButton')) {
            const voiceButton = document.createElement('button');
            voiceButton.type = 'button';
            voiceButton.id = 'voiceButton';
            voiceButton.className = 'btn btn-outline-secondary ms-2';
            voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceButton.title = 'Voice Input';
            
            voiceButton.addEventListener('click', () => this.startVoiceRecognition());
            
            const sendButton = chatForm.querySelector('button[type="submit"]');
            sendButton.parentNode.insertBefore(voiceButton, sendButton.nextSibling);
        }
    }
    
    startVoiceRecognition() {
        if (this.recognition) {
            const voiceButton = document.getElementById('voiceButton');
            voiceButton.innerHTML = '<i class="fas fa-stop text-danger"></i>';
            voiceButton.disabled = true;
            
            this.recognition.start();
            
            setTimeout(() => {
                this.recognition.stop();
                voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
                voiceButton.disabled = false;
            }, 5000); // Stop after 5 seconds
        }
    }
    
    disableVoiceInput() {
        if (this.recognition) {
            this.recognition = null;
        }
        
        const voiceButton = document.getElementById('voiceButton');
        if (voiceButton) {
            voiceButton.remove();
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PDFChatApp();
});
