import pdfplumber
import logging
from typing import List, Generator
import os

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def extract_text_chunks(self, pdf_path: str) -> Generator[str, None, None]:
        """
        Extract text from PDF in chunks to handle large files efficiently.
        Uses streaming approach to avoid loading entire file into memory.
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_chunk = ""
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Clean the text
                            page_text = self._clean_text(page_text)
                            current_chunk += f" {page_text}"
                            
                            # Split into chunks when we exceed chunk_size
                            while len(current_chunk.split()) > self.chunk_size:
                                chunk_words = current_chunk.split()
                                chunk = " ".join(chunk_words[:self.chunk_size])
                                yield chunk
                                current_chunk = " ".join(chunk_words[self.chunk_size:])
                    
                    except Exception as e:
                        logger.warning(f"Error processing page {page_num}: {e}")
                        continue
                
                # Yield remaining text as final chunk
                if current_chunk.strip():
                    yield current_chunk.strip()
                    
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace and formatting."""
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """Get basic information about the PDF."""
        try:
            file_size = os.path.getsize(pdf_path)
            
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                
                # Try to get metadata
                metadata = pdf.metadata or {}
                
                return {
                    'file_size': file_size,
                    'page_count': page_count,
                    'title': metadata.get('Title', ''),
                    'author': metadata.get('Author', ''),
                    'subject': metadata.get('Subject', '')
                }
        except Exception as e:
            logger.error(f"Error getting PDF info for {pdf_path}: {e}")
            return {'file_size': os.path.getsize(pdf_path), 'page_count': 0}
