#!/usr/bin/env python3
"""
Properly decode Supernote RLE format based on pattern analysis
"""

import numpy as np
from PIL import Image
from pathlib import Path
import struct

def analyze_marker_patterns(data: bytes):
    """Analyze the meaning of 0x61 and 0x62 markers"""
    
    print("Analyzing marker patterns (0x61 and 0x62)...")
    
    # Count occurrences
    marker_61_count = 0
    marker_62_count = 0
    other_count = 0
    
    # Analyze context around markers
    marker_61_contexts = []
    marker_62_contexts = []
    
    pos = 0
    while pos < len(data) - 3:
        b1, b2, b3, b4 = data[pos:pos+4]
        
        if b4 == 0x61:
            marker_61_count += 1
            if len(marker_61_contexts) < 10:
                marker_61_contexts.append((b1, b2, b3))
        elif b4 == 0x62:
            marker_62_count += 1
            if len(marker_62_contexts) < 10:
                marker_62_contexts.append((b1, b2, b3))
        else:
            other_count += 1
        
        pos += 4
    
    total_tuples = (marker_61_count + marker_62_count + other_count)
    
    print(f"  0x61 markers: {marker_61_count} ({marker_61_count/total_tuples*100:.1f}%)")
    print(f"  0x62 markers: {marker_62_count} ({marker_62_count/total_tuples*100:.1f}%)")
    print(f"  Other values: {other_count} ({other_count/total_tuples*100:.1f}%)")
    
    print(f"\n  Sample 0x61 contexts (b1, b2, b3):")
    for ctx in marker_61_contexts[:5]:
        print(f"    {ctx}")
    
    print(f"\n  Sample 0x62 contexts (b1, b2, b3):")
    for ctx in marker_62_contexts[:5]:
        print(f"    {ctx}")

def decode_supernote_rle(data: bytes, width: int, height: int, debug: bool = False):
    """
    Decode Supernote RLE format based on reverse engineering
    
    Theory: The format uses a state machine with command bytes:
    - 0x61: Start of stroke/pen down
    - 0x62: Movement/continuation
    - Other: Direct pixel data or end markers
    """
    
    output = np.full((height, width), 255, dtype=np.uint8)
    
    pos = 0
    stroke_active = False
    current_x = 0
    current_y = 0
    
    strokes_decoded = 0
    pixels_written = 0
    
    while pos < len(data) - 3:
        b1, b2, b3, b4 = data[pos:pos+4]
        
        # Interpret based on the 4th byte (command/marker)
        if b4 == 0x61:  # Start stroke marker
            # b1 appears to be stroke ID or type
            # b2 and b3 might be coordinates or offsets
            stroke_active = True
            strokes_decoded += 1
            
            # Try interpreting b2 and b3 as coordinates
            # They often have values like 0x0f, 0x1f, 0x2f, etc. (multiples of 16 - 1)
            # This suggests they might be block coordinates
            
            if b2 > 0:
                # Interpret as block coordinate (16-pixel blocks)
                current_x = ((b2 + 1) * 16) % width
            
            if b3 > 0:
                # Similar for y
                current_y = ((b3 + 1) * 8) % height  # Smaller blocks vertically?
            
            if debug and strokes_decoded <= 5:
                print(f"  Stroke {strokes_decoded}: marker 0x61, b1={b1}, pos=({current_x},{current_y})")
            
        elif b4 == 0x62:  # Continuation/data marker
            # b1 and b2 appear to be constant (0x89, 0x62 frequently)
            # b3 might be the actual coordinate or length
            
            if stroke_active and b3 > 0:
                # Interpret b3 as y-coordinate (scaled)
                y = int(b3 * height / 128)  # Different scaling factor
                
                # Draw a horizontal line segment
                if 0 <= y < height:
                    # Draw several pixels to make strokes visible
                    for dx in range(20):  # Hypothesis: fixed-length segments
                        x = (current_x + dx) % width
                        if 0 <= x < width:
                            output[y, x] = 0  # Black
                            pixels_written += 1
                    
                    current_x = (current_x + 20) % width
            
        elif b4 == 0x00:  # Possible data or end marker
            # When b4 is 0, other bytes might contain position/length info
            if b1 > 0 and b1 < 250 and b3 > 0 and b3 < 250:
                # Direct coordinate mode
                x = int(b1 * width / 256)
                y = int(b3 * height / 256)
                length = min(b2, 20) if b2 > 0 else 1
                
                if 0 <= x < width and 0 <= y < height:
                    for i in range(length):
                        if x + i < width:
                            output[y, x + i] = 0
                            pixels_written += 1
            
            stroke_active = False
            
        elif b4 >= 0xef:  # High values might be special
            # These might indicate jumps or mode changes
            if b2 == 0x00:
                # Possible position update
                if b1 > 0:
                    current_x = int(b1 * width / 256)
                if b3 > 0:
                    current_y = int(b3 * height / 256)
        
        pos += 4
    
    if debug:
        print(f"  Total strokes: {strokes_decoded}")
        print(f"  Total pixels: {pixels_written}")
    
    return output

def decode_alternative_interpretation(data: bytes, width: int, height: int):
    """
    Alternative interpretation: Treat as coordinate pairs with run-length
    """
    
    output = np.full((height, width), 255, dtype=np.uint8)
    
    # Theory: The frequent 0x62 0x89 pattern might be a separator
    # Split data by this pattern
    
    separator = bytes([0x62, 0x89])
    segments = data.split(separator)
    
    print(f"  Found {len(segments)} segments using 0x62 0x89 separator")
    
    for seg_idx, segment in enumerate(segments[:10]):  # Process first 10 segments
        if len(segment) < 2:
            continue
        
        # Each segment might encode a stroke
        for i in range(0, len(segment) - 1, 2):
            b1 = segment[i]
            b2 = segment[i + 1] if i + 1 < len(segment) else 0
            
            # Interpret as x,y coordinates
            x = int(b1 * width / 256)
            y = int(b2 * height / 256)
            
            if 0 <= x < width and 0 <= y < height:
                # Draw a small area to make it visible
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            output[ny, nx] = 0
    
    return output

def test_decoding_methods():
    """Test different decoding methods on joe.note"""
    
    note_path = Path("/home/ed/ghost-writer/joe.note")
    
    with open(note_path, 'rb') as f:
        data = f.read()
    
    print("=" * 60)
    print("TESTING RLE DECODING METHODS")
    print("=" * 60)
    
    # Test layers with known offsets
    test_cases = [
        (1091, 758, "Page1_MainLayer"),
        (9408, 9075, "Page2_MainLayer"),
    ]
    
    for offset, size, name in test_cases:
        print(f"\n{name}:")
        print(f"  Extracting {size} bytes from offset {offset}")
        
        if offset + size <= len(data):
            bitmap_data = data[offset:offset + size]
            
            # Analyze markers
            analyze_marker_patterns(bitmap_data)
            
            # Method 1: State machine decoding
            print("\n  Method 1: State Machine Decoding")
            decoded1 = decode_supernote_rle(bitmap_data, 1404, 1872, debug=True)
            non_white1 = np.sum(decoded1 < 255)
            print(f"    Non-white pixels: {non_white1:,}")
            
            img1 = Image.fromarray(decoded1, mode='L')
            img1.save(f"/home/ed/ghost-writer/decoded_method1_{name}.png")
            
            # Method 2: Alternative interpretation
            print("\n  Method 2: Segment-based Decoding")
            decoded2 = decode_alternative_interpretation(bitmap_data, 1404, 1872)
            non_white2 = np.sum(decoded2 < 255)
            print(f"    Non-white pixels: {non_white2:,}")
            
            img2 = Image.fromarray(decoded2, mode='L')
            img2.save(f"/home/ed/ghost-writer/decoded_method2_{name}.png")
            
            # Method 3: Combine both images to see all detected content
            print("\n  Method 3: Combined Output")
            combined = np.minimum(decoded1, decoded2)  # Take darker pixel from each
            non_white3 = np.sum(combined < 255)
            print(f"    Non-white pixels: {non_white3:,}")
            
            img3 = Image.fromarray(combined, mode='L')
            img3.save(f"/home/ed/ghost-writer/decoded_combined_{name}.png")
            
            print(f"\n  Target (sn2md): ~2,800,000 pixels")
            print(f"  Current best: {max(non_white1, non_white2, non_white3):,} pixels")
            print(f"  Achievement: {max(non_white1, non_white2, non_white3)/2800000*100:.2f}%")

if __name__ == "__main__":
    test_decoding_methods()