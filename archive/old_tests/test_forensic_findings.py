#!/usr/bin/env python3
"""
Test script to validate forensic findings about joe.note RLE decoder issues.

This script will:
1. Extract layer data from correct LAYERBITMAP addresses
2. Apply corrected RLE decoder algorithm  
3. Generate images showing the actual handwriting content
4. Compare pixel counts with sn2md extraction results
"""

import numpy as np
from PIL import Image
import logging
import struct

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_layer_data_correct(file_path: str):
    """Extract layer data using correct LAYERBITMAP address interpretation"""
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    logger.info(f"File size: {len(data):,} bytes")
    
    # Known layer addresses from forensic analysis
    layers = [
        {"name": "Page1_MAINLAYER", "address": 768},
        {"name": "Page1_BGLAYER", "address": 440}, 
        {"name": "Page2_MAINLAYER", "address": 847208}
    ]
    
    extracted_layers = []
    
    for layer in layers:
        address = layer['address']
        
        # Read 4-byte size field
        if address + 4 > len(data):
            logger.warning(f"Address {address} exceeds file size")
            continue
            
        size = int.from_bytes(data[address:address+4], 'little')
        data_start = address + 4
        
        if data_start + size > len(data):
            logger.warning(f"Layer {layer['name']}: data extends beyond file")
            continue
            
        # Extract actual RLE data
        rle_data = data[data_start:data_start + size]
        
        logger.info(f"Layer {layer['name']}: address={address}, size={size:,} bytes")
        logger.info(f"  First 20 bytes: {rle_data[:20].hex()}")
        
        # Count RLE command bytes (0x61-0x68)
        rle_commands = sum(1 for b in rle_data[:min(1000, len(rle_data))] if 0x61 <= b <= 0x68)
        logger.info(f"  RLE commands in first 1000 bytes: {rle_commands}")
        
        extracted_layers.append({
            'name': layer['name'],
            'data': rle_data,
            'size': size,
            'address': address
        })
    
    return extracted_layers

def decode_rle_corrected(compressed_data: bytes, width: int = 1404, height: int = 1872) -> np.ndarray:
    """Corrected RLE decoder based on supernotelib reference implementation"""
    
    if not compressed_data or len(compressed_data) < 2:
        logger.warning("Insufficient RLE data")
        return np.full((height, width), 255, dtype=np.uint8)
    
    logger.info(f"Decoding {len(compressed_data):,} bytes for {width}x{height}")
    
    # Color mapping from reference
    color_map = {
        0x61: 0,    # Black
        0x62: 255,  # White/Transparent
        0x63: 64,   # Dark gray  
        0x64: 128,  # Gray
        0x65: 255,  # White
        0x66: 0,    # Marker black
        0x67: 64,   # Marker dark gray
        0x68: 128,  # Marker gray
    }
    
    expected_pixels = width * height
    uncompressed = bytearray()
    
    bin_iter = iter(compressed_data)
    holder = ()
    waiting = []
    
    try:
        while True:
            colorcode = next(bin_iter)
            length = next(bin_iter)
            data_pushed = False
            
            # Process held data from previous iteration (CRITICAL)
            if len(holder) > 0:
                (prev_colorcode, prev_length) = holder
                holder = ()
                if colorcode == prev_colorcode:
                    # CRITICAL: Combine lengths using reference formula
                    length = 1 + length + (((prev_length & 0x7f) + 1) << 7)
                    waiting.append((colorcode, length))
                    data_pushed = True
                else:
                    # Different color: flush held data first
                    prev_length = ((prev_length & 0x7f) + 1) << 7
                    waiting.append((prev_colorcode, prev_length))
            
            # Process current command
            if not data_pushed:
                if length == 0xFF:
                    # Special marker for large blocks
                    length = 16384  # SPECIAL_LENGTH  
                    waiting.append((colorcode, length))
                    data_pushed = True
                elif length & 0x80 != 0:
                    # High bit set: hold for next iteration (CRITICAL)
                    holder = (colorcode, length)
                    # Will be processed in next loop iteration
                else:
                    # Normal length: immediate processing
                    length += 1
                    waiting.append((colorcode, length))
                    data_pushed = True
            
            # Process waiting queue (FIFO order)
            while waiting:
                (colorcode, length) = waiting.pop(0)
                color = color_map.get(colorcode, 255)
                
                # Prevent buffer overflow
                remaining_space = expected_pixels - len(uncompressed)
                actual_length = min(length, remaining_space)
                
                uncompressed.extend([color] * actual_length)
                
                if len(uncompressed) >= expected_pixels:
                    break
                    
    except StopIteration:
        # Handle final held data at end of stream
        if len(holder) > 0:
            (colorcode, length) = holder
            # Calculate final length to not exceed canvas
            gap = expected_pixels - len(uncompressed)
            for i in reversed(range(8)):
                l = ((length & 0x7f) + 1) << i
                if l <= gap:
                    final_length = l
                    break
            else:
                final_length = gap  # Use remaining space
                
            if final_length > 0:
                color = color_map.get(colorcode, 255)
                uncompressed.extend([color] * final_length)
    
    # Convert to image array
    actual_pixels = min(len(uncompressed), expected_pixels)
    output = np.full((height, width), 255, dtype=np.uint8)
    
    if actual_pixels > 0:
        for i in range(actual_pixels):
            row = i // width
            col = i % width
            if row < height and col < width:
                output[row, col] = uncompressed[i]
    
    non_white = np.sum(output < 255)
    total_pixels = width * height
    logger.info(f"Decoded {actual_pixels:,}/{total_pixels:,} pixels, {non_white:,} non-white ({non_white/total_pixels*100:.2f}%)")
    
    return output

def main():
    """Test corrected layer extraction and RLE decoding"""
    
    file_path = "/home/ed/ghost-writer/joe.note"
    
    logger.info("=== FORENSIC VALIDATION TEST ===")
    logger.info("Testing corrected layer extraction and RLE decoding")
    
    # Extract layers using correct addresses
    layers = extract_layer_data_correct(file_path)
    
    if not layers:
        logger.error("No layers extracted")
        return
    
    # Process each layer
    for i, layer in enumerate(layers):
        logger.info(f"\n--- Processing {layer['name']} ---")
        
        # Decode using corrected algorithm
        decoded_bitmap = decode_rle_corrected(layer['data'])
        
        # Save image
        output_path = f"forensic_test_{layer['name']}.png"
        img = Image.fromarray(decoded_bitmap, mode='L')
        img.save(output_path)
        
        logger.info(f"Saved decoded image: {output_path}")
        
        # Analyze content
        non_white_pixels = np.sum(decoded_bitmap < 255)
        if non_white_pixels > 0:
            min_val = np.min(decoded_bitmap[decoded_bitmap < 255])
            logger.info(f"  Content detected: {non_white_pixels:,} pixels, darkest value: {min_val}")
        else:
            logger.info("  No content detected (all white)")
    
    logger.info("\n=== FORENSIC VALIDATION COMPLETE ===")
    logger.info("Check generated PNG files for actual handwriting content")

if __name__ == "__main__":
    main()