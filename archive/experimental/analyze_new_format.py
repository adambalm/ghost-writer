#!/usr/bin/env python3
"""
Analyze the new Supernote format (SN_FILE_VER_20230015)
"""

import struct
import re
from typing import Dict, List, Tuple

def parse_supernote_new_format(file_path: str):
    """Parse the newer Supernote format"""
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"📄 File size: {len(data):,} bytes")
    
    # Parse header
    if not data.startswith(b'noteSN_FILE_VER_'):
        print("❌ Not a newer format file")
        return
    
    # Extract version
    version_end = data.find(b'\x92\x01\x00\x00', 16)
    if version_end == -1:
        print("❌ Could not find version boundary")
        return
    
    version = data[4:version_end].decode('ascii')
    print(f"📋 Version: {version}")
    
    # Find metadata section
    metadata_start = version_end + 4
    
    # Parse XML-like metadata
    metadata_section = []
    pos = metadata_start
    
    while pos < len(data):
        # Look for <TAG:VALUE> pattern
        if data[pos:pos+1] == b'<':
            end_pos = data.find(b'>', pos)
            if end_pos == -1:
                break
            
            tag_content = data[pos+1:end_pos].decode('ascii', errors='ignore')
            metadata_section.append(tag_content)
            pos = end_pos + 1
        else:
            # Check if we've moved into binary data
            if pos > metadata_start + 1000:  # Reasonable metadata size limit
                break
            pos += 1
    
    print(f"\\n📋 Metadata tags found:")
    for tag in metadata_section:
        if ':' in tag:
            key, value = tag.split(':', 1)
            print(f"  {key}: {value}")
    
    # Look for layer information
    layer_starts = []
    pos = 0
    while True:
        layer_pos = data.find(b'LAYERTYPE:', pos)
        if layer_pos == -1:
            break
        layer_starts.append(layer_pos)
        pos = layer_pos + 1
    
    print(f"\\n📄 Found {len(layer_starts)} layers:")
    
    for i, layer_pos in enumerate(layer_starts):
        print(f"\\n🎨 Layer {i+1} at position {layer_pos:,}:")
        
        # Extract layer info
        layer_end = data.find(b'\\x00\\x00\\x00', layer_pos)
        if layer_end == -1:
            layer_end = min(layer_pos + 500, len(data))
        
        layer_data = data[layer_pos:layer_end]
        
        # Parse layer metadata
        layer_info = layer_data.decode('ascii', errors='ignore')
        layer_tags = re.findall(r'<([^>]+)>', layer_info)
        
        for tag in layer_tags:
            if ':' in tag:
                key, value = tag.split(':', 1)
                print(f"  {key}: {value}")
    
    # Look for actual drawing data patterns
    print(f"\\n🔍 Looking for drawing data patterns...")
    
    # Common patterns in drawing data
    patterns = [
        (b'\\x00\\x00\\x00\\x00', "Zero padding"),
        (b'\\xff\\xff\\xff\\xff', "Full bytes"),
        (b'RATTA_RLE', "RLE compression"),
        (b'PNG', "PNG data"),
        (b'LAYER', "Layer markers")
    ]
    
    for pattern, description in patterns:
        count = data.count(pattern)
        if count > 0:
            pos = data.find(pattern)
            print(f"  {description}: {count} occurrences, first at {pos:,}")

if __name__ == "__main__":
    parse_supernote_new_format("/home/ed/ghost-writer/temp_20250807_035920.note")