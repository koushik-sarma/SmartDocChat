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
    
    def generate_response(self, query: str, session_id: str) -> Tuple[str, List[Dict]]:
        """
        Generate a response combining PDF content and web search results.
        Returns the response text and a list of sources.
        """
        try:
            sources = []
            context_parts = []
            
            # 1. Search PDF content
            pdf_results = self.vector_store.search(query, k=5)
            
            if pdf_results:
                pdf_context = []
                for text, score, doc_id in pdf_results:
                    if score > 0.1:  # Lower relevance threshold for better results
                        pdf_context.append(text)
                        sources.append({
                            'type': 'pdf',
                            'content': text[:200] + '...' if len(text) > 200 else text,
                            'score': score,
                            'document_id': doc_id
                        })
                
                if pdf_context:
                    context_parts.append(f"📘 **From PDF Documents:**\n{' '.join(pdf_context[:3])}")
            
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
