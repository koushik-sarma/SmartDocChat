from app import db
from datetime import datetime
import json

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    chunk_count = db.Column(db.Integer, default=0)
    file_size = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_time': self.upload_time.isoformat(),
            'chunk_count': self.chunk_count,
            'file_size': self.file_size,
            'is_active': getattr(self, 'is_active', True)
        }

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False, unique=True)
    ai_role = db.Column(db.Text, default="You are a helpful AI assistant.")
    theme_preference = db.Column(db.String(50), default="dark")  # 'dark' or 'light'
    voice_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ai_role': self.ai_role,
            'theme_preference': self.theme_preference,
            'voice_enabled': self.voice_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    message_type = db.Column(db.String(50), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sources = db.Column(db.Text)  # JSON string of sources
    ai_role_used = db.Column(db.Text)  # Store the AI role used for this response
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'sources': json.loads(self.sources) if self.sources else []
        }
