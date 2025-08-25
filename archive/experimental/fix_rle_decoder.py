#!/usr/bin/env python3
"""
Improved RLE decoder that properly handles spatial reconstruction
"""

import struct
from pathlib import Path
from PIL import Image
import numpy as np

def analyze_rle_structure(data: bytes) -> dict:
    """Analyze the RLE data structure to understand the format"""
    
    print(f"🔍 Analyzing RLE structure ({len(data)} bytes)")
    
    # Look for patterns in the data
    byte_counts = {}
    for b in data:
        byte_counts[b] = byte_counts.get(b, 0) + 1
    
    # Most common bytes (likely run lengths or pixel values)
    sorted_counts = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"📊 Most common bytes: {sorted_counts[:10]}")
    
    # Look for potential coordinate or control sequences
    patterns = {
        'zero_runs': [],
        'high_values': [],
        'coordinate_pairs': []
    }
    
    for i in range(len(data) - 1):
        if data[i] == 0:
            # Track zero runs (might be coordinate resets)
            patterns['zero_runs'].append(i)
        elif data[i] > 200:
            # Track high values (might be special markers)
            patterns['high_values'].append((i, data[i]))
        
        # Look for potential coordinate pairs
        if i < len(data) - 3:
            val1, val2 = data[i], data[i+1]
            if 0 < val1 < 100 and 0 < val2 < 100:
                patterns['coordinate_pairs'].append((i, val1, val2))
    
    print(f"📍 Zero positions: {len(patterns['zero_runs'])}")
    print(f"🔺 High values (>200): {len(patterns['high_values'])}")
    print(f"📐 Potential coordinate pairs: {len(patterns['coordinate_pairs'])}")
    
    return patterns

def decode_ratta_rle_improved(compressed_data: bytes, width: int = 1404, height: int = 1872) -> np.ndarray:
    """Improved RATTA_RLE decoder with proper spatial handling"""
    
    print(f"🎯 Improved RLE decoding ({len(compressed_data):,} bytes)")
    
    # Analyze structure first
    patterns = analyze_rle_structure(compressed_data)
    
    # Create output canvas
    output = np.full((height, width), 255, dtype=np.uint8)  # White background
    
    pos = 0
    pixels_written = 0
    
    # Try different decoding strategies
    strategies = [
        "coordinate_based",
        "block_based", 
        "scan_line"
    ]
    
    for strategy in strategies:
        print(f"\n🧪 Trying {strategy} strategy...")
        
        if strategy == "coordinate_based":
            result = decode_coordinate_based(compressed_data, width, height)
        elif strategy == "block_based":
            result = decode_block_based(compressed_data, width, height)
        elif strategy == "scan_line":
            result = decode_scan_line(compressed_data, width, height)
        
        non_white = np.sum(result < 255)
        if non_white > 0:
            print(f"✅ {strategy} produced {non_white:,} non-white pixels")
            return result
        else:
            print(f"❌ {strategy} produced no content")
    
    return output

def decode_coordinate_based(data: bytes, width: int, height: int) -> np.ndarray:
    """Try coordinate-based decoding"""
    
    output = np.full((height, width), 255, dtype=np.uint8)
    pos = 0
    
    while pos < len(data) - 3:
        try:
            # Try interpreting as [x, y, length, value]
            x = data[pos]
            y = data[pos + 1] 
            length = data[pos + 2]
            value = data[pos + 3]
            
            # Scale coordinates if needed
            actual_x = int(x * width / 255)
            actual_y = int(y * height / 255)
            
            if actual_x < width and actual_y < height and length > 0 and length < 50:
                # Draw horizontal run
                for i in range(min(length, width - actual_x)):
                    if actual_x + i < width:
                        output[actual_y, actual_x + i] = value
            
            pos += 4
            
        except:
            pos += 1
    
    return output

def decode_block_based(data: bytes, width: int, height: int) -> np.ndarray:
    """Try block-based decoding"""
    
    output = np.full((height, width), 255, dtype=np.uint8)
    pos = 0
    
    # Divide into blocks
    block_size = 64
    
    while pos < len(data) - 1:
        try:
            count = data[pos]
            value = data[pos + 1]
            
            if count > 0 and count < 100:
                # Find next available block position
                block_y = (pos // 100) % (height // block_size)
                block_x = (pos // 10) % (width // block_size)
                
                start_y = block_y * block_size
                start_x = block_x * block_size
                
                # Fill block area
                for i in range(min(count, block_size * block_size)):
                    y = start_y + (i // block_size)
                    x = start_x + (i % block_size)
                    
                    if x < width and y < height:
                        output[y, x] = value
            
            pos += 2
            
        except:
            pos += 1
    
    return output

def decode_scan_line(data: bytes, width: int, height: int) -> np.ndarray:
    """Try scan-line based decoding with proper distribution"""
    
    output = np.full((height, width), 255, dtype=np.uint8)
    pos = 0
    
    # Calculate how to distribute compressed rows across full height
    compressed_height = len(data) // (width // 10)  # Estimate compressed height
    scale_factor = height / max(1, compressed_height)
    
    current_y = 0
    x = 0
    
    while pos < len(data) - 1 and current_y < height:
        try:
            count = data[pos]
            value = data[pos + 1]
            
            if count > 0 and count < 200:
                # Write pixels with proper Y scaling
                for i in range(count):
                    actual_y = int(current_y * scale_factor)
                    
                    if actual_y < height and x < width:
                        output[actual_y, x] = value
                        x += 1
                        
                        if x >= width:
                            x = 0
                            current_y += 1
                            if current_y >= height / scale_factor:
                                break
            
            pos += 2
            
        except:
            pos += 1
    
    return output

def process_all_layers():
    """Process all layers with improved decoder"""
    
    file_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Layer information
    layers = [
        {"name": "Page1_MainLayer", "pos": 1091, "bitmap_size": 758},
        {"name": "Page1_Background", "pos": 1222, "bitmap_size": 430},
        {"name": "Page2_MainLayer", "pos": 9408, "bitmap_size": 9075},
        {"name": "Page2_Background", "pos": 9540, "bitmap_size": 430}
    ]
    
    for layer in layers:
        print(f"\n🎨 Processing {layer['name']} with improved decoder...")
        
        # Extract bitmap data
        start_pos = layer['pos'] + 100  # Skip metadata
        bitmap_data = data[start_pos:start_pos + layer['bitmap_size']]
        
        print(f"📊 Processing {len(bitmap_data):,} bytes")
        
        # Decode with improved algorithm
        decoded = decode_ratta_rle_improved(bitmap_data)
        
        # Save result
        img = Image.fromarray(decoded, mode='L')
        output_path = f"/home/ed/ghost-writer/fixed_{layer['name']}.png"
        img.save(output_path)
        
        # Check content
        non_white = np.sum(decoded < 255)
        print(f"✅ Saved to {output_path}")
        print(f"📈 Non-white pixels: {non_white:,} ({100*non_white/decoded.size:.2f}%)")

if __name__ == "__main__":
    process_all_layers()