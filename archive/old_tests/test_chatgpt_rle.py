#!/usr/bin/env python3
"""Test ChatGPT's RLE decoder implementation"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/src')

# ChatGPT's implementation
DEFAULT_PALETTE = {
    0x61: 0x00,  # black
    0x62: 0xFF,  # background
    0x63: 0x70,
    0x64: 0xA0,
    0x65: 0xC0,
    0x66: 0xD0,
    0x67: 0xE0,
    0x68: 0xF0,  # lightest
}

class RLEError(ValueError):
    pass

def _read_varlen_run_length(it):
    """
    Length encoding:
      - 0xFF: adds 0x4000 and continues.
      - Otherwise: adds (byte & 0x7F) + 1; if (byte & 0x80) is set, continue reading.
      - Stop when you read a non-0xFF byte whose 0x80 bit is clear.
    """
    total = 0
    while True:
        try:
            b = next(it)
        except StopIteration:
            raise RLEError("Unexpected EOF while reading length")
        
        if b == 0xFF:
            total += 0x4000
            continue
        total += (b & 0x7F) + 1
        if (b & 0x80) != 0:
            continue
        break
    return total

def decode_ratta_rle_chatgpt(rle_bytes, width, height, palette=None):
    """ChatGPT's RATTA_RLE decoder"""
    if palette is None:
        palette = DEFAULT_PALETTE

    total_pixels = width * height
    out = bytearray(total_pixels)
    it = iter(rle_bytes)
    pos = 0
    
    try:
        while pos < total_pixels:
            colorcode = next(it)
            run_len = _read_varlen_run_length(it)
            if run_len <= 0 or pos + run_len > total_pixels:
                raise RLEError(f"RLE overflow/underflow (pos={pos}, run={run_len}, total={total_pixels})")
            val = palette.get(colorcode, 0x00)  # unknown color -> black
            out[pos:pos+run_len] = bytes([val]) * run_len
            pos += run_len
    except StopIteration as e:
        raise RLEError("RLE underflow: unexpected EOF while reading run") from e
    
    return out

def test_implementations():
    # Read joe.note bitmap data
    with open('/home/ed/ghost-writer/joe.note', 'rb') as f:
        data = f.read()
    
    # Page 1 MAINLAYER
    address = 768
    length = int.from_bytes(data[address:address+4], 'little')
    bitmap_data = data[address+4:address+4+length]
    
    print(f"Testing on {length:,} bytes of RLE data")
    print("=" * 60)
    
    # Test 1: ChatGPT's decoder
    print("\n1. ChatGPT's RLE Decoder:")
    try:
        result = decode_ratta_rle_chatgpt(bitmap_data, 1404, 1872)
        import numpy as np
        arr = np.frombuffer(result, dtype=np.uint8).reshape((1872, 1404))
        non_white = np.sum(arr < 255)
        print(f"   Pixels decoded: {non_white:,}")
        print(f"   Total pixels: {len(result):,}")
        print(f"   Shape: {arr.shape}")
        
        # Check first few values
        print(f"   First 10 pixels: {list(result[:10])}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Our current decoder
    print("\n2. Our Current Decoder:")
    try:
        from utils.supernote_parser import SupernoteParser
        parser = SupernoteParser()
        result = parser._decode_ratta_rle(bitmap_data, 1404, 1872)
        non_white = np.sum(result < 255)
        print(f"   Pixels decoded: {non_white:,}")
        print(f"   Shape: {result.shape}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Analyze first few commands manually
    print("\n3. Manual Command Analysis:")
    print("   First 20 RLE commands:")
    for i in range(0, min(40, len(bitmap_data)), 2):
        if i+1 < len(bitmap_data):
            color = bitmap_data[i]
            length_byte = bitmap_data[i+1]
            
            # Apply ChatGPT's length logic
            if length_byte == 0xFF:
                decoded_len = "0x4000 (16384)"
            elif length_byte & 0x80:
                decoded_len = f"{((length_byte & 0x7F) + 1)}+continuation"
            else:
                decoded_len = f"{length_byte + 1}"
            
            color_name = {0x61: "BLACK", 0x62: "WHITE"}.get(color, f"0x{color:02x}")
            print(f"     [{i//2:2}] {color_name:5} × {decoded_len}")

if __name__ == "__main__":
    test_implementations()