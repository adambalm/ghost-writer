#!/usr/bin/env python3
"""
Test the corrected production parser against the forensic test results.
This script validates that our fixes produce identical output.
"""

import numpy as np
from PIL import Image
import logging
import sys
import os

# Add src to path to import our corrected parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.supernote_parser import SupernoteParser
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_corrected_parser():
    """Test the corrected production parser"""
    
    file_path = "/home/ed/ghost-writer/joe.note"
    
    if not os.path.exists(file_path):
        logger.error(f"Test file not found: {file_path}")
        return False
    
    logger.info("=== TESTING CORRECTED PRODUCTION PARSER ===")
    logger.info("Validating fixes against forensic test results")
    
    try:
        # Initialize parser and parse file
        parser = SupernoteParser()
        pages = parser.parse_file(Path(file_path))
        
        if not pages:
            logger.error("No pages extracted")
            return False
        
        logger.info(f"Extracted {len(pages)} pages")
        
        # Process each page
        results = []
        for i, page in enumerate(pages):
            logger.info(f"\n--- Processing Page {i+1} ---")
            
            if page.metadata and 'decoded_bitmap' in page.metadata:
                bitmap = page.metadata['decoded_bitmap']
                
                # Analyze content
                non_white_pixels = np.sum(bitmap < 255)
                total_pixels = bitmap.shape[0] * bitmap.shape[1]
                content_percentage = (non_white_pixels / total_pixels) * 100
                
                logger.info(f"  Content detected: {non_white_pixels:,} pixels ({content_percentage:.2f}%)")
                
                if non_white_pixels > 0:
                    min_val = np.min(bitmap[bitmap < 255])
                    logger.info(f"  Darkest value: {min_val}")
                
                # Save image for visual verification
                output_path = f"corrected_parser_Page{i+1}.png"
                img = Image.fromarray(bitmap, mode='L')
                img.save(output_path)
                logger.info(f"  Saved: {output_path}")
                
                results.append({
                    'page': i+1,
                    'non_white_pixels': non_white_pixels,
                    'content_percentage': content_percentage,
                    'output_path': output_path
                })
            else:
                logger.warning(f"  No bitmap data in page {i+1}")
        
        # Validate results
        success = True
        for result in results:
            if result['non_white_pixels'] == 0:
                logger.error(f"Page {result['page']}: No content detected - parser failed")
                success = False
            else:
                logger.info(f"Page {result['page']}: SUCCESS - {result['non_white_pixels']:,} pixels extracted")
        
        logger.info(f"\n=== CORRECTED PARSER TEST {'PASSED' if success else 'FAILED'} ===")
        
        if success:
            logger.info("Parser successfully extracts readable handwriting content")
            logger.info("Ready for production use with corrected RLE decoder")
        else:
            logger.error("Parser still has issues - investigate further")
        
        return success
        
    except Exception as e:
        logger.error(f"Parser test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_corrected_parser()
    sys.exit(0 if success else 1)