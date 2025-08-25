#!/usr/bin/env python3
"""Analyze the actual RLE format in joe.note"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/src')

def analyze_rle_data():
    with open('/home/ed/ghost-writer/joe.note', 'rb') as f:
        data = f.read()
    
    # Get bitmap data from address 768 (Page 1 MAINLAYER)
    address = 768
    length = int.from_bytes(data[address:address+4], 'little')
    bitmap_data = data[address+4:address+4+length]
    
    print(f"Analyzing Page 1 MAINLAYER RLE data")
    print(f"Total size: {length:,} bytes")
    print("=" * 60)
    
    # Analyze first 100 bytes
    print("\nFirst 100 bytes (hex):")
    for i in range(0, min(100, len(bitmap_data)), 20):
        chunk = bitmap_data[i:i+20]
        hex_str = chunk.hex()
        # Format as pairs
        formatted = ' '.join(hex_str[j:j+2] for j in range(0, len(hex_str), 2))
        print(f"{i:04x}: {formatted}")
    
    # Count occurrences of each byte value
    print("\nByte value distribution (first 1000 bytes):")
    from collections import Counter
    counter = Counter(bitmap_data[:min(1000, len(bitmap_data))])
    
    # Group by ranges
    ranges = {
        "0x61-0x68 (RLE colors)": [b for b in range(0x61, 0x69)],
        "0xFF (special)": [0xFF],
        "0x80-0xFE (high bit)": [b for b in range(0x80, 0xFF)],
        "0x00-0x7F (normal)": [b for b in range(0x00, 0x80)],
    }
    
    for range_name, byte_values in ranges.items():
        count = sum(counter.get(b, 0) for b in byte_values)
        if count > 0:
            print(f"  {range_name}: {count} occurrences")
            # Show most common in this range
            common = [(b, counter[b]) for b in byte_values if counter.get(b, 0) > 0]
            common.sort(key=lambda x: x[1], reverse=True)
            for byte_val, cnt in common[:5]:
                print(f"    0x{byte_val:02x}: {cnt} times")

if __name__ == "__main__":
    analyze_rle_data()
