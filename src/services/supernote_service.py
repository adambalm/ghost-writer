"""
Unified Supernote Processing Service

This service provides a single interface for Supernote file processing
that can be used by both CLI and web interfaces.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from src.utils.supernote_parser_enhanced import convert_note_to_images
from src.utils.ocr_providers import HybridOCR
from src.utils.supernote_api import create_supernote_client, SupernoteFile

logger = logging.getLogger(__name__)


class SupernoteService:
    """Unified service for Supernote file processing"""
    
    def __init__(self):
        from src.utils.config import config
        self.ocr_provider = HybridOCR(config.get('ocr', {}))
    
    def process_note_file(self, note_path: Path, output_dir: Path) -> Dict:
        """
        Process a .note file and return structured results
        
        Args:
            note_path: Path to .note file
            output_dir: Directory for output files
            
        Returns:
            Dict with processing results including extracted images and OCR text
        """
        try:
            # Create temp directory for images
            temp_dir = output_dir / "temp_images"
            temp_dir.mkdir(exist_ok=True)
            
            # Extract images using clean room decoder
            image_paths = convert_note_to_images(note_path, temp_dir)
            
            if not image_paths:
                logger.warning(f"No images extracted from {note_path}")
                return {"success": False, "error": "No images extracted"}
            
            # Process each image with OCR
            ocr_results = []
            for img_path in image_paths:
                ocr_result = self.ocr_provider.extract_text(str(img_path))
                if ocr_result and ocr_result.text.strip():
                    ocr_results.append({
                        "image_path": str(img_path),
                        "text": ocr_result.text,
                        "confidence": ocr_result.confidence,
                        "provider": ocr_result.provider
                    })
            
            return {
                "success": True,
                "note_path": str(note_path),
                "extracted_images": [str(p) for p in image_paths],
                "ocr_results": ocr_results,
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process note file {note_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate_supernote(self, phone: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Authenticate with Supernote Cloud service
        
        Args:
            phone: Phone number (if not provided, will check environment)
            password: Password (if not provided, will check environment)
            
        Returns:
            True if authentication successful
        """
        try:
            from src.utils.config import config
            client = create_supernote_client(config._config, email=phone, password=password)
            return client is not None
        except Exception as e:
            logger.error(f"Supernote authentication failed: {e}")
            return False
    
    def list_cloud_files(self) -> List[SupernoteFile]:
        """
        List files from Supernote Cloud
        
        Returns:
            List of SupernoteFile objects
        """
        try:
            from src.utils.config import config
            client = create_supernote_client(config._config)
            if not client:
                logger.error("Not authenticated with Supernote Cloud")
                return []
            
            return client.list_files()
        except Exception as e:
            logger.error(f"Failed to list cloud files: {e}")
            return []
    
    def download_cloud_file(self, supernote_file: SupernoteFile, output_path: Path) -> bool:
        """
        Download a file from Supernote Cloud
        
        Args:
            supernote_file: SupernoteFile object to download
            output_path: Where to save the file
            
        Returns:
            True if download successful
        """
        try:
            from src.utils.config import config
            client = create_supernote_client(config._config)
            if not client:
                logger.error("Not authenticated with Supernote Cloud")
                return False
            
            return client.download_file(supernote_file, output_path)
        except Exception as e:
            file_name = getattr(supernote_file, 'name', str(supernote_file))
            logger.error(f"Failed to download file {file_name}: {e}")
            return False


# Global service instance
supernote_service = SupernoteService()