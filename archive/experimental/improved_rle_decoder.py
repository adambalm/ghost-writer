#!/usr/bin/env python3
"""
Improved RLE decoder with better stroke rendering and post-processing
"""

import struct
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

def decode_ratta_rle_improved(compressed_data: bytes, width: int = 1404, height: int = 1872) -> np.ndarray:
    """Improved RATTA_RLE decoder with better spatial handling and stroke rendering"""
    
    output = np.full((height, width), 255, dtype=np.uint8)  # White background
    pos = 0
    
    print(f"🔍 Decoding {len(compressed_data):,} bytes with improved algorithm")
    
    # Try multiple decoding strategies and combine results
    strategies = [
        ("coordinate_based", decode_coordinate_strategy),
        ("run_length", decode_run_length_strategy),
        ("bitmap_chunks", decode_bitmap_chunks_strategy)
    ]
    
    best_result = None
    max_content = 0
    
    for strategy_name, strategy_func in strategies:
        try:
            result = strategy_func(compressed_data, width, height)
            non_white = np.sum(result < 255)
            
            print(f"   {strategy_name}: {non_white:,} pixels")
            
            if non_white > max_content:
                max_content = non_white
                best_result = result
                print(f"   ✅ New best: {strategy_name}")
                
        except Exception as e:
            print(f"   ❌ {strategy_name} failed: {e}")
    
    return best_result if best_result is not None else output

def decode_coordinate_strategy(data: bytes, width: int, height: int) -> np.ndarray:
    """Coordinate-based strategy with improved scaling"""
    
    output = np.full((height, width), 255, dtype=np.uint8)
    pos = 0
    
    while pos < len(data) - 3:
        try:
            # Pattern: [x, y, length, value]
            x = data[pos]
            y = data[pos + 1] 
            length = data[pos + 2]
            value = data[pos + 3]
            
            # Improved coordinate scaling - use full range
            actual_x = int((x / 255.0) * (width - 1))
            actual_y = int((y / 255.0) * (height - 1))
            
            # Validate and draw
            if (0 <= actual_x < width and 0 <= actual_y < height and 
                1 <= length <= 50 and value < 255):
                
                # Draw horizontal stroke with thickness
                for dx in range(min(length, width - actual_x)):
                    if actual_x + dx < width:
                        output[actual_y, actual_x + dx] = value
                        
                        # Add vertical thickness for better visibility
                        for dy in [-1, 1]:
                            y_pos = actual_y + dy
                            if 0 <= y_pos < height:
                                current_val = output[y_pos, actual_x + dx]
                                # Blend with existing content
                                output[y_pos, actual_x + dx] = min(current_val, value + 50)
            
            pos += 4
            
        except:
            pos += 1
    
    return output

def decode_run_length_strategy(data: bytes, width: int, height: int) -> np.ndarray:
    """Traditional run-length strategy with better distribution"""
    
    output = np.full((height, width), 255, dtype=np.uint8)
    pos = 0
    x, y = 0, 0
    
    while pos < len(data) - 1:
        try:
            count = data[pos]
            value = data[pos + 1]
            
            if 1 <= count <= 100 and value < 255:
                for _ in range(count):
                    if x < width and y < height:
                        output[y, x] = value
                        x += 1
                        if x >= width:
                            x = 0
                            y += 1
                            if y >= height:
                                break
            
            pos += 2
            
        except:
            pos += 1
    
    return output

def decode_bitmap_chunks_strategy(data: bytes, width: int, height: int) -> np.ndarray:
    """Decode as bitmap chunks with intelligent placement"""
    
    output = np.full((height, width), 255, dtype=np.uint8)
    
    # Try to identify repeating patterns that might be stroke data
    chunk_size = 4
    pos = 0
    
    # Place chunks in a grid pattern
    chunks_per_row = width // 64  # Assume 64px chunks
    chunk_height = 32
    
    chunk_row = 0
    chunk_col = 0
    
    while pos < len(data) - chunk_size:
        try:
            chunk = data[pos:pos + chunk_size]
            
            # Skip if all bytes are the same (likely padding)
            if len(set(chunk)) <= 1:
                pos += chunk_size
                continue
            
            # Calculate chunk position
            start_x = chunk_col * 64
            start_y = chunk_row * chunk_height
            
            if start_x < width - 64 and start_y < height - chunk_height:
                # Draw chunk data as small strokes
                for i, byte_val in enumerate(chunk):
                    if byte_val < 200:  # Only draw non-white values
                        x = start_x + (i % 8) * 8
                        y = start_y + (i // 8) * 4
                        
                        if x < width and y < height:
                            # Draw a small stroke
                            for dx in range(min(4, width - x)):
                                for dy in range(min(2, height - y)):
                                    if x + dx < width and y + dy < height:
                                        output[y + dy, x + dx] = byte_val
            
            # Move to next chunk position
            chunk_col += 1
            if chunk_col >= chunks_per_row:
                chunk_col = 0
                chunk_row += 1
            
            pos += chunk_size
            
        except:
            pos += 1
    
    return output

def post_process_image(image_array: np.ndarray) -> np.ndarray:
    """Post-process the decoded image for better readability"""
    
    # Convert to PIL for advanced processing
    img = Image.fromarray(image_array)
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)  # Increase contrast
    
    # Slightly blur to connect broken strokes
    img = img.filter(ImageFilter.BoxBlur(0.5))
    
    # Convert back to numpy
    result = np.array(img)
    
    # Final cleanup - ensure good contrast
    result = np.where(result < 200, result // 2, 255)  # Darken non-white pixels
    
    return result.astype(np.uint8)

def process_note_with_improved_decoder():
    """Process the note file with improved decoder"""
    
    print("🚀 Processing Note with Improved RLE Decoder")
    print("=" * 55)
    
    file_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Layer information from our previous analysis
    layers = [
        {"name": "Page1_MainLayer", "pos": 1091, "bitmap_size": 758},
        {"name": "Page2_MainLayer", "pos": 9408, "bitmap_size": 9075}
    ]
    
    for layer in layers:
        print(f"\n📄 Processing {layer['name']}...")
        
        # Extract bitmap data
        start_pos = layer['pos'] + 100  # Skip metadata
        bitmap_data = data[start_pos:start_pos + layer['bitmap_size']]
        
        print(f"   📊 Bitmap size: {len(bitmap_data):,} bytes")
        
        # Decode with improved algorithm
        decoded = decode_ratta_rle_improved(bitmap_data, 1404, 1872)
        
        # Post-process for better visibility
        processed = post_process_image(decoded)
        
        # Save both versions
        raw_path = f"/home/ed/ghost-writer/improved_{layer['name']}_raw.png"
        processed_path = f"/home/ed/ghost-writer/improved_{layer['name']}_processed.png"
        
        Image.fromarray(decoded).save(raw_path)
        Image.fromarray(processed).save(processed_path)
        
        # Analysis
        raw_content = np.sum(decoded < 255)
        processed_content = np.sum(processed < 255)
        
        print(f"   💾 Raw: {raw_path} ({raw_content:,} pixels)")
        print(f"   ✨ Processed: {processed_path} ({processed_content:,} pixels)")
        
        if processed_content > raw_content * 1.1:  # Significant improvement
            print(f"   🎉 Post-processing improved visibility by {((processed_content/raw_content-1)*100):.1f}%")

if __name__ == "__main__":
    process_note_with_improved_decoder()