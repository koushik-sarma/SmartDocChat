"""
Simplified chat service.
Handles AI chat with clean separation of concerns.
"""

import os
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from app import db
from models import ChatMessage, Document, UserProfile
from .base_service import BaseService
from .document_service import DocumentService
from .simple_similarity import SimpleSimilarity
from vector_store import VectorStore
from web_search import WebSearcher

try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except ImportError:
    openai_client = None

class ChatService(BaseService):
    """Clean service for handling chat operations."""
    
    def __init__(self):
        super().__init__()
        self.document_service = DocumentService()
        self.vector_store = VectorStore()
        self.simple_similarity = SimpleSimilarity()
        self.web_searcher = WebSearcher()
        
        # Load existing vector store if available
        try:
            self.vector_store.load('vector_store.pkl')
        except:
            pass  # Will create new one when needed
    
    def process_chat_message(self, query: str, session_id: str) -> Dict:
        """Process a chat message and return response with sources."""
        try:
            # Get user profile for AI role
            profile = UserProfile.query.filter_by(session_id=session_id).first()
            ai_role = profile.ai_role if profile else "You are a helpful AI assistant."
            
            # Generate response
            response_text, sources = self._generate_response(query, session_id, ai_role)
            
            # Save messages to database
            self._save_chat_messages(query, response_text, sources, session_id, ai_role)
            
            return self.success_response({
                'response': response_text,
                'sources': sources,
                'message_count': self._get_message_count(session_id)
            })
            
        except Exception as e:
            return self.error_response(f"Chat processing failed: {str(e)}")
    
    def _generate_response(self, query: str, session_id: str, ai_role: str) -> Tuple[str, List[Dict]]:
        """Generate AI response combining document content and web search."""
        sources = []
        context_parts = []
        
        # 1. Search document content
        doc_context, doc_sources = self._search_documents(query, session_id)
        if doc_context:
            context_parts.append(f"Document Content:\n{doc_context}")
            sources.extend(doc_sources)
        
        # 2. Web search for additional context
        web_context, web_sources = self._search_web(query)
        if web_context:
            context_parts.append(f"Additional Information:\n{web_context}")
            sources.extend(web_sources)
        
        # 3. Generate AI response
        full_context = "\n\n".join(context_parts) if context_parts else ""
        response = self._generate_ai_response(query, full_context, ai_role)
        
        return response, sources
    
    def _search_documents(self, query: str, session_id: str) -> Tuple[str, List[Dict]]:
        """Search in uploaded documents."""
        try:
            # Get active documents for this session
            active_docs = Document.query.filter_by(session_id=session_id, is_active=True).all()
            if not active_docs:
                return "", []
            
            # Try vector search first
            try:
                results = self.vector_store.search(query, k=5)
                if results:
                    # Filter results to only include documents from this session
                    doc_ids = {doc.id for doc in active_docs}
                    filtered_results = [(text, score, doc_id) for text, score, doc_id in results if doc_id in doc_ids]
                    
                    if filtered_results:
                        # Combine relevant chunks
                        context_texts = [text for text, score, doc_id in filtered_results if score > 0.7]
                        
                        # Create sources list
                        sources = []
                        for doc in active_docs:
                            if any(doc_id == doc.id for _, _, doc_id in filtered_results):
                                sources.append({
                                    'type': 'document',
                                    'title': doc.filename,
                                    'content': f"Uploaded document ({doc.chunk_count} chunks)"
                                })
                        
                        context = "\n\n".join(context_texts) if context_texts else ""
                        return context, sources
            except Exception as vector_error:
                self.logger.warning(f"Vector search failed, using similarity search fallback: {vector_error}")
            
            # Fallback: Use simple similarity search
            try:
                # Build document index for similarity search
                doc_texts = {}
                for doc in active_docs:
                    if os.path.exists(doc.file_path):
                        chunks = list(self.document_service.extract_text_chunks(doc.file_path))
                        doc_texts[doc.id] = ' '.join(chunks)
                
                if doc_texts:
                    # Add documents to similarity index
                    self.simple_similarity.add_documents(doc_texts)
                    
                    # Search for similar content
                    results = self.simple_similarity.search(query, k=5)
                    
                    if results:
                        context_texts = [text for text, score, doc_id in results if score > 0.3]
                        
                        # Create sources list
                        sources = []
                        found_doc_ids = {doc_id for _, _, doc_id in results}
                        for doc in active_docs:
                            if doc.id in found_doc_ids:
                                sources.append({
                                    'type': 'document',
                                    'title': doc.filename,
                                    'content': f"Similarity search in document ({doc.chunk_count} chunks)"
                                })
                        
                        context = "\n\n".join(context_texts) if context_texts else ""
                        return context, sources
                
            except Exception as similarity_error:
                self.logger.warning(f"Similarity search failed: {similarity_error}")
            
            # Final fallback: Basic text search
            context_parts = []
            sources = []
            
            for doc in active_docs:
                try:
                    if os.path.exists(doc.file_path):
                        chunks = list(self.document_service.extract_text_chunks(doc.file_path))
                        full_text = ' '.join(chunks)
                        
                        # Simple keyword matching
                        query_lower = query.lower()
                        if any(keyword in full_text.lower() for keyword in query_lower.split()):
                            # Take first few chunks as context
                            context_parts.extend(chunks[:2])
                            sources.append({
                                'type': 'document',
                                'title': doc.filename,
                                'content': f"Text search in document ({doc.chunk_count} chunks)"
                            })
                except Exception as e:
                    self.logger.warning(f"Error reading document {doc.filename}: {e}")
                    continue
            
            context = "\n\n".join(context_parts) if context_parts else ""
            return context, sources
            
        except Exception as e:
            self.logger.error(f"Document search failed: {e}")
            return "", []
    
    def _search_web(self, query: str) -> Tuple[str, List[Dict]]:
        """Search web for additional information."""
        try:
            search_results = self.web_searcher.search_multiple_sources(query, max_results=3)
            if not search_results:
                return "", []
            
            # Format context
            context_parts = []
            sources = []
            
            for result in search_results:
                context_parts.append(f"Source: {result['title']}\n{result['snippet']}")
                sources.append({
                    'type': 'web',
                    'title': result['title'],
                    'url': result.get('url', ''),
                    'content': result['snippet']
                })
            
            context = "\n\n".join(context_parts)
            return context, sources
            
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return "", []
    
    def _generate_ai_response(self, query: str, context: str, ai_role: str) -> str:
        """Generate response using OpenAI."""
        if not openai_client:
            return "AI service is not available. Please check configuration."
        
        try:
            # Prepare prompt
            system_prompt = ai_role + "\n\nUse the provided context to answer questions accurately. If the context doesn't contain relevant information, provide a helpful general response."
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if context:
                messages.append({
                    "role": "user", 
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                })
            else:
                messages.append({
                    "role": "user", 
                    "content": query
                })
            
            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # Latest model
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"AI response generation failed: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    def _save_chat_messages(self, user_message: str, ai_response: str, sources: List[Dict], session_id: str, ai_role: str):
        """Save chat messages to database."""
        try:
            # Save user message
            user_msg = ChatMessage(
                session_id=session_id,
                message_type='user',
                content=user_message
            )
            
            # Save AI response
            ai_msg = ChatMessage(
                session_id=session_id,
                message_type='assistant',
                content=ai_response,
                sources=json.dumps(sources) if sources else None,
                ai_role_used=ai_role
            )
            
            db.session.add(user_msg)
            db.session.add(ai_msg)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to save chat messages: {e}")
    
    def _get_message_count(self, session_id: str) -> int:
        """Get total message count for session."""
        return ChatMessage.query.filter_by(session_id=session_id).count()
    
    def update_vector_store(self, session_id: str):
        """Update vector store with documents from this session."""
        try:
            active_docs = Document.query.filter_by(session_id=session_id, is_active=True).all()
            
            for doc in active_docs:
                if os.path.exists(doc.file_path):
                    chunks = list(self.document_service.extract_text_chunks(doc.file_path))
                    if chunks:
                        self.vector_store.add_texts(chunks, doc.id)
            
            # Save updated vector store
            self.vector_store.save('vector_store.pkl')
            
        except Exception as e:
            if "insufficient_quota" in str(e) or "429" in str(e):
                self.logger.warning("OpenAI embeddings quota exceeded - continuing without vector search")
            else:
                self.logger.error(f"Vector store update failed: {e}")
            # Don't raise error - continue without vector search
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for session."""
        try:
            messages = (ChatMessage.query
                       .filter_by(session_id=session_id)
                       .order_by(ChatMessage.timestamp.desc())
                       .limit(limit)
                       .all())
            
            return [msg.to_dict() for msg in reversed(messages)]
            
        except Exception as e:
            self.logger.error(f"Failed to get chat history: {e}")
            return []
    
    def regenerate_last_response(self, session_id: str) -> Dict:
        """Regenerate the last AI response with current AI role."""
        try:
            # Get last user message
            last_user_msg = (ChatMessage.query
                            .filter_by(session_id=session_id, message_type='user')
                            .order_by(ChatMessage.timestamp.desc())
                            .first())
            
            if not last_user_msg:
                return self.error_response("No previous message to regenerate")
            
            # Delete last AI response if exists
            last_ai_msg = (ChatMessage.query
                          .filter_by(session_id=session_id, message_type='assistant')
                          .order_by(ChatMessage.timestamp.desc())
                          .first())
            
            if last_ai_msg and last_ai_msg.timestamp > last_user_msg.timestamp:
                db.session.delete(last_ai_msg)
                db.session.commit()
            
            # Generate new response
            return self.process_chat_message(last_user_msg.content, session_id)
            
        except Exception as e:
            return self.error_response(f"Failed to regenerate response: {str(e)}")