"""
Simplified chat service.
Handles AI chat with clean separation of concerns.
Includes retry logic with exponential backoff and automatic fallback between AI providers.
"""

import os
import json
import time
import random
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from app import db
from models import ChatMessage, Document, UserProfile
from .base_service import BaseService
from .document_service import DocumentService
from .simple_similarity import SimpleSimilarity
from vector_store import VectorStore
from web_search import WebSearcher

# Initialize both AI clients for fallback support
gemini_client = None
openai_client = None
ai_provider = None

try:
    from google import genai
    gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    ai_provider = "gemini"
    print("Using Google Gemini as primary AI provider")
except Exception as e:
    print(f"Gemini client initialization failed: {e}")

try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if ai_provider is None:
        ai_provider = "openai"
        print("Using OpenAI as primary AI provider")
    else:
        print("OpenAI available as fallback AI provider")
except Exception as e:
    print(f"OpenAI client initialization failed: {e}")

if ai_provider is None:
    print("WARNING: No AI provider available!")

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
            
            # Rebuild vector store with only session documents to ensure isolation
            self._rebuild_vector_store_for_session(session_id)
            
            # Try vector search first
            try:
                results = self.vector_store.search(query, k=5)
                if results:
                    # Since we rebuilt the vector store with only session docs, all results are valid
                    # Combine relevant chunks (lowered threshold for FAISS cosine similarity)
                    context_texts = [text for text, score, doc_id in results if score > 0.3]
                    
                    # Create sources list
                    sources = []
                    for doc in active_docs:
                        if any(doc_id == doc.id for _, _, doc_id in results):
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
        """Generate response using available AI provider with retry and fallback."""
        global ai_provider, gemini_client, openai_client
        
        # Try primary provider first with retries
        if ai_provider == "gemini" and gemini_client:
            response = self._try_with_retry(
                lambda: self._generate_gemini_response(query, context, ai_role),
                provider_name="Gemini"
            )
            if response:
                return response
            
            # Fallback to OpenAI if Gemini fails
            if openai_client:
                self.logger.info("Falling back to OpenAI after Gemini failure")
                response = self._try_with_retry(
                    lambda: self._generate_openai_response(query, context, ai_role),
                    provider_name="OpenAI"
                )
                if response:
                    return response
        
        elif ai_provider == "openai" and openai_client:
            response = self._try_with_retry(
                lambda: self._generate_openai_response(query, context, ai_role),
                provider_name="OpenAI"
            )
            if response:
                return response
            
            # Fallback to Gemini if OpenAI fails
            if gemini_client:
                self.logger.info("Falling back to Gemini after OpenAI failure")
                response = self._try_with_retry(
                    lambda: self._generate_gemini_response(query, context, ai_role),
                    provider_name="Gemini"
                )
                if response:
                    return response
        
        return "I'm having trouble connecting to AI services right now. Please try again in a few moments."
    
    def _is_retryable_error(self, error) -> bool:
        """Check if an error is retryable (503, rate limit, overloaded, etc.)."""
        error_str = str(error).lower()
        retryable_patterns = [
            '503', 'overloaded', 'rate', 'quota', 'unavailable',
            'resource_exhausted', 'too many requests', 'try again',
            'temporarily unavailable', 'service unavailable', 'busy'
        ]
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def _try_with_retry(self, func, provider_name: str, max_retries: int = 3, base_delay: float = 1.0) -> Optional[str]:
        """
        Execute function with exponential backoff retry logic.
        Returns None if all retries fail (signals need to try fallback).
        Returns string response on success.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = func()
                # Any non-empty result from the AI is a success
                if result:
                    return result
                # Empty response - retry
                last_error = "Empty response"
                self.logger.warning(f"{provider_name} attempt {attempt + 1}/{max_retries} returned empty response")
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"{provider_name} attempt {attempt + 1}/{max_retries} failed: {e}")
                
                # Check if error is NOT retryable (authentication, invalid key, etc.)
                non_retryable_patterns = ['invalid_api_key', 'authentication', 'permission', 'unauthorized', '401', '403']
                if any(pattern in str(e).lower() for pattern in non_retryable_patterns):
                    self.logger.error(f"{provider_name} non-retryable error: {e}")
                    return None
            
            # Calculate delay with exponential backoff and jitter before next attempt
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                self.logger.info(f"Retrying {provider_name} in {delay:.2f} seconds...")
                time.sleep(delay)
        
        self.logger.error(f"{provider_name} failed after {max_retries} retries. Last error: {last_error}")
        return None
    
    def _generate_gemini_response(self, query: str, context: str, ai_role: str) -> str:
        """Generate response using Google Gemini."""
        # Prepare prompt
        system_prompt = ai_role + "\n\nUse the provided context to answer questions accurately. If the context doesn't contain relevant information, provide a helpful general response."
        
        if context:
            prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {query}"
        else:
            prompt = f"{system_prompt}\n\nQuestion: {query}"
        
        # Call Gemini API - let exceptions propagate for retry logic
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        response_text = response.text
        return response_text if response_text else "I apologize, but I couldn't generate a proper response."
    
    def _generate_openai_response(self, query: str, context: str, ai_role: str) -> str:
        """Generate response using OpenAI."""
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
        
        # Call OpenAI API - let exceptions propagate for retry logic
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Latest model
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        response_content = response.choices[0].message.content
        return response_content if response_content is not None else "I apologize, but I couldn't generate a proper response."
    
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
    
    def _rebuild_vector_store_for_session(self, session_id: str):
        """Rebuild vector store with only documents from current session."""
        try:
            # Clear existing vector store
            self.vector_store.clear()
            
            # Get active documents for this session only
            active_docs = Document.query.filter_by(session_id=session_id, is_active=True).all()
            
            if not active_docs:
                return
            
            # Add documents to vector store
            for doc in active_docs:
                if os.path.exists(doc.file_path):
                    try:
                        chunks = list(self.document_service.extract_text_chunks(doc.file_path))
                        if chunks:
                            self.vector_store.add_texts(chunks, doc.id)
                    except Exception as e:
                        self.logger.warning(f"Failed to add document {doc.filename} to vector store: {e}")
                        
        except Exception as e:
            self.logger.error(f"Failed to rebuild vector store for session: {e}")