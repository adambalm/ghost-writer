#!/usr/bin/env python3
"""
Test script to extract BGLAYER data using proper metadata parsing
This will help us achieve pixel parity with sn2md by finding all 5 layers.
"""

import sys
import struct
import re
from pathlib import Path

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

def parse_metadata_block(fobj, address):
    """Parse metadata block at given address (following sn2md approach)"""
    if address == 0:
        return {}
    
    fobj.seek(address)
    
    # Read 4-byte length field (little endian)
    length_bytes = fobj.read(4)
    if len(length_bytes) != 4:
        return {}
    
    block_length = struct.unpack('<I', length_bytes)[0]
    contents = fobj.read(block_length)
    
    try:
        metadata_str = contents.decode('ascii', errors='ignore')
        return extract_parameters(metadata_str)
    except Exception as e:
        print(f"Error decoding metadata at {address}: {e}")
        return {}

def extract_parameters(metadata):
    """Extract key-value parameters from metadata string"""
    pattern = r'<([^:<>]+):([^:<>]*)>'
    result = re.finditer(pattern, metadata)
    params = {}
    
    for m in result:
        key = m[1]
        value = m[2]
        
        if params.get(key):
            # Handle duplicate keys by converting to list
            if type(params.get(key)) != list:
                first_value = params.pop(key)
                params[key] = [first_value, value]
            else:
                params[key].append(value)
        else:
            params[key] = value
    
    return params

def find_footer_address(data):
    """Find footer address using SN_FILE_VER signature"""
    signature_pattern = b'SN_FILE_VER_'
    
    # The footer is typically near the end, scan last 2KB
    search_start = max(0, len(data) - 2048)
    pos = data.find(signature_pattern, search_start)
    
    if pos == -1:
        return None
    
    # The footer address is usually 4-8 bytes before the signature
    # Try different offsets
    for offset in [4, 8, 12, 16]:
        if pos >= offset:
            try:
                addr_candidate = struct.unpack('<I', data[pos-offset:pos-offset+4])[0]
                # Validate address is reasonable
                if 100 < addr_candidate < len(data) - 50:
                    return addr_candidate
            except:
                continue
    
    return None

def extract_all_layers(note_path):
    """Extract all layers (MAINLAYER, BGLAYER, etc.) from note file"""
    
    print(f"=== EXTRACTING ALL LAYERS FROM {note_path} ===")
    
    with open(note_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data):,} bytes")
    
    # Use known page addresses from sn2md analysis
    # These are the PAGE1 and PAGE2 addresses from sn2md metadata
    page_addresses = []
    
    # We need to scan for PAGE1 and PAGE2 in the footer
    # The footer contains PAGE1:142528 and PAGE2:887828 based on sn2md output
    # Let's find these dynamically by scanning for PAGE patterns
    
    # Scan for PAGE metadata tags
    page_pattern = b'<PAGE'
    pos = 0
    while True:
        pos = data.find(page_pattern, pos)
        if pos == -1:
            break
        
        # Look for the value after PAGE1: or PAGE2:
        end_pos = data.find(b'>', pos)
        if end_pos != -1:
            tag_content = data[pos:end_pos+1].decode('ascii', errors='ignore')
            print(f"Found page tag: {tag_content}")
            
            # Extract address if this is PAGE1 or PAGE2
            if ':' in tag_content:
                try:
                    addr_str = tag_content.split(':')[1].replace('>', '')
                    addr = int(addr_str)
                    page_addresses.append(addr)
                    print(f"  -> Page address: {addr}")
                except:
                    pass
        
        pos += 1
    
    if not page_addresses:
        # Fallback to known addresses for joe.note
        page_addresses = [142528, 887828]
        print(f"Using fallback page addresses: {page_addresses}")
    
    print(f"Found {len(page_addresses)} pages: {page_addresses}")
    
    # Process each page
    for page_idx, page_addr in enumerate(page_addresses):
        print(f"\n=== PAGE {page_idx} at address {page_addr} ===")
        
        with open(note_path, 'rb') as f:
            page_info = parse_metadata_block(f, page_addr)
        
        print(f"Page {page_idx} keys: {list(page_info.keys())}")
        
        # Extract layer addresses using sn2md's LAYER_KEYS
        LAYER_KEYS = ['MAINLAYER', 'LAYER1', 'LAYER2', 'LAYER3', 'BGLAYER']
        
        for layer_name in LAYER_KEYS:
            if layer_name in page_info:
                layer_addr = int(page_info[layer_name])
                print(f"  {layer_name}: {layer_addr}")
                
                if layer_addr > 0:
                    # Parse layer metadata
                    with open(note_path, 'rb') as f:
                        layer_info = parse_metadata_block(f, layer_addr)
                    
                    print(f"    Layer metadata keys: {list(layer_info.keys())}")
                    
                    # Look for LAYERBITMAP address
                    if 'LAYERBITMAP' in layer_info:
                        bitmap_addr = int(layer_info['LAYERBITMAP'])
                        print(f"    LAYERBITMAP at: {bitmap_addr}")
                        
                        # Extract bitmap data
                        with open(note_path, 'rb') as f:
                            f.seek(bitmap_addr)
                            bitmap_length = struct.unpack('<I', f.read(4))[0]
                            bitmap_data = f.read(bitmap_length)
                        
                        print(f"    Bitmap data: {len(bitmap_data)} bytes")
                        print(f"    First 20 bytes: {bitmap_data[:20].hex()}")
                        
                        # Analyze for RLE patterns
                        if len(bitmap_data) >= 4:
                            analyze_rle_pattern(bitmap_data, layer_name)
            else:
                print(f"  {layer_name}: NOT FOUND")

def analyze_rle_pattern(data, layer_name):
    """Analyze RLE pattern to estimate pixel count"""
    
    total_pixels = 0
    
    for i in range(0, min(20, len(data)), 2):
        if i+1 < len(data):
            color_code = data[i]
            length_code = data[i+1]
            
            if length_code == 0xff:  # SPECIAL_LENGTH_MARKER
                pixels = 16384  # SPECIAL_LENGTH
            else:
                pixels = length_code + 1
            
            total_pixels += pixels
    
    # Estimate full pattern
    if len(data) >= 4:
        pattern_length = 20 if len(data) > 20 else len(data)
        full_estimate = (total_pixels * len(data)) // pattern_length
        
        print(f"    RLE Analysis ({layer_name}):")
        print(f"      Sample pixels (first 20 bytes): {total_pixels:,}")
        print(f"      Estimated total pixels: {full_estimate:,}")

def main():
    note_path = Path("/home/ed/ghost-writer/joe.note")
    
    if not note_path.exists():
        print(f"❌ File not found: {note_path}")
        return
    
    extract_all_layers(note_path)

if __name__ == "__main__":
    main()