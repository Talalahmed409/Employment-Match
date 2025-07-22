#!/usr/bin/env python3
"""
Google Cloud Storage integration for file uploads and downloads
"""

import os
import logging
from typing import Optional, BinaryIO
from pathlib import Path
from datetime import datetime
import tempfile

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    CLOUD_STORAGE_AVAILABLE = True
except ImportError:
    CLOUD_STORAGE_AVAILABLE = False
    logging.warning("Google Cloud Storage not available. Install with: pip install google-cloud-storage")

logger = logging.getLogger(__name__)

class CloudStorageManager:
    """Manages file uploads and downloads using Google Cloud Storage"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "employment-match-files")
        self.client = None
        self.bucket = None
        
        if CLOUD_STORAGE_AVAILABLE:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"Initialized Cloud Storage with bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Cloud Storage: {e}")
                self.client = None
                self.bucket = None
    
    def upload_file(self, file_data: BinaryIO, file_path: str, content_type: Optional[str] = None) -> str:
        """Upload a file to Cloud Storage"""
        if not self.bucket:
            logger.error("Cloud Storage not available. Aborting upload.")
            raise RuntimeError("Cloud Storage not available. Check your GCS credentials and bucket configuration.")
        
        try:
            blob = self.bucket.blob(file_path)
            
            # Set content type if provided
            if content_type is not None:
                blob.content_type = content_type
            
            # Upload the file
            blob.upload_from_file(file_data, rewind=True)
            
            logger.info(f"Uploaded file to Cloud Storage: {file_path}")
            return f"gs://{self.bucket_name}/{file_path}"
            
        except Exception as e:
            logger.error(f"Failed to upload file to Cloud Storage: {e}")
            raise RuntimeError(f"Failed to upload file to Cloud Storage: {e}")
    
    def download_file(self, file_path: str) -> Optional[BinaryIO]:
        """Download a file from Cloud Storage"""
        if not self.bucket:
            logger.error("Cloud Storage not available. Cannot download file.")
            raise RuntimeError("Cloud Storage not available. Check your GCS credentials and bucket configuration.")
        
        try:
            blob = self.bucket.blob(file_path)
            
            # Check if file exists
            if not blob.exists():
                logger.warning(f"File not found in Cloud Storage: {file_path}")
                return None
            
            # Download to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            blob.download_to_filename(temp_file.name)
            
            # Reopen for reading
            temp_file.close()
            return open(temp_file.name, 'rb')
            
        except Exception as e:
            logger.error(f"Failed to download file from Cloud Storage: {e}")
            raise RuntimeError(f"Failed to download file from Cloud Storage: {e}")
    
    def get_download_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """Generate a signed URL for file download"""
        if not self.bucket:
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                logger.warning(f"File not found in Cloud Storage: {file_path}")
                return None
            
            # Try to generate signed URL with longer expiration
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET",
                response_type="application/octet-stream"
            )
            
            logger.info(f"Generated signed URL for {file_path}: {url[:50]}...")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate download URL for {file_path}: {e}")
            # Fallback to public URL if bucket is publicly readable
            try:
                public_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_path}"
                logger.info(f"Using public URL fallback: {public_url}")
                return public_url
            except Exception as fallback_error:
                logger.error(f"Fallback URL generation also failed: {fallback_error}")
                return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Cloud Storage"""
        if not self.bucket:
            logger.error("Cloud Storage not available. Cannot delete file.")
            raise RuntimeError("Cloud Storage not available. Check your GCS credentials and bucket configuration.")
        
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"Deleted file from Cloud Storage: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from Cloud Storage: {e}")
            raise RuntimeError(f"Failed to delete file from Cloud Storage: {e}")
    
    def get_public_url(self, file_path: str) -> Optional[str]:
        """Get public URL for file (if bucket is publicly readable)"""
        if not self.bucket:
            return None
        
        try:
            # Since bucket is public, we can generate URLs without checking blob existence
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_path}"
            logger.info(f"Generated public URL for {file_path}: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to generate public URL for {file_path}: {e}")
            return None
    
    def _save_locally(self, file_data: BinaryIO, file_path: str) -> str:
        """Fallback to local storage"""
        local_path = Path("uploads") / file_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, "wb") as f:
            file_data.seek(0)
            f.write(file_data.read())
        
        logger.info(f"Saved file locally: {local_path}")
        return str(local_path)
    
    def _read_locally(self, file_path: str) -> Optional[BinaryIO]:
        """Read file from local storage"""
        local_path = Path("uploads") / file_path
        
        if not local_path.exists():
            return None
        
        try:
            return open(local_path, "rb")
        except Exception as e:
            logger.error(f"Failed to read local file: {e}")
            return None
    
    def _delete_locally(self, file_path: str) -> bool:
        """Delete file from local storage"""
        local_path = Path("uploads") / file_path
        
        try:
            if local_path.exists():
                local_path.unlink()
                logger.info(f"Deleted local file: {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete local file: {e}")
            return False

# Global instance
storage_manager = CloudStorageManager()

def get_storage_manager() -> CloudStorageManager:
    """Get the global storage manager instance"""
    return storage_manager 