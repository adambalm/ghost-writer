#!/usr/bin/env python3
"""
Extract and decode bitmap data from joe.note using correct offsets
"""

import numpy as np
from PIL import Image
from pathlib import Path

def analyze_rle_data(data: bytes, max_samples: int = 20):
    """Analyze RLE data patterns"""
    print("  RLE Data Analysis:")
    
    # Look at the actual byte patterns
    unique_values = {}
    coordinate_patterns = []
    
    for i in range(0, min(len(data), max_samples * 4), 4):
        if i + 3 < len(data):
            b1, b2, b3, b4 = data[i:i+4]
            coordinate_patterns.append((b1, b2, b3, b4))
            
            # Track unique values in each position
            for pos, val in enumerate([b1, b2, b3, b4]):
                if pos not in unique_values:
                    unique_values[pos] = set()
                unique_values[pos].add(val)
    
    # Print statistics
    for pos in range(4):
        if pos in unique_values:
            vals = unique_values[pos]
            print(f"    Byte {pos}: {len(vals)} unique values, range {min(vals)}-{max(vals)}")
    
    # Print first few patterns
    print(f"\n  First {min(5, len(coordinate_patterns))} tuples:")
    for i, (b1, b2, b3, b4) in enumerate(coordinate_patterns[:5]):
        print(f"    [{b1:3d}, {b2:3d}, {b3:3d}, {b4:3d}] = {b1:02x} {b2:02x} {b3:02x} {b4:02x}")
    
    return coordinate_patterns

def decode_with_pattern_analysis(data: bytes, width: int, height: int):
    """Decode RLE with pattern-based interpretation"""
    
    # Analyze the data first
    patterns = analyze_rle_data(data, 100)
    
    # Look for common patterns that might indicate encoding type
    # Check if byte positions have specific ranges
    
    output = np.full((height, width), 255, dtype=np.uint8)
    
    # Try decoding based on observed patterns
    # Pattern observation: byte 2 often has value 0, byte 4 often 0, 97 (0x61), or 98 (0x62)
    # This suggests a different encoding scheme
    
    pos = 0
    current_x = 0
    current_y = 0
    
    while pos < len(data) - 3:
        b1 = data[pos]
        b2 = data[pos + 1]
        b3 = data[pos + 2]
        b4 = data[pos + 3]
        
        # Hypothesis: b4 might be a command byte
        # 0x61 (97) and 0x62 (98) appear frequently
        
        if b4 == 0x61:  # Possible pen down command
            # b1 might be x offset, b3 might be y position
            x = b1
            y = b3
            
            # Scale to page coordinates
            actual_x = int(x * width / 255) if x > 0 else current_x
            actual_y = int(y * height / 255) if y > 0 else current_y
            
            if 0 <= actual_x < width and 0 <= actual_y < height:
                # Draw a stroke segment
                length = min(b2, 10) if b2 > 0 else 1
                for i in range(length):
                    if actual_x + i < width:
                        output[actual_y, actual_x + i] = 0  # Black ink
                
                current_x = actual_x + length
                current_y = actual_y
                
        elif b4 == 0x62:  # Possible move command
            # Update position without drawing
            if b1 > 0:
                current_x = int(b1 * width / 255)
            if b3 > 0:
                current_y = int(b3 * height / 255)
        
        elif b4 == 0:  # Possible ink/stroke data
            # Traditional RLE: position and length
            if b1 > 0 and b3 > 0:
                x = int(b1 * width / 255)
                y = int(b3 * height / 255)
                length = min(b2, 50) if b2 > 0 else 1
                
                if 0 <= x < width and 0 <= y < height:
                    for i in range(min(length, width - x)):
                        output[y, x + i] = 0
        
        pos += 4
    
    return output

def extract_and_decode_bitmaps():
    """Extract bitmap data using discovered offsets and decode"""
    
    note_path = Path("/home/ed/ghost-writer/joe.note")
    
    with open(note_path, 'rb') as f:
        data = f.read()
    
    print("=" * 60)
    print("BITMAP EXTRACTION AND DECODING")
    print("=" * 60)
    
    # Test data extraction at known working offsets
    test_layers = [
        (1091, 758, "Page1_MainLayer"),
        (1222, 430, "Page1_Background"),
        (9408, 9075, "Page2_MainLayer"),
        (9540, 430, "Page2_Background")
    ]
    
    for offset, size, name in test_layers:
        print(f"\n{name}:")
        print(f"  Offset: {offset} (0x{offset:08x})")
        print(f"  Size: {size} bytes")
        
        if offset + size <= len(data):
            bitmap_data = data[offset:offset + size]
            
            # Decode the bitmap
            decoded = decode_with_pattern_analysis(bitmap_data, 1404, 1872)
            
            # Calculate statistics
            non_white = np.sum(decoded < 255)
            print(f"\n  Decoded Statistics:")
            print(f"    Non-white pixels: {non_white:,}")
            print(f"    Coverage: {(non_white / (1404 * 1872)) * 100:.2f}%")
            
            # Save the decoded image
            img = Image.fromarray(decoded, mode='L')
            output_path = f"/home/ed/ghost-writer/extracted_{name}.png"
            img.save(output_path)
            print(f"    Saved to: {output_path}")
        else:
            print(f"  ERROR: Offset + size exceeds file size")
    
    # Now let's try to find these offsets dynamically
    print("\n" + "=" * 60)
    print("DYNAMIC OFFSET DETECTION")
    print("=" * 60)
    
    # Search for patterns that indicate layer data
    # Looking for MAINLAYER and BGLAYER position markers with their actual offsets
    
    # Method: Find <MAINLAYER:number> pattern
    import re
    
    pattern = rb'<(MAINLAYER|BGLAYER|LAYER\d+):(\d+)>'
    matches = re.finditer(pattern, data)
    
    print("\nFound layer offset markers:")
    for match in matches:
        layer_name = match.group(1).decode('ascii')
        offset = int(match.group(2).decode('ascii'))
        
        if offset > 0 and offset < len(data):
            print(f"  {layer_name}: offset {offset} (0x{offset:08x})")
            
            # Check what's at that offset
            if offset + 4 < len(data):
                # This offset points to the layer metadata, not the bitmap data
                # The bitmap data is typically a bit further
                
                # Look for the actual bitmap start after this position
                # It usually starts after a size indicator
                metadata_start = offset
                
                # Read 4 bytes as potential size indicator
                size_bytes = data[offset:offset + 4]
                if len(size_bytes) == 4:
                    # Try little-endian interpretation
                    potential_size = int.from_bytes(size_bytes[:2], 'little')
                    print(f"    Potential size indicator: {potential_size}")
                    
                    # The actual bitmap might start after the metadata header
                    # Look for the end of metadata (closing bracket)
                    search_end = min(offset + 200, len(data))
                    bracket_pos = data.find(b'>', offset)
                    
                    if bracket_pos != -1 and bracket_pos < search_end:
                        bitmap_start = bracket_pos + 1
                        # Check if next byte is '}' (end of metadata block)
                        if bitmap_start < len(data) and data[bitmap_start] == ord('}'):
                            bitmap_start += 1
                        
                        print(f"    Likely bitmap start: {bitmap_start} (0x{bitmap_start:08x})")
                        
                        # Sample the data
                        if bitmap_start + 12 < len(data):
                            sample = data[bitmap_start:bitmap_start + 12]
                            print(f"    Sample: {' '.join(f'{b:02x}' for b in sample)}")

if __name__ == "__main__":
    extract_and_decode_bitmaps()