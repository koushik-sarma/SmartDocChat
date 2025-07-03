"""
Refactored routes using clean service layer architecture.
All business logic moved to services, routes only handle HTTP concerns.
"""

import os
import logging
from flask import render_template, request, jsonify, session

from app import app
from services import DocumentService, ChatService, SessionService, ComparisonService
from tts_service import TTSService

# Initialize services
document_service = DocumentService()
chat_service = ChatService()
session_service = SessionService()
comparison_service = ComparisonService()
tts_service = TTSService()

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main chat interface."""
    session_id = session_service.get_or_create_session_id(request)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle document upload."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        result = document_service.upload_document(file, session_id)
        
        if result['success']:
            # Update vector store with new document
            chat_service.update_vector_store(session_id)
            
            # Ensure proper response format for frontend
            response_data = {
                'success': True,
                'data': result.get('data', {}),
                'message': result.get('data', {}).get('message', 'Upload successful'),
                'document': {
                    'id': result.get('data', {}).get('document_id'),
                    'filename': result.get('data', {}).get('filename'),
                    'chunk_count': result.get('data', {}).get('chunk_count', 0),
                    'file_size': result.get('data', {}).get('file_size', 0),
                    'is_active': True
                }
            }
            return jsonify(response_data), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        result = chat_service.process_chat_message(data['message'], session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'success': False, 'error': 'Chat processing failed'}), 500

@app.route('/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents for current session."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        documents = document_service.get_session_documents(session_id)
        
        return jsonify([doc.to_dict() for doc in documents]), 200
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return jsonify({'error': 'Failed to retrieve documents'}), 500

@app.route('/documents/<int:doc_id>/toggle', methods=['POST'])
def toggle_document(doc_id):
    """Toggle document inclusion in context."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        result = document_service.toggle_document_status(doc_id, session_id)
        
        if result['success']:
            # Update vector store after status change
            chat_service.update_vector_store(session_id)
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Toggle document error: {e}")
        return jsonify({'success': False, 'error': 'Failed to toggle document'}), 500

@app.route('/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a specific document."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        result = document_service.delete_document(doc_id, session_id)
        
        if result['success']:
            # Update vector store after deletion
            chat_service.update_vector_store(session_id)
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete document'}), 500



@app.route('/profile', methods=['GET', 'POST'])
def user_profile():
    """Manage user profile settings."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        
        if request.method == 'GET':
            profile = session_service.get_user_profile(session_id)
            if profile:
                return jsonify({'success': True, 'profile': profile.to_dict()}), 200
            else:
                # Return defaults
                return jsonify({
                    'success': True, 
                    'profile': {
                        'ai_role': 'You are a helpful AI assistant.',
                        'theme_preference': 'dark',
                        'voice_enabled': False
                    }
                }), 200
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            result = session_service.update_user_profile(session_id, data)
            
            return jsonify(result), 200 if result['success'] else 400
            
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'success': False, 'error': 'Profile operation failed'}), 500

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear current session data."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        result = session_service.clear_session_data(session_id, 'all')
        
        # Clear vector store
        chat_service.vector_store.clear()
        chat_service.vector_store.save('vector_store.pkl')
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Clear session error: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear session'}), 500

@app.route('/clear-chat', methods=['POST'])
def clear_chat():
    """Clear chat messages only, keep documents."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        result = session_service.clear_session_data(session_id, 'chat')
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Clear chat error: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear chat'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get application statistics."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        stats = session_service.get_session_stats(session_id)
        
        return jsonify({'success': True, 'stats': stats}), 200
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech using OpenAI TTS."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        text = data['text']
        voice = data.get('voice', 'alloy')
        emotion = data.get('emotion', 'neutral')
        language = data.get('language', 'english')
        
        # Generate speech
        audio_data = tts_service.create_expressive_speech(text, voice, emotion, language)
        
        # Save to temporary file and return path
        filename = tts_service.save_audio_to_file(audio_data)
        
        return jsonify({
            'success': True,
            'audio_file': filename,
            'message': 'Audio generated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({'success': False, 'error': f'TTS failed: {str(e)}'}), 500

@app.route('/voices', methods=['GET'])
def get_voices():
    """Get available TTS voices."""
    try:
        voices = tts_service.get_available_voices()
        return jsonify({'success': True, 'voices': voices}), 200
        
    except Exception as e:
        logger.error(f"Get voices error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get voices'}), 500

@app.route('/regenerate-response', methods=['POST'])
def regenerate_response():
    """Regenerate the last AI response with current settings."""
    try:
        session_id = session_service.get_or_create_session_id(request)
        result = chat_service.regenerate_last_response(session_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Regenerate response error: {e}")
        return jsonify({'success': False, 'error': 'Failed to regenerate response'}), 500

# Serve audio files
@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files."""
    try:
        import tempfile
        from flask import send_file
        
        file_path = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'Audio file not found'}), 404
            
    except Exception as e:
        logger.error(f"Serve audio error: {e}")
        return jsonify({'error': 'Failed to serve audio'}), 500