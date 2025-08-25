#!/usr/bin/env python3
"""
Extract and decode RATTA_RLE bitmap data from the new format
"""

import struct
from pathlib import Path
from PIL import Image
import numpy as np

def find_bitmap_data(data: bytes, layer_start: int) -> tuple:
    """Find the actual bitmap data after layer metadata"""
    
    # Look for the end of metadata (find binary data start)
    pos = layer_start
    while pos < len(data):
        # Look for patterns that indicate start of binary data
        if (pos + 4 < len(data) and 
            data[pos:pos+4] not in [b'<LAY', b'TYPE', b'PROT', b'NAME', b'PATH', b'BITM', b'VECT', b'RECO']):
            
            # Check if we're in a binary section
            chunk = data[pos:pos+16]
            if any(b < 32 or b > 126 for b in chunk if b != 0):  # Non-ASCII binary data
                return pos, data[pos:]
        pos += 1
    
    return -1, b''

def decode_ratta_rle(compressed_data: bytes, width: int = 1404, height: int = 1872) -> np.ndarray:
    """Attempt to decode RATTA_RLE compressed bitmap data"""
    
    print(f"🔍 Decoding {len(compressed_data):,} bytes of RLE data")
    
    # Try to decode RLE format
    output = np.full((height, width), 255, dtype=np.uint8)  # Start with white
    
    pos = 0
    y, x = 0, 0
    pixels_written = 0
    
    while pos < len(compressed_data) and y < height:
        if pos + 1 >= len(compressed_data):
            break
            
        # Try different RLE patterns
        try:
            # Pattern 1: [count][value] 
            count = compressed_data[pos]
            value = compressed_data[pos + 1] if pos + 1 < len(compressed_data) else 255
            
            # Skip if count seems unreasonable
            if count > 200:
                pos += 1
                continue
                
            # Write pixels
            for _ in range(count):
                if x < width and y < height:
                    output[y, x] = value
                    pixels_written += 1
                    x += 1
                    if x >= width:
                        x = 0
                        y += 1
                        if y >= height:
                            break
            
            pos += 2
            
        except Exception:
            pos += 1
    
    print(f"📊 Wrote {pixels_written:,} pixels")
    return output

def extract_and_decode_layers(file_path: str):
    """Extract and decode all layers from the file"""
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Layer information from our analysis
    layers = [
        {"name": "Page1_MainLayer", "pos": 1091, "bitmap_size": 758},
        {"name": "Page1_Background", "pos": 1222, "bitmap_size": 430},
        {"name": "Page2_MainLayer", "pos": 9408, "bitmap_size": 9075},
        {"name": "Page2_Background", "pos": 9540, "bitmap_size": 430}
    ]
    
    for i, layer in enumerate(layers):
        print(f"\\n🎨 Processing {layer['name']}...")
        
        # Find bitmap data start
        bitmap_start, bitmap_data = find_bitmap_data(data, layer['pos'])
        
        if bitmap_start == -1:
            print(f"❌ Could not find bitmap data")
            continue
            
        # Take the expected amount of data
        bitmap_size = layer['bitmap_size']
        actual_data = bitmap_data[:bitmap_size]
        
        print(f"📊 Bitmap data starts at {bitmap_start:,}, size: {len(actual_data):,} bytes")
        
        # Show first few bytes
        hex_preview = ' '.join(f'{b:02x}' for b in actual_data[:16])
        print(f"🔍 First 16 bytes: {hex_preview}")
        
        # Try to decode
        try:
            decoded = decode_ratta_rle(actual_data)
            
            # Convert to PIL image
            img = Image.fromarray(decoded, mode='L')
            
            # Save as PNG
            output_path = f"/home/ed/ghost-writer/decoded_{layer['name']}.png"
            img.save(output_path)
            
            # Check if it has content
            non_white = np.sum(decoded < 255)
            total = decoded.size
            print(f"✅ Saved to {output_path}")
            print(f"📈 Non-white pixels: {non_white:,} / {total:,} ({100*non_white/total:.2f}%)")
            
        except Exception as e:
            print(f"❌ Decode error: {e}")

if __name__ == "__main__":
    extract_and_decode_layers("/home/ed/ghost-writer/temp_20250807_035920.note")