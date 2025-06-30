import os
import uuid
import json
import logging
import tempfile
from flask import render_template, request, jsonify, session, redirect, url_for, flash, Response, send_from_directory, make_response
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, ChatMessage
from pdf_processor import PDFProcessor
from chat_service import ChatService
from tts_service import SimpleTTSWrapper

logger = logging.getLogger(__name__)

# Initialize services
pdf_processor = PDFProcessor()
chat_service = ChatService()
tts_service = SimpleTTSWrapper()

def allowed_file(filename):
    """Check if file is a PDF."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/')
def index():
    """Main chat interface."""
    # Initialize session ID if not present
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Get documents for this session
    documents = Document.query.filter_by(session_id=session['session_id']).all()
    
    # Get chat history
    messages = ChatMessage.query.filter_by(session_id=session['session_id']).order_by(ChatMessage.timestamp).all()
    
    return render_template('index.html', 
                         documents=[doc.to_dict() for doc in documents],
                         messages=[msg.to_dict() for msg in messages])

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file or file.filename == '' or file.filename is None:
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Ensure session ID exists
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # Save file
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logging.info(f"Attempting to save file to: {file_path}")
        
        try:
            file.save(file_path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File was not saved to {file_path}")
            file_size = os.path.getsize(file_path)
            logging.info(f"File saved successfully: {file_path}, size: {file_size} bytes")
        except Exception as e:
            logging.error(f"Failed to save file {file_path}: {str(e)}")
            raise ValueError(f"Failed to save uploaded file: {str(e)}")
        
        # Process PDF
        try:
            # Validate PDF file before processing
            try:
                pdf_info = pdf_processor.get_pdf_info(file_path)
                if pdf_info['page_count'] == 0:
                    raise ValueError("PDF file contains no readable pages")
            except Exception as e:
                raise ValueError(f"Invalid PDF file: {str(e)}")
            
            # Extract text chunks
            chunks = []
            try:
                chunk_generator = pdf_processor.extract_text_chunks(file_path)
                chunks = list(chunk_generator)
            except Exception as e:
                raise ValueError(f"Could not extract text from PDF: {str(e)}")
            
            if not chunks:
                raise ValueError("No text content could be extracted from the PDF")
            
            # Save document record
            document = Document(
                session_id=session['session_id'],
                filename=file.filename,  # Original filename
                file_path=file_path,
                chunk_count=len(chunks),
                file_size=file_size
            )
            db.session.add(document)
            db.session.commit()
            
            # Add to vector store
            try:
                chat_service.process_pdf_chunks(chunks, document.id)
            except Exception as e:
                # Rollback database if vector store fails
                db.session.rollback()
                raise ValueError(f"Failed to process document for search: {str(e)}")
            
            return jsonify({
                'message': f'Successfully uploaded and processed {file.filename}',
                'document': document.to_dict(),
                'chunks_processed': len(chunks)
            })
            
        except ValueError as e:
            # Handle validation errors with user-friendly messages
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            logger.warning(f"PDF validation error: {e}")
            return jsonify({'error': str(e)}), 400
            
        except Exception as e:
            # Handle unexpected errors
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            logger.error(f"Unexpected error processing PDF: {e}")
            return jsonify({'error': 'An unexpected error occurred while processing the PDF. Please try again with a different file.'}), 500
            
    except Exception as e:
        logger.error(f"Error in file upload: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Ensure session ID exists
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        
        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            message_type='user',
            content=user_message
        )
        db.session.add(user_msg)
        
        # Generate response
        try:
            response_text, sources = chat_service.generate_response(user_message, session_id)
            
            # Save assistant response
            assistant_msg = ChatMessage(
                session_id=session_id,
                message_type='assistant',
                content=response_text,
                sources=json.dumps(sources) if sources else None
            )
            db.session.add(assistant_msg)
            db.session.commit()
            
            return jsonify({
                'response': response_text,
                'sources': sources,
                'message_id': assistant_msg.id
            })
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Still save user message even if response fails
            db.session.commit()
            return jsonify({'error': f'Failed to generate response: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': f'Chat error: {str(e)}'}), 500

@app.route('/documents')
def get_documents():
    """Get list of uploaded documents for current session."""
    if 'session_id' not in session:
        return jsonify([])
    
    documents = Document.query.filter_by(session_id=session['session_id']).all()
    return jsonify([doc.to_dict() for doc in documents])

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear current session data."""
    try:
        if 'session_id' in session:
            session_id = session['session_id']
            
            # Delete chat messages
            ChatMessage.query.filter_by(session_id=session_id).delete()
            
            # Delete documents and files
            documents = Document.query.filter_by(session_id=session_id).all()
            for doc in documents:
                # Delete file if it exists
                if os.path.exists(doc.file_path):
                    try:
                        os.remove(doc.file_path)
                    except OSError:
                        pass
            
            # Delete document records
            Document.query.filter_by(session_id=session_id).delete()
            db.session.commit()
            
            # Clear session
            session.clear()
        
        return jsonify({'message': 'Session cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({'error': f'Failed to clear session: {str(e)}'}), 500

@app.route('/stats')
def get_stats():
    """Get application statistics."""
    try:
        vector_stats = chat_service.get_vector_store_stats()
        
        session_docs = 0
        if 'session_id' in session:
            session_docs = Document.query.filter_by(session_id=session['session_id']).count()
        
        return jsonify({
            'total_chunks': vector_stats['total_chunks'],
            'total_documents': vector_stats['document_count'],
            'session_documents': session_docs
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

# Import time module for timestamp
import time

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech using OpenAI TTS with language support."""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        voice_id = data.get('voice', 'nova_indian')
        download = data.get('download', False)
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if len(text) > 4096:
            return jsonify({'error': 'Text too long (max 4096 characters)'}), 400
        
        # Get voice configuration from available voices
        available_voices = tts_service.get_available_voices()
        voice_config = next((v for v in available_voices if v['id'] == voice_id), available_voices[1])
        
        actual_voice = voice_config.get('voice', 'nova')
        language = voice_config.get('language', 'indian_english')
        
        # Use expressive speech with language support
        audio_data = tts_service.create_expressive_speech_sync(
            text=text,
            voice=actual_voice,
            emotion="enthusiastic",
            language=language
        )
        
        response = make_response(audio_data)
        response.headers['Content-Type'] = 'audio/mp3'
        
        if download:
            # For download requests
            response.headers['Content-Disposition'] = f'attachment; filename="tts_audio_{voice_id}.mp3"'
        else:
            # For inline playback
            response.headers['Content-Disposition'] = 'inline; filename="speech.mp3"'
        
        return response
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({'error': 'Text-to-speech conversion failed'}), 500

@app.route('/tts/voices', methods=['GET'])
def get_voices():
    """Get available TTS voices with language options."""
    try:
        voices = tts_service.get_available_voices()
        return jsonify(voices)
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({'error': 'Failed to get voices'}), 500
