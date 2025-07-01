# PDF Chat - RAG Assistant

## Overview

This is a Flask-based PDF chat application that implements Retrieval-Augmented Generation (RAG) to enable users to chat with their PDF documents. The system combines document content with web search results to provide comprehensive answers to user queries.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with connection pooling and optimization
- **Session Management**: Flask sessions with proxy fix for deployment
- **File Handling**: Werkzeug secure file handling with 50MB upload limit
- **Logging**: Built-in Python logging with DEBUG level

### Frontend Architecture
- **Template Engine**: Jinja2 templates
- **UI Framework**: Bootstrap with dark theme, mobile-first responsive design
- **Icons**: Font Awesome
- **JavaScript**: Vanilla ES6 classes for chat functionality with mobile sidebar controls
- **Styling**: Custom CSS with Bootstrap variables, touch-friendly interface
- **Mobile Features**: Responsive layout, touch-optimized controls, sidebar navigation

### AI/ML Components
- **LLM Integration**: OpenAI GPT models via OpenAI Python client
- **Vector Database**: FAISS for similarity search
- **Embeddings**: OpenAI text-embedding models (1536 dimensions)
- **Text Processing**: pdfplumber for PDF text extraction
- **Text-to-Speech**: OpenAI TTS with multi-language support, play/pause controls, audio download, and Tenglish (Telugu-English) voice processing

## Key Components

### 1. Document Processing Pipeline
- **PDFProcessor**: Extracts text from PDFs in configurable chunks (default 1000 words)
- **VectorStore**: Manages FAISS index for document embeddings with cosine similarity
- **Text Chunking**: Streaming approach to handle large files efficiently

### 2. Chat System
- **ChatService**: Orchestrates PDF content retrieval and web search
- **Hybrid Search**: Combines PDF vector search with DuckDuckGo web search
- **Context Assembly**: Merges multiple sources with relevance scoring

### 3. Web Search Integration
- **WebSearcher**: DuckDuckGo API integration for real-time information
- **Source Attribution**: Tracks and displays source information for all responses

### 4. Database Models
- **Document**: Stores PDF metadata (filename, path, chunk count, file size)
- **ChatMessage**: Stores conversation history with source attribution
- **Session Management**: UUID-based sessions for multi-user support

## Data Flow

1. **PDF Upload**: User uploads PDF → File validation → Text extraction → Chunking → Embedding generation → Vector storage
2. **Query Processing**: User question → Vector similarity search → Web search (if needed) → Context assembly → LLM response → Source attribution
3. **Response Display**: Formatted response with expandable source citations

## External Dependencies

### Required APIs
- **OpenAI API**: For embeddings and chat completions (requires OPENAI_API_KEY)
- **DuckDuckGo API**: For web search (no API key required)

### Python Packages
- Flask ecosystem (Flask, SQLAlchemy, Werkzeug)
- AI/ML libraries (openai, faiss-cpu, numpy)
- PDF processing (pdfplumber)
- HTTP requests (requests)

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI services
- `DATABASE_URL`: Optional database connection string (defaults to SQLite)
- `SESSION_SECRET`: Optional session secret (has development default)

## Deployment Strategy

### Development
- Flask development server with debug mode
- SQLite database for simplicity
- Local file storage in `uploads/` directory

### Production Considerations
- Proxy fix middleware included for reverse proxy deployment
- Database pooling configured with connection recycling
- Environment-based configuration for secrets
- File upload size limits enforced

### File Structure
```
├── app.py              # Flask application factory
├── main.py             # Application entry point
├── models.py           # Database models
├── routes.py           # HTTP route handlers
├── chat_service.py     # Core chat logic
├── pdf_processor.py    # PDF text extraction
├── vector_store.py     # FAISS vector operations
├── web_search.py       # Web search integration
├── templates/          # HTML templates
└── static/            # CSS/JS assets
```

## Changelog
- June 29, 2025: Initial setup with complete RAG application
- June 29, 2025: Added PostgreSQL database with connection pooling
- June 29, 2025: Enhanced PDF processing with PyMuPDF fallback
- June 29, 2025: Improved error handling for robust file uploads
- June 29, 2025: Fixed logging conflicts and PDF processing errors
- June 29, 2025: Verified full system functionality (upload, chat, search)
- June 29, 2025: Added TTS functionality using OpenAI TTS with voice selection and expressive speech processing
- June 30, 2025: Enhanced mobile responsiveness with touch-friendly controls, sidebar navigation, and optimized layouts for all screen sizes
- June 30, 2025: Added advanced TTS features with play/pause controls, audio download capability, and multi-language support including Tenglish (Telugu-English mix)
- July 1, 2025: Implemented comprehensive document management with delete functionality and context selection
- July 1, 2025: Enhanced PDF processing with robust multi-fallback error handling (pdfplumber + PyMuPDF)
- July 1, 2025: Fixed document display issues and added individual document control capabilities
- July 1, 2025: Fixed Phase 2 bugs - Dark/Light theme toggle working properly with CSS switching
- July 1, 2025: Moved voice input from sidebar to chat input area (Google/WhatsApp style)
- July 1, 2025: Added comprehensive help panel with instructions and tool capabilities
- July 1, 2025: Fixed PDF source deduplication - single entry per document type in Sources
- July 1, 2025: Implemented PDF image extraction with query-based relevance filtering
- July 1, 2025: Enhanced voice input with browser speech recognition (Chrome/Edge optimized)
- July 1, 2025: Fixed session context isolation - documents now properly filtered by session
- July 1, 2025: Fixed light theme styling with proper text colors and blue/orange chat bubbles  
- July 1, 2025: Added multi-format document support (PDF, DOCX, TXT, MD files)
- July 1, 2025: Implemented document comparison and cross-referencing features
- July 1, 2025: Added automatic response regeneration when AI personality changes
- July 1, 2025: Fixed PyMuPDF import issue preventing PDF image extraction
- July 1, 2025: Fixed document controls disappearing on page refresh - delete/toggle buttons now persist
- July 1, 2025: Enhanced PDF image extraction with comprehensive debugging and automatic trigger
- July 1, 2025: Updated frontend to display extracted PDF images in chat with click-to-expand functionality
- July 1, 2025: Completely resolved PDF upload crash with smart processing system (>30MB auto-switches to PyMuPDF)
- July 1, 2025: Enhanced chemical equation parsing with comprehensive subscript/superscript support
- July 1, 2025: Fixed JavaScript regex errors and improved chemical formula recognition for student education
- July 1, 2025: Added extensive chemical formula database (H2O→H₂O, CO2→CO₂, H2SO4→H₂SO₄, ionic charges)
- July 1, 2025: Added AI personality refresh button with real-time response regeneration capability
- July 1, 2025: Implemented comprehensive formatting for chemistry and physics content with proper visual styling
- July 1, 2025: Fixed message formatting persistence after page refresh with formatExistingMessages() function
- July 1, 2025: Enhanced arrow handling for chemical reactions (→, ←, ↔, ⇌) with comprehensive regex patterns
- July 1, 2025: Improved image extraction system with content-aware filtering and size-based relevance
- July 1, 2025: Added intelligent image display in chat responses with click-to-expand functionality
- July 1, 2025: CRITICAL FIX - Resolved all server response errors with comprehensive backend repairs
- July 1, 2025: Fixed missing PyMuPDF extraction method preventing large file processing
- July 1, 2025: Corrected type errors in chat service causing null response crashes
- July 1, 2025: Verified complete functionality: uploads (text/PDF), chat with document context, session isolation

## Phase 1 Complete - Checkpoint
Successfully implemented comprehensive PDF chat application with:
- Robust PDF processing with multi-fallback error handling
- Advanced TTS with play/pause controls and multi-language support including Tenglish
- Complete document management (upload, delete, context selection)
- Mobile-responsive design with touch-friendly controls
- Enhanced UI with proper error handling and visual feedback

## Phase 2 Development Goals
- PDF image extraction and contextual display
- Role-based AI persona with custom instructions
- Dark/Light mode toggle for improved user experience
- Voice input capability for hands-free interaction

## User Preferences

Preferred communication style: Simple, everyday language.
Voice customization preferences:
- Indian English pronunciation for clarity
- Optimized for Telugu-speaking teenagers 
- Smooth and easy to understand speech patterns
- Educational content with encouraging phrases