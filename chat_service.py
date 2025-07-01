import logging
from typing import List, Dict, Tuple
from openai import OpenAI
import os
from vector_store import VectorStore
from web_search import WebSearcher

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.vector_store = VectorStore()
        self.web_searcher = WebSearcher()
        
        # Load existing vector store if available
        try:
            self.vector_store.load("vector_store")
        except:
            pass  # Start with empty store if loading fails
    
    def process_pdf_chunks(self, text_chunks: List[str], document_id: int):
        """Add PDF text chunks to the vector store."""
        try:
            self.vector_store.add_texts(text_chunks, document_id)
            # Save the updated vector store
            self.vector_store.save("vector_store")
            logger.info(f"Processed {len(text_chunks)} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Error processing PDF chunks: {e}")
            raise
    
    def generate_response(self, query: str, session_id: str, ai_role: str = "You are a helpful AI assistant.") -> Tuple[str, List[Dict]]:
        """
        Generate a response combining PDF content and web search results.
        Returns the response text and a list of sources.
        """
        try:
            sources = []
            context_parts = []
            
            # Get active documents for current session only
            from models import Document
            active_docs = Document.query.filter_by(session_id=session_id, is_active=True).all()
            active_doc_ids = {doc.id for doc in active_docs}
            
            # 1. Search PDF content (filtered by session)
            pdf_results = self.vector_store.search(query, k=5)
            
            if pdf_results:
                pdf_context = []
                pdf_doc_ids = set()  # Track unique document IDs
                for text, score, doc_id in pdf_results:
                    # Only include results from current session's active documents
                    if score > 0.1 and doc_id in active_doc_ids:
                        pdf_context.append(text)
                        pdf_doc_ids.add(doc_id)
                
                # Add only one source entry for PDF documents (deduplicated)
                if pdf_context:
                    context_parts.append(f"📘 **From PDF Documents:**\n{' '.join(pdf_context[:3])}")
                    # Add a single PDF source entry
                    sources.append({
                        'type': 'pdf',
                        'content': f"Retrieved from {len(pdf_doc_ids)} PDF document(s)",
                        'document_count': len(pdf_doc_ids)
                    })
                    
                    # Extract images if query suggests visual content is needed or content is found
                    image_keywords = ['image', 'picture', 'chart', 'graph', 'diagram', 'figure', 'photo', 'show me', 'display', 'structure', 'formula', 'equation', 'reaction', 'process', 'cycle', 'model']
                    should_extract_images = any(keyword in query.lower() for keyword in image_keywords)
                    
                    # Extract images when there are relevant text chunks or visual keywords
                    if should_extract_images or len(pdf_results) > 0:
                        logger.info(f"Attempting to extract images for query: {query}")
                        self._extract_relevant_images(pdf_doc_ids, query, sources, pdf_results)
            
            # 2. Search web content
            web_results = self.web_searcher.search_multiple_sources(query, max_results=2)
            if web_results:
                web_context = []
                for result in web_results:
                    web_context.append(f"{result['title']}: {result['snippet']}")
                    sources.append({
                        'type': 'web',
                        'title': result['title'],
                        'snippet': result['snippet'],
                        'url': result['url'],
                        'source': result['source']
                    })
                
                if web_context:
                    context_parts.append(f"🌐 **From Web Search:**\n{' '.join(web_context)}")
            
            # 3. Generate response using OpenAI
            context = "\n\n".join(context_parts) if context_parts else "No specific context found."
            
            # Use role-based system prompt if provided
            if ai_role:
                system_prompt = f"""{ai_role}

When answering questions:
1. Stay true to your assigned role and personality throughout the response
2. Use the provided context from PDF documents and web search
3. Clearly indicate which parts come from PDF documents (📘) vs web search (🌐)
4. If you're a teacher, explain with examples and ask clarifying questions
5. If you're an expert, provide detailed technical insights
6. Maintain your character while being helpful and informative"""
            else:
                system_prompt = """You are a helpful AI assistant that answers questions using information from PDF documents and web search results. 

Instructions:
1. Use the provided context to answer the user's question
2. Clearly indicate which parts of your answer come from PDF documents (📘) vs web search (🌐)
3. If the context doesn't contain relevant information, say so honestly
4. Provide a comprehensive answer that synthesizes information from both sources when available
5. Be concise but informative"""

            user_prompt = f"""Context information:
{context}

User question: {query}

Please provide a helpful answer based on the available context. Use 📘 to indicate information from PDF documents and 🌐 to indicate information from web sources."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            return answer, sources
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}", []
    
    def get_vector_store_stats(self) -> Dict:
        """Get statistics about the vector store."""
        return {
            'total_chunks': len(self.vector_store.texts),
            'document_count': self.vector_store.get_document_count()
        }
    
    def clear_session_data(self, session_id: str):
        """Clear data for a specific session (if needed)."""
        # For now, we keep all data across sessions
        # This could be extended to support session-specific data
        pass
    
    def _extract_relevant_images(self, pdf_doc_ids: set, query: str, sources: list, relevant_chunks: List[Tuple[str, float, int]] = None):
        """Extract images from PDFs based on content relevance and add them to sources."""
        try:
            from models import Document
            from pdf_processor import PDFProcessor
            
            pdf_processor = PDFProcessor()
            
            # Get page numbers from relevant chunks if available
            relevant_pages = set()
            if relevant_chunks:
                for chunk_text, score, doc_id in relevant_chunks:
                    if doc_id in pdf_doc_ids:
                        # Try to extract page information from chunk if available
                        # For now, we'll extract from all pages but this could be enhanced
                        pass
            
            for doc_id in pdf_doc_ids:
                doc = Document.query.get(doc_id)
                if doc and doc.file_path:
                    # Extract images from this PDF with query-based filtering
                    images = pdf_processor.extract_images_from_pdf(doc.file_path, query)
                    
                    if images:
                        # Filter images for relevance and size
                        relevant_images = []
                        for image in images:
                            # Only include images that are large enough to be meaningful
                            width = image.get('width', 0)
                            height = image.get('height', 0)
                            size = image.get('size', 0)
                            
                            # Filter criteria: reasonable size and format
                            if (width >= 100 and height >= 100) or size >= 10000:
                                relevant_images.append(image)
                        
                        # Add relevant images to sources (limit to 3 per document)
                        for i, image in enumerate(relevant_images[:3]):
                            sources.append({
                                'type': 'image',
                                'document': doc.filename,
                                'page': image.get('page', 'Unknown'),
                                'image_data': image.get('base64', ''),
                                'width': image.get('width', 0),
                                'height': image.get('height', 0),
                                'size': image.get('size', 0),
                                'format': image.get('format', 'png')
                            })
                        
                        logger.info(f"Extracted {len(relevant_images)} relevant images from {doc.filename} (filtered from {len(images)} total)")
                        
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            # Don't break the response if image extraction fails
