import faiss
import numpy as np
from typing import List, Tuple
import pickle
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 1536):  # OpenAI embedding dimension
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.texts = []
        self.document_ids = []
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def add_texts(self, texts: List[str], document_id: int):
        """Add text chunks to the vector store with embeddings."""
        try:
            # Get embeddings for all texts
            embeddings = self._get_embeddings(texts)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Store metadata
            self.texts.extend(texts)
            self.document_ids.extend([document_id] * len(texts))
            
            logger.info(f"Added {len(texts)} text chunks for document {document_id}")
            
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
                if idx < len(self.texts):
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
        """Get embeddings from OpenAI API."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            embeddings = np.array([item.embedding for item in response.data])
            return embeddings
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
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
