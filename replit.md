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

## User Preferences

Preferred communication style: Simple, everyday language.
Voice customization preferences:
- Indian English pronunciation for clarity
- Optimized for Telugu-speaking teenagers 
- Smooth and easy to understand speech patterns
- Educational content with encouraging phrases