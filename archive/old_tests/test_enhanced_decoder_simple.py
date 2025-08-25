#!/usr/bin/env python3
"""
Simple test script for the enhanced clean room decoder
Just processes a note file and shows what actually happens

IMPORTANT: Must run with virtual environment activated:
source .venv/bin/activate && python3 test_enhanced_decoder_simple.py
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def check_virtual_env():
    """Check if virtual environment is activated"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Virtual environment: ACTIVATED")
        return True
    else:
        print("ERROR: Virtual environment NOT activated")
        print("Please run: source .venv/bin/activate && python3 test_enhanced_decoder_simple.py")
        return False

def test_enhanced_decoder():
    """Test the enhanced decoder on joe.note"""
    
    print("Testing Enhanced Clean Room Decoder")
    print("=" * 40)
    
    # Check for test file
    test_file = project_root / "joe.note"
    if not test_file.exists():
        print(f"Error: {test_file} not found")
        return False
    
    print(f"Test file: {test_file}")
    print(f"File size: {test_file.stat().st_size:,} bytes")
    
    try:
        # Import enhanced parser
        from src.utils.supernote_parser_enhanced import SupernoteParser
        print("Enhanced parser imported successfully")
        
        # Initialize parser
        parser = SupernoteParser()
        print("Parser initialized")
        
        # Parse file
        print("Processing file...")
        pages = parser.parse_file(test_file)
        
        if not pages:
            print("No pages extracted")
            return False
        
        print(f"Extracted {len(pages)} pages")
        
        # Analyze results
        total_pixels = 0
        total_content = 0
        
        for i, page in enumerate(pages, 1):
            print(f"\nPage {i}:")
            print(f"  Dimensions: {page.width}x{page.height}")
            print(f"  Parser: {page.metadata.get('parser', 'unknown')}")
            
            if 'decoded_bitmap' in page.metadata:
                bitmap = page.metadata['decoded_bitmap']
                page_pixels = bitmap.size if hasattr(bitmap, 'size') else (page.width * page.height)
                content_pixels = (bitmap < 255).sum() if hasattr(bitmap, 'sum') else 0
                
                total_pixels += page_pixels
                total_content += content_pixels
                
                print(f"  Total pixels: {page_pixels:,}")
                print(f"  Content pixels: {content_pixels:,}")
                print(f"  Content ratio: {content_pixels/page_pixels:.4f}")
            else:
                print("  No decoded bitmap found")
        
        print(f"\nSummary:")
        print(f"Total pixels extracted: {total_pixels:,}")
        print(f"Total content pixels: {total_content:,}")
        
        # Compare to baseline
        baseline = 95031
        if total_pixels > baseline:
            improvement = total_pixels / baseline
            print(f"Improvement over baseline: {improvement:.1f}x")
        
        return total_pixels > 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if not check_virtual_env():
        sys.exit(1)
    
    success = test_enhanced_decoder()
    if success:
        print("\nTest completed - check results above")
    else:
        print("\nTest failed")
        sys.exit(1)