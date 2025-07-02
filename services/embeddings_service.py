"""
Alternative embeddings service using free/low-cost providers.
Fallback options when OpenAI quota is exceeded.
"""

import numpy as np
import logging
from typing import List, Optional
import requests

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service to handle embeddings with multiple providers."""
    
    def __init__(self):
        self.providers = [
            self._openai_embeddings,
            self._sentence_transformers_embeddings,
            self._huggingface_embeddings
        ]
    
    def get_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Get embeddings using the first available provider."""
        for provider in self.providers:
            try:
                embeddings = provider(texts)
                if embeddings is not None:
                    logger.info(f"Successfully got embeddings using {provider.__name__}")
                    return embeddings
            except Exception as e:
                logger.warning(f"Provider {provider.__name__} failed: {e}")
                continue
        
        logger.error("All embedding providers failed")
        return None
    
    def _openai_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """OpenAI embeddings (original method)."""
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            embeddings = np.array([embedding.embedding for embedding in response.data])
            return embeddings
            
        except Exception as e:
            if "insufficient_quota" in str(e) or "429" in str(e):
                raise Exception("OpenAI quota exceeded")
            raise e
    
    def _sentence_transformers_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Local sentence transformers (no API required)."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight model that runs locally
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            return np.array(embeddings)
            
        except ImportError:
            logger.info("sentence-transformers not installed")
            raise Exception("sentence-transformers not available")
        except Exception as e:
            raise e
    
    def _huggingface_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Free Hugging Face Inference API."""
        try:
            import os
            
            # This uses the free Hugging Face Inference API
            api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
            headers = {"Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY', '')}"}
            
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": texts, "options": {"wait_for_model": True}},
                timeout=30
            )
            
            if response.status_code == 200:
                embeddings = np.array(response.json())
                if len(embeddings.shape) == 3:  # Sometimes returns extra dimension
                    embeddings = embeddings.mean(axis=1)
                return embeddings
            else:
                raise Exception(f"HuggingFace API error: {response.status_code}")
                
        except Exception as e:
            raise e