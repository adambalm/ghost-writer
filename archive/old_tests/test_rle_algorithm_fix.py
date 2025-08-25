#!/usr/bin/env python3
"""
Test to demonstrate the critical RLE algorithm fix needed.
This compares our broken algorithm with the correct holder/queue approach.
"""

import numpy as np
from collections import deque

def decode_rle_broken(data, width, height):
    """Our current broken algorithm"""
    color_map = {0x61: 0, 0x62: 255, 0x63: 64, 0x64: 128, 0x65: 255, 0x66: 0, 0x67: 64, 0x68: 128}
    output = np.full((height, width), 255, dtype=np.uint8)
    pixel_idx = 0
    max_pixels = width * height
    
    i = 0
    while i < len(data) - 1 and pixel_idx < max_pixels:
        color_code = data[i]
        length_byte = data[i + 1]
        i += 2
        
        color = color_map.get(color_code, 255)
        
        if length_byte == 0xFF:
            pixel_count = 16384
        elif length_byte & 0x80:
            # WRONG - immediate calculation
            pixel_count = ((length_byte & 0x7F) + 1) * 128
        else:
            pixel_count = length_byte + 1
            
        for _ in range(min(pixel_count, max_pixels - pixel_idx)):
            row = pixel_idx // width
            col = pixel_idx % width
            output[row, col] = color
            pixel_idx += 1
    
    return output, pixel_idx

def decode_rle_correct(data, width, height):
    """Correct algorithm using holder/queue pattern from reference"""
    color_map = {0x61: 0, 0x62: 255, 0x63: 64, 0x64: 128, 0x65: 255, 0x66: 0, 0x67: 64, 0x68: 128}
    
    expected_pixels = height * width
    uncompressed = bytearray()
    
    bin_iter = iter(data)
    try:
        holder = ()
        waiting = deque()
        debug_count = 0
        
        while True:
            colorcode = next(bin_iter)
            length = next(bin_iter)
            data_pushed = False
            debug_count += 1
            
            print(f"Debug {debug_count}: colorcode=0x{colorcode:02x}, length=0x{length:02x}, holder={holder}")
            
            if len(holder) > 0:
                (prev_colorcode, prev_length) = holder
                holder = ()
                if colorcode == prev_colorcode:
                    # Multi-byte length reconstruction
                    combined_length = 1 + length + (((prev_length & 0x7f) + 1) << 7)
                    print(f"  Combined same color: {combined_length} pixels")
                    waiting.append((colorcode, combined_length))
                    data_pushed = True
                else:
                    prev_length = ((prev_length & 0x7f) + 1) << 7
                    print(f"  Different color, flush holder: {prev_length} pixels")
                    waiting.append((prev_colorcode, prev_length))
            
            if not data_pushed:
                if length == 0xFF:
                    length = 16384  # SPECIAL_LENGTH
                    print(f"  Special FF marker: {length} pixels")
                    waiting.append((colorcode, length))
                    data_pushed = True
                elif length & 0x80 != 0:
                    # Hold for next iteration
                    print(f"  Holding data with 0x80 bit set")
                    holder = (colorcode, length)
                else:
                    length += 1
                    print(f"  Normal length: {length} pixels")
                    waiting.append((colorcode, length))
                    data_pushed = True
            
            # Process waiting queue
            while waiting:
                (colorcode, length) = waiting.popleft()
                color = color_map.get(colorcode, 255)
                print(f"  Processing: color=0x{colorcode:02x} -> {color}, length={length}")
                uncompressed.extend([color] * length)
                
    except StopIteration:
        # Handle final holder data
        if len(holder) > 0:
            (colorcode, length) = holder
            # Adjust tail length
            gap = expected_pixels - len(uncompressed)
            for i in reversed(range(8)):
                l = ((length & 0x7f) + 1) << i
                if l <= gap:
                    final_length = l
                    break
            else:
                final_length = 0
                
            if final_length > 0:
                color = color_map.get(colorcode, 255)
                uncompressed.extend([color] * final_length)
    
    # Convert to image array (limit to expected pixels)
    actual_pixels = min(len(uncompressed), expected_pixels)
    output = np.full((height, width), 255, dtype=np.uint8)
    
    if actual_pixels > 0:
        flat_data = np.array(uncompressed[:actual_pixels], dtype=np.uint8)
        for i in range(actual_pixels):
            row = i // width
            col = i % width
            if row < height and col < width:
                output[row, col] = flat_data[i]
    
    return output, len(uncompressed)

if __name__ == "__main__":
    # Test with RLE data containing the critical 0x80 patterns from joe.note
    test_data = bytes([
        0x62, 0x87, 0x62, 0x38,  # Critical holder pattern: 0x87 has 0x80 bit set
        0x62, 0x89, 0x62, 0x77,  # Another holder pattern: 0x89 has 0x80 bit set  
        0x61, 0x02,              # Simple pattern for comparison
        0x62, 0x89, 0x62, 0x76,  # More holder patterns
        0x61, 0x03,              # Simple pattern
    ])
    
    width, height = 1404, 1872
    
    print("Testing RLE Algorithm Fix")
    print("=" * 50)
    
    # Test broken algorithm
    broken_output, broken_pixels = decode_rle_broken(test_data, width, height)
    broken_content = np.sum(broken_output < 255)
    print(f"Broken Algorithm:")
    print(f"  Total pixels processed: {broken_pixels:,}")
    print(f"  Content pixels: {broken_content:,}")
    print(f"  Content percentage: {(broken_content/len(test_data*100)):.3f}%")
    
    # Test correct algorithm  
    correct_output, correct_pixels = decode_rle_correct(test_data, width, height)
    correct_content = np.sum(correct_output < 255)
    print(f"\nCorrect Algorithm:")
    print(f"  Total pixels processed: {correct_pixels:,}")
    print(f"  Content pixels: {correct_content:,}")
    print(f"  Content percentage: {(correct_content/len(test_data*100)):.3f}%")
    
    print(f"\nImprovement Factor: {correct_content/max(broken_content, 1):.1f}x")