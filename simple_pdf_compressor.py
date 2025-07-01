"""
Simple PDF Compressor - Fast compression for large PDFs
Optimized for speed and basic file size reduction
"""
import os
import logging
from typing import Dict, Any, Optional
try:
    import fitz  # PyMuPDF
except ImportError:
    try:
        import pymupdf as fitz
    except ImportError:
        fitz = None

logger = logging.getLogger(__name__)

class SimplePDFCompressor:
    """Fast PDF compression using basic PyMuPDF optimization."""
    
    def __init__(self):
        self.compression_levels = {
            'low': {'deflate': 1, 'garbage': 1, 'clean': 0},
            'medium': {'deflate': 1, 'garbage': 2, 'clean': 1}, 
            'high': {'deflate': 1, 'garbage': 3, 'clean': 1},
            'extreme': {'deflate': 1, 'garbage': 4, 'clean': 1}
        }
    
    def compress_pdf(self, input_path: str, output_path: str = None, 
                    compression_level: str = 'medium') -> Dict[str, Any]:
        """
        Fast PDF compression using PyMuPDF optimization.
        """
        try:
            if fitz is None:
                return {'success': False, 'error': 'PyMuPDF not available for PDF compression'}
                
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Input file not found'}
            
            # Get original file size
            original_size = os.path.getsize(input_path)
            
            # Generate output path if not provided
            if not output_path:
                base = os.path.splitext(input_path)[0]
                output_path = f"{base}_compressed.pdf"
            
            # Get compression parameters
            params = self.compression_levels.get(compression_level, self.compression_levels['medium'])
            
            # Open and optimize PDF
            with fitz.open(input_path) as doc:
            
            # Simple optimization approach
            doc.save(output_path, 
                    deflate=params['deflate'],
                    garbage=params['garbage'], 
                    clean=params['clean'],
                    linear=True)
            doc.close()
            
            # Verify compression worked
            if os.path.exists(output_path):
                compressed_size = os.path.getsize(output_path)
                
                # Calculate compression metrics
                size_reduction = original_size - compressed_size
                if size_reduction > 0:
                    compression_ratio = round(size_reduction / original_size * 100, 2)
                else:
                    compression_ratio = 0
                
                return {
                    'success': True,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': compression_ratio,
                    'size_reduction_mb': round(size_reduction / 1024 / 1024, 2),
                    'output_path': output_path,
                    'pages_processed': len(fitz.open(input_path)),
                    'images_compressed': 0,  # Basic compression doesn't track images
                    'compression_level': compression_level
                }
            else:
                return {'success': False, 'error': 'Failed to create compressed file'}
                
        except Exception as e:
            logger.error(f"PDF compression failed: {e}")
            return {'success': False, 'error': f'Compression failed: {str(e)}'}
    
    def get_compression_estimate(self, file_path: str) -> Dict[str, Any]:
        """Get quick compression estimate."""
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            file_size = os.path.getsize(file_path)
            
            # Open PDF to get basic info
            doc = fitz.open(file_path)
            page_count = len(doc)
            
            # Count images quickly
            total_images = 0
            for page_num in range(min(5, page_count)):  # Sample first 5 pages
                page = doc.load_page(page_num)
                total_images += len(page.get_images())
            
            doc.close()
            
            # Estimate compression based on file size and content
            if file_size > 50 * 1024 * 1024:  # >50MB
                estimated_compression = 0.15  # 15% compression
                recommendation = 'high'
            elif file_size > 20 * 1024 * 1024:  # >20MB
                estimated_compression = 0.10  # 10% compression  
                recommendation = 'medium'
            else:
                estimated_compression = 0.05  # 5% compression
                recommendation = 'low'
            
            estimated_savings = file_size * estimated_compression
            
            return {
                'file_size': file_size,
                'total_images': total_images,
                'large_images': max(0, total_images - 10),
                'estimated_savings_bytes': estimated_savings,
                'estimated_compression_ratio': round(1 / (1 - estimated_compression), 2),
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error estimating compression: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def auto_compress_if_needed(self, file_path: str, max_size_mb: int = 25) -> Optional[str]:
        """Auto-compress if file exceeds threshold."""
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size_mb * 1024 * 1024:
                result = self.compress_pdf(file_path, compression_level='medium')
                if result.get('success'):
                    return result['output_path']
            return None
        except Exception as e:
            logger.error(f"Auto-compression failed: {e}")
            return None