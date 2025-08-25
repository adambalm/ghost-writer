#!/usr/bin/env python3
"""
Test the fixed RLE decoder with the actual joe.note file.
This should extract hundreds of thousands of content pixels instead of just 911.
"""

import sys
sys.path.append('/home/ed/ghost-writer/src')

from utils.supernote_parser import SupernoteParser
import numpy as np
import logging

# Set up logging to see the results
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_fixed_decoder():
    print("Testing Fixed RLE Decoder")
    print("=" * 50)
    
    # Test with joe.note
    from pathlib import Path
    parser = SupernoteParser()
    pages = parser.parse_file(Path('/home/ed/ghost-writer/joe.note'))
    
    if pages:
        for i, page in enumerate(pages):
            print(f"\nPage {i+1} (ID: {page.page_id}):")
            
            for layer in page.layers:
                if layer.decoded_image is not None:
                    image = layer.decoded_image
                    content_pixels = np.sum(image < 255)
                    total_pixels = image.size
                    percentage = (content_pixels / total_pixels) * 100
                    
                    print(f"  {layer.name}:")
                    print(f"    Content pixels: {content_pixels:,}")
                    print(f"    Total pixels: {total_pixels:,}")
                    print(f"    Content percentage: {percentage:.3f}%")
                    print(f"    Canvas size: {image.shape}")
                    
                    # Save test image for visual verification
                    if layer.name == 'MAINLAYER':
                        from PIL import Image
                        pil_image = Image.fromarray(image)
                        filename = f'/home/ed/ghost-writer/test_fixed_decoder_page_{i+1}.png'
                        pil_image.save(filename)
                        print(f"    Saved: {filename}")
    else:
        print("Failed to parse pages")

if __name__ == "__main__":
    test_fixed_decoder()