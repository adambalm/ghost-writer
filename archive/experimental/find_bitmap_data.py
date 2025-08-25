#!/usr/bin/env python3
"""
Find the actual bitmap data start positions in joe.note
"""

import struct
from pathlib import Path

def find_bitmap_positions(data: bytes):
    """Find actual bitmap data positions using multiple strategies"""
    
    print("FINDING ACTUAL BITMAP DATA POSITIONS")
    print("=" * 50)
    
    # Strategy 1: Look for LAYERBITMAP tags and their values
    print("\n1. LAYERBITMAP Tags:")
    pos = 0
    while True:
        idx = data.find(b"<LAYERBITMAP:", pos)
        if idx == -1:
            break
        
        end = data.find(b">", idx + 13)
        if end != -1:
            try:
                size_str = data[idx + 13:end].decode('ascii')
                size = int(size_str)
                print(f"   Position 0x{idx:08x}: LAYERBITMAP size = {size}")
                
                # The actual data likely starts after the closing tag
                # Look for the end of the metadata section (typically ">}")
                metadata_end = data.find(b">}", end)
                if metadata_end != -1:
                    potential_start = metadata_end + 2
                    print(f"     Potential data start: 0x{potential_start:08x}")
                    
                    # Sample the data at this position
                    if potential_start + 16 < len(data):
                        sample = data[potential_start:potential_start + 16]
                        print(f"     Sample bytes: {' '.join(f'{b:02x}' for b in sample)}")
                        
                        # Check if this looks like bitmap data (not ASCII)
                        ascii_count = sum(1 for b in sample if 32 <= b <= 126)
                        if ascii_count < 8:  # Less than half ASCII = likely binary data
                            print(f"     ✓ Looks like binary data (non-ASCII)")
                        else:
                            print(f"     ✗ Looks like text/metadata")
                
            except Exception as e:
                print(f"   Error parsing at 0x{idx:08x}: {e}")
        
        pos = idx + 1
    
    # Strategy 2: Look for MAINLAYER and BGLAYER position markers
    print("\n2. Layer Position Markers:")
    for marker in [b"<MAINLAYER:", b"<BGLAYER:"]:
        idx = 0
        while True:
            idx = data.find(marker, idx)
            if idx == -1:
                break
            
            end = data.find(b">", idx + len(marker))
            if end != -1:
                try:
                    offset_str = data[idx + len(marker):end].decode('ascii')
                    offset = int(offset_str)
                    layer_name = marker.decode('ascii')[1:-1]
                    print(f"   {layer_name} at file offset: {offset} (0x{offset:08x})")
                    
                    # Check what's at that offset
                    if offset < len(data) - 16:
                        sample = data[offset:offset + 16]
                        print(f"     Sample at offset: {' '.join(f'{b:02x}' for b in sample)}")
                        
                        # Look for patterns
                        ascii_count = sum(1 for b in sample if 32 <= b <= 126)
                        if ascii_count < 8:
                            print(f"     ✓ Binary data")
                        else:
                            print(f"     ✗ Text/metadata")
                            
                except Exception as e:
                    print(f"   Error: {e}")
            
            idx += 1
    
    # Strategy 3: Search for likely RLE patterns
    print("\n3. Searching for RLE Patterns:")
    print("   Looking for sequences that match stroke patterns...")
    
    # Typical stroke patterns might have:
    # - Coordinates in reasonable ranges (not all 0xFF or 0x00)
    # - Length values typically 1-50
    # - Grayscale values (0-255 but often specific ink values)
    
    candidate_positions = []
    
    # Skip first 1000 bytes (header) and search
    for pos in range(1000, min(len(data) - 1000, 200000), 100):
        # Check if this position has RLE-like patterns
        window = data[pos:pos + 40]
        
        # Count how many 4-byte tuples look like valid RLE
        valid_tuples = 0
        for i in range(0, 40, 4):
            if i + 3 < len(window):
                x, y, length, value = window[i:i+4]
                
                # Heuristics for valid RLE tuple:
                # - Length usually 1-100
                # - Value often 0 (black) or specific gray levels
                # - x, y should vary but not be all 0xFF
                if 0 < length < 100 and (value == 0 or value < 100 or value > 200):
                    valid_tuples += 1
        
        if valid_tuples >= 3:  # At least 3 valid-looking tuples
            candidate_positions.append(pos)
    
    print(f"   Found {len(candidate_positions)} candidate positions")
    if candidate_positions:
        print("   Top candidates:")
        for pos in candidate_positions[:5]:
            sample = data[pos:pos + 12]
            print(f"     0x{pos:08x}: {' '.join(f'{b:02x}' for b in sample)}")
    
    # Strategy 4: Check known offsets from parallel test
    print("\n4. Testing Known Working Offsets:")
    known_offsets = [
        (1091, "Page1_MainLayer"),  # From hardcoded values
        (1222, "Page1_Background"),
        (9408, "Page2_MainLayer"), 
        (9540, "Page2_Background")
    ]
    
    for offset, name in known_offsets:
        print(f"\n   {name} at offset {offset} (0x{offset:08x}):")
        if offset < len(data) - 20:
            sample = data[offset:offset + 20]
            print(f"     Bytes: {' '.join(f'{b:02x}' for b in sample)}")
            
            # Interpret as RLE
            for i in range(0, 12, 4):
                if i + 3 < len(sample):
                    x, y, length, value = sample[i:i+4]
                    print(f"     Tuple {i//4}: x={x:3d}, y={y:3d}, len={length:3d}, val={value:3d}")

def main():
    note_path = Path("/home/ed/ghost-writer/joe.note")
    
    with open(note_path, 'rb') as f:
        data = f.read()
    
    find_bitmap_positions(data)

if __name__ == "__main__":
    main()