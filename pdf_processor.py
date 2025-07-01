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
                        # Try multiple extraction methods for problematic PDFs
                        page_text = None
                        
                        # Method 1: Standard text extraction
                        try:
                            page_text = page.extract_text()
                        except Exception as e1:
                            logger.warning(f"Standard extraction failed for page {page_num + 1}: {e1}")
                            
                            # Method 2: Extract with simpler parameters
                            try:
                                page_text = page.extract_text(layout=False)
                            except Exception as e2:
                                logger.warning(f"Simple extraction failed for page {page_num + 1}: {e2}")
                                
                                # Method 3: Extract characters directly
                                try:
                                    chars = page.chars
                                    if chars:
                                        page_text = ''.join([char.get('text', '') for char in chars])
                                except Exception as e3:
                                    logger.warning(f"Character extraction failed for page {page_num + 1}: {e3}")
                                    page_text = f"[Page {page_num + 1}: Content extraction failed]"
                        
                        processed_pages += 1
                        
                        if page_text and page_text.strip():
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
            logger.error(f"pdfplumber processing failed: {str(e)}")
            logger.info("Attempting fallback with PyMuPDF...")
            
            # Fallback to PyMuPDF
            try:
                import fitz  # PyMuPDF
                
                current_chunk = ""
                processed_pages = 0
                
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    try:
                        page = doc.load_page(page_num)
                        page_text = page.get_text()
                        processed_pages += 1
                        
                        if page_text and page_text.strip():
                            page_text = self._clean_text(page_text)
                            current_chunk += f" {page_text}"
                            
                            while len(current_chunk.split()) > self.chunk_size:
                                chunk_words = current_chunk.split()
                                chunk = " ".join(chunk_words[:self.chunk_size])
                                if chunk.strip():
                                    yield chunk
                                current_chunk = " ".join(chunk_words[self.chunk_size:])
                    
                    except Exception as page_error:
                        logger.warning(f"PyMuPDF error on page {page_num + 1}: {page_error}")
                        continue
                
                doc.close()
                
                # Yield remaining chunk
                if current_chunk.strip():
                    yield current_chunk
                
                if processed_pages == 0:
                    raise ValueError("Could not extract text from any pages using either method")
                    
                logger.info(f"PyMuPDF fallback successful: processed {processed_pages} pages")
                
            except ImportError:
                logger.error("PyMuPDF not available for fallback")
                # Clean up file if processing failed
                try:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except:
                    pass
                raise ValueError(f"Failed to process PDF with pdfplumber: {str(e)}")
            except Exception as fallback_error:
                logger.error(f"PyMuPDF fallback also failed: {str(fallback_error)}")
                # Clean up file if processing failed
                try:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except:
                    pass
                raise ValueError(f"Failed to process PDF with both methods: pdfplumber ({str(e)}), PyMuPDF ({str(fallback_error)})")
    
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