import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Optional, Dict, Any
import io

from utils.logger import Logger
from utils.exceptions import S3ConnectionError
from config.settings import get_settings

class S3Client:
    def __init__(self):
        self.settings = get_settings()
        self.logger = Logger.get_logger()
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client with credentials"""
        try:
            self._client = boto3.client(
                's3',
                aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.settings.AWS_DEFAULT_REGION
            )
            
            # Test connection
            self._client.head_bucket(Bucket=self.settings.S3_BUCKET_NAME)
            self.logger.info(f"Successfully connected to S3 bucket: {self.settings.S3_BUCKET_NAME}")
            
        except NoCredentialsError:
            raise S3ConnectionError("AWS credentials not found")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise S3ConnectionError(f"Bucket {self.settings.S3_BUCKET_NAME} not found")
            elif error_code == '403':
                raise S3ConnectionError(f"Access denied to bucket {self.settings.S3_BUCKET_NAME}")
            else:
                raise S3ConnectionError(f"S3 connection error: {str(e)}")
    
    def list_objects(self, prefix: str = '') -> List[Dict[str, Any]]:
        """List all objects in bucket with given prefix"""
        try:
            objects = []
            paginator = self._client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.settings.S3_BUCKET_NAME,
                Prefix=prefix
            )
            
            for page in pages:
                if 'Contents' in page:
                    objects.extend(page['Contents'])
            
            return objects
            
        except ClientError as e:
            self.logger.error(f"Error listing objects: {str(e)}")
            raise S3ConnectionError(f"Failed to list objects: {str(e)}")
    
    def get_object(self, key: str) -> bytes:
        """Get object content from S3"""
        try:
            response = self._client.get_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            self.logger.error(f"Error getting object {key}: {str(e)}")
            raise S3ConnectionError(f"Failed to get object {key}: {str(e)}")
    
    def put_object(self, key: str, body: bytes, content_type: str = 'application/octet-stream') -> bool:
        """Put object to S3"""
        try:
            self._client.put_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=key,
                Body=body,
                ContentType=content_type
            )
            return True
            
        except ClientError as e:
            self.logger.error(f"Error putting object {key}: {str(e)}")
            raise S3ConnectionError(f"Failed to put object {key}: {str(e)}")
    
    def delete_object(self, key: str) -> bool:
        """Delete object from S3"""
        try:
            self._client.delete_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=key
            )
            return True
            
        except ClientError as e:
            self.logger.error(f"Error deleting object {key}: {str(e)}")
            raise S3ConnectionError(f"Failed to delete object {key}: {str(e)}")
