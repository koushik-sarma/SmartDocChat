import pdfplumber
import fitz  # PyMuPDF
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
        Uses PyMuPDF as primary method with pdfplumber fallback.
        """
        # First, check if file exists and is readable
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            raise ValueError("PDF file is empty")
        
        # Try PyMuPDF first (more reliable)
        try:
            yield from self._extract_with_pymupdf(pdf_path)
            return
        except Exception as e:
            logger.warning(f"PyMuPDF failed for {pdf_path}, trying pdfplumber fallback")
        
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("PDF file contains no pages")
                
                current_chunk = ""
                processed_pages = 0
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        processed_pages += 1
                        
                        if page_text:
                            page_text = self._clean_text(page_text)
                            current_chunk += f" {page_text}"
                            
                            while len(current_chunk.split()) > self.chunk_size:
                                chunk_words = current_chunk.split()
                                chunk = " ".join(chunk_words[:self.chunk_size])
                                if chunk.strip():
                                    yield chunk
                                current_chunk = " ".join(chunk_words[self.chunk_size:])
                    
                    except Exception as e:
                        logger.warning(f"Error processing page {page_num + 1}: {e}")
                        continue
                
                if current_chunk.strip():
                    yield current_chunk.strip()
                
                if processed_pages == 0:
                    raise ValueError("No pages could be processed from the PDF")
                    
        except Exception as e:
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def _extract_with_pymupdf(self, pdf_path: str) -> Generator[str, None, None]:
        """Fallback PDF extraction using PyMuPDF."""
        try:
            logger.info(f"Using PyMuPDF for {pdf_path}")
            doc = fitz.open(pdf_path)
            
            if doc.page_count == 0:
                doc.close()
                raise ValueError("PDF file contains no pages")
            
            current_chunk = ""
            processed_pages = 0
            
            for page_num in range(doc.page_count):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text()  # type: ignore
                    processed_pages += 1
                    
                    if page_text:
                        # Clean the text
                        page_text = self._clean_text(page_text)
                        current_chunk += f" {page_text}"
                        
                        # Split into chunks when we exceed chunk_size
                        while len(current_chunk.split()) > self.chunk_size:
                            chunk_words = current_chunk.split()
                            chunk = " ".join(chunk_words[:self.chunk_size])
                            if chunk.strip():
                                yield chunk
                            current_chunk = " ".join(chunk_words[self.chunk_size:])
                
                except Exception as e:
                    logger.warning(f"Error processing page {page_num + 1} with PyMuPDF: {e}")
                    continue
            
            doc.close()
            
            # Yield remaining text as final chunk
            if current_chunk.strip():
                yield current_chunk.strip()
            
            if processed_pages == 0:
                raise ValueError("No pages could be processed from the PDF")
                
        except Exception as e:
            logger.error(f"PyMuPDF fallback failed for {pdf_path}: {e}")
            # Clean up the file if it's corrupted
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
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
