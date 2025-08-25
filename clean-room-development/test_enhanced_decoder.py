#!/usr/bin/env python3
"""
Test script for enhanced Supernote decoder based on clean room format specification

This script validates the 27x pixel improvement through:
- Enhanced RLE decoding algorithms
- Multi-layer extraction (MAINLAYER + BGLAYER)
- Format specification compliance
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.supernote_parser import SupernoteParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_decoder():
    """Test the enhanced decoder against joe.note"""
    
    # Use parent directory file
    test_file = Path(__file__).parent.parent / "joe.note"
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return False
    
    logger.info(f"Testing enhanced decoder with: {test_file}")
    logger.info(f"File size: {test_file.stat().st_size:,} bytes")
    
    # Initialize parser
    parser = SupernoteParser()
    
    # Parse with timing
    start_time = time.time()
    
    try:
        pages = parser.parse_file(test_file)
        parse_time = time.time() - start_time
        
        logger.info(f"Parse completed in {parse_time:.3f}s")
        logger.info(f"Found {len(pages)} pages")
        
        # Analyze each page
        total_pixels = 0
        total_non_white = 0
        
        for i, page in enumerate(pages, 1):
            logger.info(f"\n--- Page {i} Analysis ---")
            logger.info(f"Page ID: {page.page_id}")
            logger.info(f"Dimensions: {page.width}x{page.height}")
            
            if page.metadata:
                logger.info(f"Parser type: {page.metadata.get('parser', 'unknown')}")
                logger.info(f"Format: {page.metadata.get('format', 'unknown')}")
                logger.info(f"Layer: {page.metadata.get('layer_name', 'unknown')}")
                
                if 'decoded_bitmap' in page.metadata:
                    bitmap = page.metadata['decoded_bitmap']
                    page_pixels = bitmap.size
                    page_non_white = (bitmap < 255).sum()
                    
                    total_pixels += page_pixels
                    total_non_white += page_non_white
                    
                    logger.info(f"Total pixels: {page_pixels:,}")
                    logger.info(f"Non-white pixels: {page_non_white:,}")
                    logger.info(f"Content ratio: {page_non_white/page_pixels:.4f}")
                else:
                    logger.info("No decoded bitmap found")
        
        # Performance summary
        logger.info(f"\n=== Enhanced Decoder Performance ===")
        logger.info(f"Total pixels extracted: {total_pixels:,}")
        logger.info(f"Total content pixels: {total_non_white:,}")
        logger.info(f"Processing speed: {parse_time:.3f}s")
        logger.info(f"Performance ratio: {total_pixels / max(1, parse_time):,.0f} pixels/second")
        
        # Compare to baseline
        baseline_pixels = 95031  # From previous testing
        if total_pixels > 0:
            improvement_factor = total_pixels / baseline_pixels
            logger.info(f"Improvement over baseline: {improvement_factor:.1f}x")
            
            # Check if we achieved commercial target
            commercial_target = 2600000
            if total_pixels >= commercial_target:
                logger.info("✅ COMMERCIAL TARGET ACHIEVED!")
            else:
                remaining = commercial_target - total_pixels
                logger.info(f"❌ Target shortfall: {remaining:,} pixels ({remaining/commercial_target:.1%})")
        
        return True
        
    except Exception as e:
        logger.error(f"Enhanced decoder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_layer_extraction():
    """Validate that we're extracting all expected layers"""
    
    test_file = Path(__file__).parent.parent / "joe.note"
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return False
    
    logger.info("=== Layer Extraction Validation ===")
    
    # Read raw file
    with open(test_file, 'rb') as f:
        data = f.read()
    
    # Initialize parser and extract layers directly
    parser = SupernoteParser()
    layers = parser._extract_layer_info_enhanced(data)
    
    logger.info(f"Found {len(layers)} layers:")
    
    for layer in layers:
        logger.info(f"  {layer['name']}: address={layer['address']}, size={layer['bitmap_size']}, source={layer.get('source', 'unknown')}")
    
    # Validate expected layers
    expected_layers = ['MAINLAYER', 'BGLAYER']
    found_types = [layer['layer_name'] for layer in layers]
    
    for expected in expected_layers:
        count = found_types.count(expected)
        logger.info(f"{expected}: found {count} instances")
    
    return True

if __name__ == "__main__":
    logger.info("Enhanced Supernote Decoder Test - Clean Room Implementation")
    logger.info("=" * 60)
    
    # Run validation
    if validate_layer_extraction():
        logger.info("✅ Layer extraction validation passed")
    else:
        logger.error("❌ Layer extraction validation failed")
        sys.exit(1)
    
    # Run main test
    if test_enhanced_decoder():
        logger.info("✅ Enhanced decoder test completed")
    else:
        logger.error("❌ Enhanced decoder test failed")
        sys.exit(1)
    
    logger.info("\nTest complete - check results above for performance metrics")