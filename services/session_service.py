"""
Session management service.
Handles user sessions, profiles, and session-specific data.
"""

import os
import uuid
from typing import Dict, Optional
from datetime import datetime

from app import db
from models import UserProfile, Document, ChatMessage
from .base_service import BaseService

class SessionService(BaseService):
    """Service for managing user sessions and profiles."""
    
    def __init__(self):
        super().__init__()
    
    def get_or_create_session_id(self, request) -> str:
        """Get existing session ID or create new one."""
        from flask import session
        
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        return session['session_id']
    
    def get_user_profile(self, session_id: str) -> Optional[UserProfile]:
        """Get user profile for session."""
        return UserProfile.query.filter_by(session_id=session_id).first()
    
    def create_user_profile(self, session_id: str, **kwargs) -> UserProfile:
        """Create new user profile."""
        profile = UserProfile(
            session_id=session_id,
            ai_role=kwargs.get('ai_role', "You are a helpful AI assistant."),
            theme_preference=kwargs.get('theme', 'dark'),
            voice_enabled=kwargs.get('voice_enabled', False)
        )
        
        db.session.add(profile)
        db.session.commit()
        return profile
    
    def update_user_profile(self, session_id: str, updates: Dict) -> Dict:
        """Update user profile settings."""
        try:
            profile = self.get_user_profile(session_id)
            
            if not profile:
                profile = self.create_user_profile(session_id, **updates)
            else:
                # Update allowed fields
                if 'ai_role' in updates:
                    profile.ai_role = updates['ai_role']
                if 'theme_preference' in updates:
                    profile.theme_preference = updates['theme_preference']
                if 'voice_enabled' in updates:
                    profile.voice_enabled = updates['voice_enabled']
                
                profile.updated_at = datetime.utcnow()
                db.session.commit()
            
            return self.success_response({
                'profile': profile.to_dict(),
                'message': 'Profile updated successfully'
            })
            
        except Exception as e:
            return self.error_response(f"Failed to update profile: {str(e)}")
    
    def clear_session_data(self, session_id: str, data_type: str = 'all') -> Dict:
        """Clear session data based on type."""
        try:
            if data_type in ['all', 'documents']:
                # Delete document files
                documents = Document.query.filter_by(session_id=session_id).all()
                for doc in documents:
                    if doc.file_path and os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                
                # Delete document records
                Document.query.filter_by(session_id=session_id).delete()
            
            if data_type in ['all', 'chat']:
                # Delete chat messages
                ChatMessage.query.filter_by(session_id=session_id).delete()
            
            if data_type == 'all':
                # Delete user profile (but recreate with defaults)
                UserProfile.query.filter_by(session_id=session_id).delete()
            
            db.session.commit()
            
            return self.success_response({
                'message': f'Session {data_type} data cleared successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return self.error_response(f"Failed to clear session data: {str(e)}")
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get comprehensive session statistics."""
        try:
            # Document stats
            documents = Document.query.filter_by(session_id=session_id).all()
            active_docs = [d for d in documents if d.is_active]
            
            # Chat stats
            messages = ChatMessage.query.filter_by(session_id=session_id).all()
            user_messages = [m for m in messages if m.message_type == 'user']
            assistant_messages = [m for m in messages if m.message_type == 'assistant']
            
            # Calculate totals
            total_chunks = sum(doc.chunk_count for doc in active_docs)
            total_file_size = sum(doc.file_size for doc in documents)
            
            return {
                'documents': {
                    'total': len(documents),
                    'active': len(active_docs),
                    'total_chunks': total_chunks,
                    'total_size_mb': round(total_file_size / (1024 * 1024), 2)
                },
                'chat': {
                    'total_messages': len(messages),
                    'user_messages': len(user_messages),
                    'assistant_messages': len(assistant_messages)
                },
                'session_id': session_id[:8] + '...'  # Partial ID for privacy
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session stats: {e}")
            return {
                'documents': {'total': 0, 'active': 0, 'total_chunks': 0, 'total_size_mb': 0},
                'chat': {'total_messages': 0, 'user_messages': 0, 'assistant_messages': 0},
                'session_id': session_id[:8] + '...'
            }