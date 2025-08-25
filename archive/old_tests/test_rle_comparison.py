#!/usr/bin/env python3
"""Compare RLE decoding between our implementation and supernotelib"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')
sys.path.insert(0, '/home/ed/ghost-writer/supernote-tool')
sys.path.insert(0, '/home/ed/ghost-writer/src')

def test_rle_decoding():
    # Read the raw file
    with open('/home/ed/ghost-writer/joe.note', 'rb') as f:
        data = f.read()
    
    # Get Page 1 MAINLAYER bitmap data
    address = 768
    length = int.from_bytes(data[address:address+4], 'little')
    bitmap_data = data[address+4:address+4+length]
    
    print(f"Testing RLE decoding on {length:,} bytes")
    print("=" * 60)
    
    # Test 1: supernotelib decoder
    print("\n1. supernotelib RattaRleDecoder:")
    try:
        from supernotelib.decoder import RattaRleDecoder
        from supernotelib import color
        
        decoder = RattaRleDecoder()
        palette = color.DEFAULT_COLORPALETTE
        
        result, size, bpp = decoder.decode(bitmap_data, 1404, 1872, palette=palette)
        
        # Count non-white pixels
        import numpy as np
        if bpp == 8:
            arr = np.frombuffer(result, dtype=np.uint8).reshape((1872, 1404))
        else:
            arr = np.frombuffer(result, dtype=np.uint8).reshape((1872, 1404, 3))
        
        non_white = np.sum(arr < 255) if bpp == 8 else np.sum(np.any(arr < 255, axis=2))
        print(f"  Pixels decoded: {non_white:,}")
        print(f"  Output size: {size}")
        print(f"  Bits per pixel: {bpp}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 2: Our decoder
    print("\n2. Our custom decoder:")
    try:
        from utils.supernote_parser import SupernoteParser
        import numpy as np
        
        parser = SupernoteParser()
        result = parser._decode_ratta_rle(bitmap_data, 1404, 1872)
        
        non_white = np.sum(result < 255)
        print(f"  Pixels decoded: {non_white:,}")
        print(f"  Output shape: {result.shape}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 3: Simple manual decode to understand the format
    print("\n3. Manual analysis:")
    pixels_from_commands = 0
    i = 0
    commands_processed = 0
    
    while i < min(1000, len(bitmap_data) - 1):
        color = bitmap_data[i]
        length = bitmap_data[i+1]
        
        if length == 0xFF:
            pixels = 16384
        elif length & 0x80:
            pixels = ((length & 0x7F) + 1) * 128
        else:
            pixels = length + 1
        
        pixels_from_commands += pixels
        commands_processed += 1
        i += 2
    
    print(f"  Commands in first 1000 bytes: {commands_processed}")
    print(f"  Pixels from those commands: {pixels_from_commands:,}")
    print(f"  Expected total pixels: {1404 * 1872:,}")

if __name__ == "__main__":
    test_rle_decoding()
