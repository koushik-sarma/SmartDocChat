import pdfplumber
import logging
from typing import List, Generator, Dict
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
        
        # Use pdfplumber for reliable PDF text extraction with fallback detection
        logger.info("Using pdfplumber for PDF text extraction")
        
        # Extract text using pdfplumber with early fallback detection
        try:
            # Quick check for problematic PDFs by file size and content hints
            if file_size > 30000000:  # Files larger than 30MB are often complex textbooks
                logger.info("Large PDF detected (>30MB), using PyMuPDF for better performance")
                raise Exception("Large PDF detected, switching to PyMuPDF")
                
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("PDF file contains no pages")
                
                current_chunk = ""
                processed_pages = 0
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if not page_text:
                            page_text = f"[Page {page_num + 1}: No extractable text]"
                        
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
                import pymupdf  # PyMuPDF
                
                current_chunk = ""
                processed_pages = 0
                
                doc = pymupdf.open(pdf_path)
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
        """Clean extracted text while preserving chemical equations and special characters."""
        if not text:
            return ""
        
        # Convert Unicode special characters first
        text = self._convert_special_characters(text)
        
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Don't remove special characters - keep them for chemistry/math content
        # Only remove non-printable control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text
    
    def _convert_special_characters(self, text: str) -> str:
        """Convert Unicode superscripts, subscripts, and special characters to readable format."""
        # Chemical formula mappings
        subscript_map = {
            '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
            'ₐ': 'a', 'ₑ': 'e', 'ᵢ': 'i', 'ₒ': 'o', 'ᵤ': 'u', 'ₓ': 'x', 'ₙ': 'n', 'ₘ': 'm', 'ₚ': 'p', 'ₛ': 's', 'ₜ': 't'
        }
        
        superscript_map = {
            '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
            'ᵃ': 'a', 'ᵇ': 'b', 'ᶜ': 'c', 'ᵈ': 'd', 'ᵉ': 'e', 'ᶠ': 'f', 'ᵍ': 'g', 'ʰ': 'h', 'ⁱ': 'i', 'ʲ': 'j',
            'ᵏ': 'k', 'ˡ': 'l', 'ᵐ': 'm', 'ⁿ': 'n', 'ᵒ': 'o', 'ᵖ': 'p', 'ʳ': 'r', 'ˢ': 's', 'ᵗ': 't', 'ᵘ': 'u',
            'ᵛ': 'v', 'ʷ': 'w', 'ˣ': 'x', 'ʸ': 'y', 'ᶻ': 'z', '⁺': '+', '⁻': '-', '⁼': '='
        }
        
        # Special chemistry and physics symbols
        special_symbols = {
            '→': ' → ', '←': ' ← ', '↔': ' ↔ ', '⇌': ' ⇌ ',
            '∆': 'Δ', '°': '°', '∞': '∞', '±': '±',
            'α': 'α', 'β': 'β', 'γ': 'γ', 'δ': 'δ', 'ε': 'ε',
            'λ': 'λ', 'μ': 'μ', 'π': 'π', 'σ': 'σ', 'Ω': 'Ω', 'θ': 'θ', 'φ': 'φ'
        }
        
        # Apply subscript conversions with underscore notation
        for sub, normal in subscript_map.items():
            text = text.replace(sub, f'_{normal}')
        
        # Apply superscript conversions with caret notation
        for sup, normal in superscript_map.items():
            text = text.replace(sup, f'^{normal}')
        
        # Keep special symbols as-is (don't convert to text)
        # This preserves the visual appearance of equations
        
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
    
    def extract_images_from_pdf(self, pdf_path: str, query: str = None) -> List[Dict]:
        """
        Extract images from PDF that are relevant to a user query.
        Returns list of image info with base64 data for display.
        """
        images = []
        logger.info(f"Starting image extraction from: {pdf_path}")
        
        try:
            # Try with PyMuPDF first
            import pymupdf
            doc = pymupdf.open(pdf_path)
            logger.info(f"Opened PDF with {len(doc)} pages for image extraction")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                logger.info(f"Page {page_num + 1}: Found {len(image_list)} images")
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image reference and extract
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Skip very small images (likely UI elements)
                        if len(image_bytes) < 1000:  # Less than 1KB
                            continue
                        
                        # Convert to base64 for web display
                        import base64
                        img_base64 = base64.b64encode(image_bytes).decode()
                        
                        images.append({
                            'page': page_num + 1,
                            'index': img_index,
                            'base64': img_base64,
                            'format': image_ext,
                            'size': len(image_bytes),
                            'width': img[2],  # width from image metadata
                            'height': img[3]  # height from image metadata
                        })
                        
                        logger.info(f"Extracted image {img_index} from page {page_num + 1}: {len(image_bytes)} bytes, format: {image_ext}")
                        
                    except Exception as img_error:
                        logger.warning(f"Error extracting image {img_index} from page {page_num + 1}: {img_error}")
                        continue
            
            doc.close()
            logger.info(f"Total images extracted: {len(images)}")
            
        except Exception as e:
            logger.error(f"Error extracting images with PyMuPDF: {e}")
            
            # Fallback: Try with pdfplumber
            try:
                import pdfplumber
                logger.info("Trying image extraction with pdfplumber fallback")
                
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        if hasattr(page, 'images'):
                            page_images = page.images
                            logger.info(f"pdfplumber - Page {page_num + 1}: Found {len(page_images)} images")
                        
            except Exception as fallback_error:
                logger.error(f"Fallback image extraction also failed: {fallback_error}")
        
        # If query is provided, filter images that might be relevant
        if query and images:
            # Return first few images if query contains image-related keywords
            image_keywords = ['image', 'picture', 'chart', 'graph', 'diagram', 'figure', 'photo', 'show me', 'display']
            if any(keyword in query.lower() for keyword in image_keywords):
                logger.info(f"Query '{query}' contains image keywords, returning {min(3, len(images))} images")
                return images[:3]  # Return up to 3 most relevant images
        
        final_count = min(5, len(images))
        logger.info(f"Returning {final_count} images from PDF")
        return images[:final_count]