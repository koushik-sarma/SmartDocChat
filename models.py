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
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_time': self.upload_time.isoformat(),
            'chunk_count': self.chunk_count,
            'file_size': self.file_size
        }

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    message_type = db.Column(db.String(50), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sources = db.Column(db.Text)  # JSON string of sources
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'sources': json.loads(self.sources) if self.sources else []
        }
