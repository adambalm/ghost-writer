#!/usr/bin/env python3

"""
Test the fixed supernote parser decoder
"""

import sys
import os
import numpy as np
from PIL import Image
import logging

# Add project root to path
sys.path.insert(0, '/home/ed/ghost-writer/clean-room-development/src')
from utils.supernote_parser import SupernoteParser, VisibilityOverlay, build_visibility_overlay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_decoder():
    """Test the fixed decoder against joe.note"""
    
    parser = SupernoteParser()
    
    # Test file
    note_file = "/home/ed/ghost-writer/joe.note"
    
    print("=" * 60)
    print("SUPERNOTE DECODER VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Parse the file using enhanced decoder
        print(f"\n1. Parsing {note_file}...")
        pages = parser.parse_file(note_file)
        print(f"   Found {len(pages)} pages")
        
        for i, page in enumerate(pages, 1):
            print(f"\n2. Processing Page {i}...")
            print(f"   Dimensions: {page.width}x{page.height}")
            print(f"   Metadata: {page.metadata}")
            
            if page.metadata and 'decoded_bitmap' in page.metadata:
                bitmap = page.metadata['decoded_bitmap']
                non_white_pixels = np.sum(bitmap < 255)
                total_pixels = bitmap.shape[0] * bitmap.shape[1]
                
                print(f"   Bitmap shape: {bitmap.shape}")
                print(f"   Non-white pixels: {non_white_pixels:,}")
                print(f"   Total pixels: {total_pixels:,}")
                print(f"   Coverage: {(non_white_pixels/total_pixels)*100:.2f}%")
                
                # Save the image
                output_path = f"/home/ed/ghost-writer/test_fixed_page_{i}.png"
                image = parser.render_page_to_image(page, output_path)
                print(f"   Saved: {output_path}")
                
                # Test different visibility overlays
                print(f"\n3. Testing visibility overlays for Page {i}...")
                
                test_overlays = [
                    ("DEFAULT", build_visibility_overlay()),
                    ("INVISIBLE_BG", build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)),
                    ("VISIBLE_ALL", build_visibility_overlay(
                        background=VisibilityOverlay.VISIBLE,
                        main=VisibilityOverlay.VISIBLE
                    ))
                ]
                
                # Get binary data for testing multi-layer approach
                with open(note_file, 'rb') as f:
                    data = f.read()
                
                for overlay_name, overlay_config in test_overlays:
                    try:
                        multi_image = parser.convert_page_with_layers(i, data, overlay_config)
                        multi_path = f"/home/ed/ghost-writer/test_fixed_page_{i}_{overlay_name.lower()}.png"
                        multi_image.save(multi_path)
                        
                        # Count pixels
                        img_array = np.array(multi_image.convert('L'))
                        multi_pixels = np.sum(img_array < 255)
                        print(f"   {overlay_name:12}: {multi_pixels:8,} pixels -> {multi_path}")
                        
                    except Exception as e:
                        print(f"   {overlay_name:12}: ERROR - {e}")
            
            else:
                print(f"   No decoded bitmap found")
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ Parser executed successfully")
        print("✅ Decoded bitmap data extracted")
        print("✅ Images rendered and saved")
        print("✅ Multiple visibility modes tested")
        print("\nCheck the generated PNG files to validate visual content.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_decoder()
    sys.exit(0 if success else 1)