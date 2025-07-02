"""
Simple text similarity without requiring external APIs.
Basic but effective for document search.
"""

import re
import math
from typing import List, Tuple, Dict
from collections import Counter

class SimpleSimilarity:
    """Basic text similarity using TF-IDF and cosine similarity."""
    
    def __init__(self):
        self.documents = {}  # doc_id -> processed text
        self.vocabulary = set()
        self.idf_scores = {}
    
    def add_documents(self, doc_texts: Dict[int, str]):
        """Add documents to the similarity index."""
        self.documents.update(doc_texts)
        self._build_vocabulary()
        self._calculate_idf()
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, int]]:
        """Search for similar documents."""
        if not self.documents:
            return []
        
        query_vector = self._vectorize_text(query)
        results = []
        
        for doc_id, doc_text in self.documents.items():
            doc_vector = self._vectorize_text(doc_text)
            similarity = self._cosine_similarity(query_vector, doc_vector)
            
            if similarity > 0.1:  # Minimum threshold
                # Return snippet around best match
                snippet = self._extract_snippet(doc_text, query)
                results.append((snippet, similarity, doc_id))
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def _build_vocabulary(self):
        """Build vocabulary from all documents."""
        for doc_text in self.documents.values():
            words = self._tokenize(doc_text)
            self.vocabulary.update(words)
    
    def _calculate_idf(self):
        """Calculate IDF scores for vocabulary."""
        total_docs = len(self.documents)
        
        for word in self.vocabulary:
            doc_count = sum(1 for doc_text in self.documents.values() 
                          if word in self._tokenize(doc_text))
            
            if doc_count > 0:
                self.idf_scores[word] = math.log(total_docs / doc_count)
            else:
                self.idf_scores[word] = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Convert to lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may',
            'might', 'must', 'shall', 'a', 'an', 'this', 'that', 'these', 'those'
        }
        
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _vectorize_text(self, text: str) -> Dict[str, float]:
        """Convert text to TF-IDF vector."""
        words = self._tokenize(text)
        word_counts = Counter(words)
        total_words = len(words)
        
        vector = {}
        for word in self.vocabulary:
            tf = word_counts.get(word, 0) / total_words if total_words > 0 else 0
            idf = self.idf_scores.get(word, 0)
            vector[word] = tf * idf
        
        return vector
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(vec1.get(word, 0) * vec2.get(word, 0) for word in vec1.keys())
        
        norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def _extract_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """Extract relevant snippet from text based on query."""
        query_words = set(self._tokenize(query))
        sentences = re.split(r'[.!?]+', text)
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence_words = set(self._tokenize(sentence))
            score = len(query_words.intersection(sentence_words))
            
            if score > best_score and len(sentence.strip()) > 20:
                best_score = score
                best_sentence = sentence.strip()
        
        if best_sentence:
            # Truncate if too long
            if len(best_sentence) > max_length:
                best_sentence = best_sentence[:max_length] + "..."
            return best_sentence
        
        # Fallback: return first part of text
        return text[:max_length] + "..." if len(text) > max_length else text