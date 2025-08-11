import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import time

from core.s3_client import S3Client
from core.image_processor import ImageProcessor
from utils.logger import Logger
from utils.exceptions import ConversionError
from config.settings import get_settings

class S3ImageConverter:
    def __init__(self):
        self.settings = get_settings()
        self.logger = Logger.get_logger()
        self.s3_client = S3Client()
        self.image_processor = ImageProcessor()
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
    
    def get_image_keys(self) -> List[str]:
        """Get all image file keys from S3 bucket"""
        try:
            objects = self.s3_client.list_objects(self.settings.S3_PREFIX)
            image_keys = [
                obj['Key'] for obj in objects 
                if self.image_processor.is_supported_image(obj['Key'])
            ]
            
            self.logger.info(f"Found {len(image_keys)} image files in bucket")
            return image_keys
            
        except Exception as e:
            self.logger.error(f"Error getting image keys: {str(e)}")
            raise ConversionError(f"Failed to get image keys: {str(e)}")
    
    def _generate_webp_key(self, source_key: str) -> str:
        """Generate WebP destination key"""
        if self.settings.S3_DESTINATION_PREFIX:
            filename = os.path.basename(source_key)
            name_without_ext = os.path.splitext(filename)[0]
            return f"{self.settings.S3_DESTINATION_PREFIX}/{name_without_ext}.webp"
        else:
            name_without_ext = os.path.splitext(source_key)[0]
            return f"{name_without_ext}.webp"
    
    def _convert_single_image(self, source_key: str) -> Dict[str, any]:
        """Convert a single image to WebP"""
        result = {
            'source_key': source_key,
            'destination_key': None,
            'success': False,
            'error': None,
            'original_size': 0,
            'webp_size': 0,
            'compression_ratio': 0
        }
        
        try:
            # Generate destination key
            destination_key = self._generate_webp_key(source_key)
            result['destination_key'] = destination_key
            
            # Check if WebP already exists
            try:
                self.s3_client.get_object(destination_key)
                self.logger.info(f"WebP already exists, skipping: {destination_key}")
                result['success'] = True
                result['error'] = 'Already exists'
                self.stats['skipped'] += 1
                return result
            except:
                pass  # File doesn't exist, continue with conversion
            
            # Get original image
            image_data = self.s3_client.get_object(source_key)
            result['original_size'] = len(image_data)
            
            # Convert to WebP
            webp_data = self.image_processor.convert_to_webp(
                image_data, 
                quality=self.settings.WEBP_QUALITY
            )
            result['webp_size'] = len(webp_data)
            
            # Calculate compression ratio
            if result['original_size'] > 0:
                result['compression_ratio'] = (
                    (result['original_size'] - result['webp_size']) / result['original_size']
                ) * 100
            
            # Upload WebP to S3
            self.s3_client.put_object(
                destination_key,
                webp_data,
                content_type='image/webp'
            )
            
            # Delete original if requested
            if self.settings.DELETE_ORIGINAL:
                self.s3_client.delete_object(source_key)
                self.logger.info(f"Deleted original file: {source_key}")
            
            result['success'] = True
            self.stats['successful'] += 1
            
            self.logger.info(
                f"Converted {source_key} -> {destination_key} "
                f"({result['original_size']} -> {result['webp_size']} bytes, "
                f"{result['compression_ratio']:.1f}% compression)"
            )
            
        except Exception as e:
            result['error'] = str(e)
            self.stats['failed'] += 1
            self.logger.error(f"Failed to convert {source_key}: {str(e)}")
        
        finally:
            self.stats['processed'] += 1
        
        return result
    
    def convert_images(self, image_keys: Optional[List[str]] = None) -> Dict[str, any]:
        """Convert images to WebP format with parallel processing"""
        if image_keys is None:
            image_keys = self.get_image_keys()
        
        if not image_keys:
            self.logger.warning("No images found to convert")
            return {'results': [], 'stats': self.stats}
        
        self.stats['total_files'] = len(image_keys)
        self.stats['start_time'] = time.time()
        
        self.logger.info(f"Starting conversion of {len(image_keys)} images with {self.settings.MAX_WORKERS} workers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.settings.MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(self._convert_single_image, key): key 
                for key in image_keys
            }
            
            # Process completed tasks
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log progress
                    if self.stats['processed'] % 10 == 0:
                        self.logger.info(
                            f"Progress: {self.stats['processed']}/{self.stats['total_files']} "
                            f"({self.stats['processed']/self.stats['total_files']*100:.1f}%)"
                        )
                        
                except Exception as e:
                    self.logger.error(f"Unexpected error processing {key}: {str(e)}")
                    results.append({
                        'source_key': key,
                        'success': False,
                        'error': str(e)
                    })
                    self.stats['failed'] += 1
                    self.stats['processed'] += 1
        
        self.stats['end_time'] = time.time()
        self._log_final_stats()
        
        return {
            'results': results,
            'stats': self.stats
        }
    
    def _log_final_stats(self):
        """Log final conversion statistics"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        self.logger.info("=" * 60)
        self.logger.info("CONVERSION COMPLETED")
        self.logger.info("=" * 60)
        self.logger.info(f"Total files: {self.stats['total_files']}")
        self.logger.info(f"Successful: {self.stats['successful']}")
        self.logger.info(f"Failed: {self.stats['failed']}")
        self.logger.info(f"Skipped: {self.stats['skipped']}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info(f"Average time per file: {duration/self.stats['total_files']:.2f} seconds")
        self.logger.info("=" * 60)
