import os
import logging
import tempfile
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PDFCompressor:
    """
    PDF compression utility using PyMuPDF for reducing file sizes
    before processing. Similar to smallpdf/ilovepdf functionality.
    """
    
    def __init__(self):
        self.compression_levels = {
            'low': {'quality': 85, 'image_quality': 75},
            'medium': {'quality': 70, 'image_quality': 60},
            'high': {'quality': 50, 'image_quality': 40},
            'extreme': {'quality': 30, 'image_quality': 25}
        }
    
    def compress_pdf(self, input_path: str, output_path: str = None, 
                    compression_level: str = 'medium') -> Dict[str, Any]:
        """
        Compress a PDF file to reduce its size.
        
        Args:
            input_path: Path to input PDF file
            output_path: Path for compressed output (optional)
            compression_level: 'low', 'medium', 'high', or 'extreme'
            
        Returns:
            Dict with compression results and metadata
        """
        try:
            import pymupdf  # PyMuPDF
            
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Get original file size
            original_size = os.path.getsize(input_path)
            
            # Set compression parameters
            if compression_level not in self.compression_levels:
                compression_level = 'medium'
            
            params = self.compression_levels[compression_level]
            
            # Create output path if not provided
            if output_path is None:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_compressed{ext}"
            
            # Open and process PDF
            doc = pymupdf.open(input_path)
            
            # Compression settings
            compression_options = {
                "garbage": 4,  # Remove unused objects
                "clean": True,  # Clean up PDF structure
                "deflate": True,  # Use deflate compression
                "deflate_images": True,  # Compress images
                "deflate_fonts": True,  # Compress fonts
            }
            
            # Process each page for image compression
            pages_processed = 0
            images_compressed = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get images on page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Only compress if image is large enough
                        if len(image_bytes) > 50000:  # 50KB threshold
                            # Replace with compressed version
                            compressed_image = self._compress_image_bytes(
                                image_bytes, image_ext, params['image_quality']
                            )
                            
                            if compressed_image and len(compressed_image) < len(image_bytes):
                                # Update image in PDF
                                doc._getXrefObject(xref, compressed_image)
                                images_compressed += 1
                                
                    except Exception as e:
                        logger.warning(f"Failed to compress image {img_index} on page {page_num}: {e}")
                        continue
                
                pages_processed += 1
            
            # Save compressed PDF
            doc.save(output_path, **compression_options)
            doc.close()
            
            # Get compressed file size
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (original_size - compressed_size) / original_size * 100
            
            result = {
                'success': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': round(compression_ratio, 2),
                'size_reduction_mb': round((original_size - compressed_size) / 1024 / 1024, 2),
                'output_path': output_path,
                'pages_processed': pages_processed,
                'images_compressed': images_compressed,
                'compression_level': compression_level
            }
            
            logger.info(f"PDF compressed: {original_size} -> {compressed_size} bytes "
                       f"({compression_ratio:.1f}% reduction)")
            
            return result
            
        except ImportError:
            raise ValueError("PyMuPDF not available for PDF compression")
        except Exception as e:
            logger.error(f"PDF compression failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_size': original_size if 'original_size' in locals() else 0
            }
    
    def _compress_image_bytes(self, image_bytes: bytes, image_ext: str, quality: int) -> Optional[bytes]:
        """Compress image bytes using PIL/Pillow."""
        try:
            from PIL import Image
            import io
            
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Compress image
            output = io.BytesIO()
            
            if image_ext.lower() in ['jpg', 'jpeg']:
                image.save(output, format='JPEG', quality=quality, optimize=True)
            elif image_ext.lower() == 'png':
                image.save(output, format='PNG', optimize=True)
            else:
                # Default to JPEG for other formats
                image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image compression failed: {e}")
            return None
    
    def get_compression_estimate(self, file_path: str) -> Dict[str, Any]:
        """
        Estimate potential compression savings without actually compressing.
        """
        try:
            import pymupdf
            
            file_size = os.path.getsize(file_path)
            doc = pymupdf.open(file_path)
            
            total_images = 0
            total_image_size = 0
            large_images = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                images = page.get_images()
                
                for img in images:
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_size = len(base_image["image"])
                        
                        total_images += 1
                        total_image_size += image_size
                        
                        if image_size > 50000:  # 50KB threshold
                            large_images += 1
                            
                    except:
                        continue
            
            doc.close()
            
            # Estimate compression potential
            estimated_savings = min(file_size * 0.7, total_image_size * 0.5)
            estimated_ratio = (estimated_savings / file_size * 100) if file_size > 0 else 0
            
            return {
                'file_size': file_size,
                'total_images': total_images,
                'large_images': large_images,
                'total_image_size': total_image_size,
                'estimated_savings_bytes': int(estimated_savings),
                'estimated_compression_ratio': round(estimated_ratio, 2),
                'recommendation': self._get_compression_recommendation(file_size, large_images)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_compression_recommendation(self, file_size: int, large_images: int) -> str:
        """Recommend compression level based on file analysis."""
        size_mb = file_size / 1024 / 1024
        
        if size_mb > 50:
            return 'high'
        elif size_mb > 20:
            return 'medium'
        elif large_images > 10:
            return 'medium'
        else:
            return 'low'
    
    def auto_compress_if_needed(self, file_path: str, max_size_mb: int = 25) -> Optional[str]:
        """
        Automatically compress PDF if it exceeds size threshold.
        Returns path to compressed file or None if no compression needed.
        """
        file_size = os.path.getsize(file_path)
        size_mb = file_size / 1024 / 1024
        
        if size_mb <= max_size_mb:
            return None  # No compression needed
        
        # Create compressed version
        base, ext = os.path.splitext(file_path)
        compressed_path = f"{base}_auto_compressed{ext}"
        
        # Choose compression level based on size
        if size_mb > 100:
            level = 'extreme'
        elif size_mb > 50:
            level = 'high'
        else:
            level = 'medium'
        
        result = self.compress_pdf(file_path, compressed_path, level)
        
        if result.get('success'):
            logger.info(f"Auto-compressed {size_mb:.1f}MB PDF to "
                       f"{result['compressed_size']/1024/1024:.1f}MB")
            return compressed_path
        else:
            return None