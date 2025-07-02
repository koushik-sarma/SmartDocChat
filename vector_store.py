import faiss
import numpy as np
from typing import List, Tuple
import pickle
import os
import logging
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class QuotaExceededException(Exception):
    """Custom exception for API quota exceeded."""
    pass

class VectorStore:
    def __init__(self, dimension: int = 768):  # Google text-embedding dimension
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.texts = []
        self.document_ids = []
        if genai:
            self.genai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        else:
            self.genai_client = None
    
    def add_texts(self, texts: List[str], document_id: int):
        """Add text chunks to the vector store with embeddings."""
        try:
            # Process in batches for efficient embedding generation
            batch_size = 50  # Process 50 chunks at a time
            total_added = 0
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Get embeddings for batch
                embeddings = self._get_embeddings(batch)
                
                # Normalize embeddings for cosine similarity
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                
                # Add to FAISS index
                self.index.add(embeddings.astype('float32'))
                
                # Store metadata
                self.texts.extend(batch)
                self.document_ids.extend([document_id] * len(batch))
                
                total_added += len(batch)
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} chunks")
            
            logger.info(f"Added {total_added} text chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, int]]:
        """Search for similar text chunks."""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Get query embedding
            query_embedding = self._get_embeddings([query])[0]
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Search
            scores, indices = self.index.search(
                query_embedding.reshape(1, -1).astype('float32'), k
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.texts):  # Check for valid index
                    results.append((
                        self.texts[idx],
                        float(score),
                        self.document_ids[idx]
                    ))
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings from Google Gemini API."""
        try:
            if not self.genai_client:
                logger.warning("Gemini client not available - generating dummy embeddings")
                # Return dummy embeddings of correct dimension
                return np.random.rand(len(texts), self.dimension).astype('float32')
            
            embeddings = []
            for text in texts:
                response = self.genai_client.models.embed_content(
                    model="models/text-embedding-004",
                    contents=text
                )
                # Google Gemini response structure: result.embeddings 
                # Handle ContentEmbedding objects properly
                if hasattr(response.embeddings, 'values'):
                    # ContentEmbedding object with values attribute
                    vector_values = list(response.embeddings.values)
                    embeddings.append(vector_values)
                    logger.info(f"Successfully extracted ContentEmbedding vector of length {len(vector_values)}")
                elif isinstance(response.embeddings, list) and len(response.embeddings) > 0:
                    # List of ContentEmbedding objects or raw values
                    first_item = response.embeddings[0]
                    if hasattr(first_item, 'values'):
                        # List of ContentEmbedding objects
                        vector_values = list(first_item.values)
                        embeddings.append(vector_values)
                        logger.info(f"Successfully extracted from ContentEmbedding list, length {len(vector_values)}")
                    else:
                        # Direct list of values
                        embeddings.append(response.embeddings)
                        logger.info(f"Successfully extracted direct list, length {len(response.embeddings)}")
                else:
                    logger.error(f"Unexpected embedding structure: {type(response.embeddings)}")
                    logger.error(f"Has values attr: {hasattr(response.embeddings, 'values')}")
                    embeddings.append(np.random.rand(self.dimension).tolist())
            
            return np.array(embeddings)
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.warning("Google Gemini quota exceeded - using dummy embeddings")
                return np.random.rand(len(texts), self.dimension).astype('float32')
            logger.error(f"Error getting embeddings: {e}")
            # Fallback to dummy embeddings
            return np.random.rand(len(texts), self.dimension).astype('float32')
    
    def save(self, filepath: str):
        """Save the vector store to disk."""
        try:
            data = {
                'texts': self.texts,
                'document_ids': self.document_ids
            }
            
            # Save FAISS index
            faiss.write_index(self.index, f"{filepath}.faiss")
            
            # Save metadata
            with open(f"{filepath}.pkl", 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def load(self, filepath: str):
        """Load the vector store from disk."""
        try:
            # Load FAISS index
            if os.path.exists(f"{filepath}.faiss"):
                self.index = faiss.read_index(f"{filepath}.faiss")
            
            # Load metadata
            if os.path.exists(f"{filepath}.pkl"):
                with open(f"{filepath}.pkl", 'rb') as f:
                    data = pickle.load(f)
                    self.texts = data['texts']
                    self.document_ids = data['document_ids']
                    
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
    
    def get_document_count(self) -> int:
        """Get number of unique documents in the store."""
        return len(set(self.document_ids)) if self.document_ids else 0
    
    def clear(self):
        """Clear all data from the vector store."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.texts = []
        self.document_ids = []
