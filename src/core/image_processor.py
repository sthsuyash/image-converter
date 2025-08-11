import io
from PIL import Image
from typing import Optional, Tuple
import os

from utils.logger import Logger
from utils.exceptions import ImageProcessingError

class ImageProcessor:
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'}
    
    def __init__(self):
        self.logger = Logger.get_logger()
    
    def is_supported_image(self, filename: str) -> bool:
        """Check if file is a supported image format"""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.SUPPORTED_FORMATS
    
    def convert_to_webp(self, image_data: bytes, quality: int = 100) -> bytes:
        """Convert image data to WebP format"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary (WebP doesn't support all modes)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # For images with transparency, convert to RGBA
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    elif img.mode in ('RGBA', 'LA'):
                        # Keep transparency for WebP
                        pass
                    else:
                        img = img.convert('RGB')
                
                # Save as WebP to memory
                webp_buffer = io.BytesIO()
                
                # Use lossless for images with transparency
                if img.mode in ('RGBA', 'LA'):
                    img.save(webp_buffer, format='WEBP', lossless=True, optimize=True)
                else:
                    img.save(webp_buffer, format='WEBP', quality=quality, optimize=True)
                
                webp_buffer.seek(0)
                return webp_buffer.getvalue()
                
        except Exception as e:
            self.logger.error(f"Error converting image to WebP: {str(e)}")
            raise ImageProcessingError(f"Failed to convert image: {str(e)}")
    
    def get_image_info(self, image_data: bytes) -> dict:
        """Get image information"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            self.logger.error(f"Error getting image info: {str(e)}")
            raise ImageProcessingError(f"Failed to get image info: {str(e)}")
