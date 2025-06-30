import pdfplumber
import logging
from typing import List, Generator
import os
import re

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def extract_text_chunks(self, pdf_path: str) -> Generator[str, None, None]:
        """
        Extract text from PDF in chunks to handle large files efficiently.
        Uses pdfplumber for reliable text extraction.
        """
        # First, check if file exists and is readable
        logger.info(f"Starting PDF text extraction for: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        file_size = os.path.getsize(pdf_path)
        logger.info(f"PDF file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("PDF file is empty")
            raise ValueError("PDF file is empty")
        
        # Use pdfplumber for reliable PDF text extraction
        logger.info("Using pdfplumber for PDF text extraction")
        
        # Extract text using pdfplumber
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
                
                # Yield remaining chunk
                if current_chunk.strip():
                    yield current_chunk
                
                if processed_pages == 0:
                    raise ValueError("Could not extract text from any pages")
                    
                logger.info(f"Successfully processed {processed_pages} pages")
                
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            # Clean up file if processing failed
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except:
                pass
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace and formatting."""
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\']', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """Get basic information about the PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return {
                    'page_count': len(pdf.pages),
                    'file_size': os.path.getsize(pdf_path),
                    'filename': os.path.basename(pdf_path)
                }
        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            raise ValueError(f"Cannot read PDF file: {str(e)}")