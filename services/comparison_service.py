"""
Document comparison service.
Handles comparison of multiple documents with intelligent analysis.
"""

import os
from typing import List, Dict, Set
from collections import Counter

from models import Document
from .base_service import BaseService
from .document_service import DocumentService

class ComparisonService(BaseService):
    """Service for comparing documents and finding similarities/differences."""
    
    def __init__(self):
        super().__init__()
        self.document_service = DocumentService()
    
    def compare_session_documents(self, session_id: str) -> Dict:
        """Compare all active documents in a session."""
        try:
            documents = Document.query.filter_by(session_id=session_id, is_active=True).all()
            
            if len(documents) < 2:
                return self.error_response(
                    f"Need at least 2 active documents to compare. Found {len(documents)} document(s)."
                )
            
            doc_paths = [doc.file_path for doc in documents]
            comparison = self._analyze_documents(doc_paths)
            
            return self.success_response({
                'comparison': comparison,
                'documents_compared': [doc.to_dict() for doc in documents]
            })
            
        except Exception as e:
            return self.error_response(f"Document comparison failed: {str(e)}")
    
    def _analyze_documents(self, doc_paths: List[str]) -> Dict:
        """Analyze documents and return structured comparison."""
        try:
            doc_contents = {}
            doc_word_sets = {}
            
            # Extract content from each document
            for doc_path in doc_paths:
                if not os.path.exists(doc_path):
                    continue
                    
                filename = os.path.basename(doc_path)
                chunks = list(self.document_service.extract_text_chunks(doc_path))
                full_text = ' '.join(chunks)
                
                doc_contents[filename] = full_text
                
                # Create word set for comparison (filter short words)
                words = [word.lower().strip('.,!?;:"()[]{}') 
                        for word in full_text.split() 
                        if len(word) > 3 and word.isalpha()]
                doc_word_sets[filename] = set(words)
            
            if not doc_contents:
                return {'error': 'No valid documents found for comparison'}
            
            # Perform analysis
            return {
                'documents': list(doc_contents.keys()),
                'word_counts': {name: len(content.split()) for name, content in doc_contents.items()},
                'common_themes': self._find_common_themes(doc_word_sets),
                'unique_content': self._find_unique_content(doc_word_sets),
                'similarity_scores': self._calculate_similarity_scores(doc_word_sets),
                'content_overlap': self._analyze_content_overlap(doc_word_sets)
            }
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _find_common_themes(self, doc_word_sets: Dict[str, Set[str]]) -> List[str]:
        """Find words common across all documents."""
        if not doc_word_sets:
            return []
        
        # Find intersection of all word sets
        common_words = set.intersection(*doc_word_sets.values()) if doc_word_sets else set()
        
        # Remove very common words (basic filtering)
        stop_words = {
            'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but',
            'his', 'from', 'they', 'she', 'her', 'been', 'than', 'its', 'were', 'said'
        }
        
        filtered_words = [word for word in common_words if word not in stop_words]
        
        # Return top 20 most meaningful common themes
        return sorted(filtered_words)[:20]
    
    def _find_unique_content(self, doc_word_sets: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """Find unique words in each document."""
        unique_content = {}
        
        for doc_name, word_set in doc_word_sets.items():
            # Find words unique to this document
            other_words = set()
            for other_doc, other_words_set in doc_word_sets.items():
                if other_doc != doc_name:
                    other_words.update(other_words_set)
            
            unique_words = word_set - other_words
            
            # Return top 15 unique words, sorted
            unique_content[doc_name] = sorted(unique_words)[:15]
        
        return unique_content
    
    def _calculate_similarity_scores(self, doc_word_sets: Dict[str, Set[str]]) -> Dict[str, float]:
        """Calculate pairwise similarity scores between documents."""
        similarity_scores = {}
        doc_names = list(doc_word_sets.keys())
        
        for i, doc1 in enumerate(doc_names):
            for j, doc2 in enumerate(doc_names[i+1:], i+1):
                # Jaccard similarity
                intersection = len(doc_word_sets[doc1] & doc_word_sets[doc2])
                union = len(doc_word_sets[doc1] | doc_word_sets[doc2])
                
                similarity = intersection / union if union > 0 else 0
                pair_key = f"{doc1} vs {doc2}"
                similarity_scores[pair_key] = round(similarity * 100, 1)  # Percentage
        
        return similarity_scores
    
    def _analyze_content_overlap(self, doc_word_sets: Dict[str, Set[str]]) -> Dict:
        """Analyze content overlap statistics."""
        if len(doc_word_sets) < 2:
            return {}
        
        all_words = set()
        for word_set in doc_word_sets.values():
            all_words.update(word_set)
        
        total_unique_words = len(all_words)
        
        # Find words that appear in multiple documents
        word_frequency = Counter()
        for word_set in doc_word_sets.values():
            for word in word_set:
                word_frequency[word] += 1
        
        shared_words = {word: count for word, count in word_frequency.items() if count > 1}
        
        return {
            'total_unique_words': total_unique_words,
            'shared_words_count': len(shared_words),
            'overlap_percentage': round((len(shared_words) / total_unique_words) * 100, 1) if total_unique_words > 0 else 0,
            'most_common_shared': [word for word, count in Counter(shared_words).most_common(10)]
        }