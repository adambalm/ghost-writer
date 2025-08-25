#!/usr/bin/env python3
"""Debug bitmap extraction differences between sn2md and our parser"""

import sys
import os
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')
sys.path.insert(0, '/home/ed/ghost-writer/supernote-tool')
sys.path.insert(0, '/home/ed/ghost-writer/src')

def analyze_bitmap_extraction():
    print("Comparing bitmap extraction methods\n")
    print("=" * 80)
    
    # Read the raw file
    with open('/home/ed/ghost-writer/joe.note', 'rb') as f:
        raw_data = f.read()
    
    print(f"Total file size: {len(raw_data):,} bytes\n")
    
    # Method 1: How sn2md/supernotelib extracts bitmap data
    print("Method 1: sn2md/supernotelib approach")
    print("-" * 40)
    
    import supernotelib as sn
    notebook = sn.load_notebook('/home/ed/ghost-writer/joe.note')
    
    for page_num in range(notebook.get_total_pages()):
        page = notebook.get_page(page_num)
        print(f"\nPage {page_num + 1}:")
        
        if page.is_layer_supported():
            layers = page.get_layers()
            for layer in layers:
                layer_name = layer.get_name()
                content = layer.get_content()
                if content:
                    print(f"  {layer_name}: {len(content):,} bytes")
                    # Show first few bytes
                    print(f"    First 20 bytes: {content[:20].hex()}")
                    
                    # Check for RLE markers
                    if len(content) > 2:
                        # Look for RATTA_RLE markers (0x61-0x68)
                        rle_markers = [0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68]
                        has_rle = any(b in content[:100] for b in rle_markers)
                        print(f"    Has RLE markers: {has_rle}")
    
    # Method 2: Our parser's approach
    print("\n" + "=" * 80)
    print("Method 2: Our parser approach")
    print("-" * 40)
    
    from utils.supernote_parser import SupernoteParser
    parser = SupernoteParser()
    
    # Find layer information
    version_start = raw_data.find(b'SN_FILE_VER_')
    if version_start != -1:
        print(f"Found SN_FILE_VER at position: {version_start}")
        
    # Look for LAYERBITMAP tags
    pos = 0
    layer_count = 0
    while pos < len(raw_data):
        bitmap_tag = raw_data.find(b'<LAYERBITMAP:', pos)
        if bitmap_tag == -1:
            break
            
        layer_count += 1
        # Find the end of the tag
        tag_end = raw_data.find(b'>', bitmap_tag)
        if tag_end != -1:
            tag_content = raw_data[bitmap_tag:tag_end+1]
            print(f"\nLayer {layer_count}:")
            print(f"  Tag position: {bitmap_tag}")
            print(f"  Tag: {tag_content}")
            
            # Extract the address from the tag
            try:
                addr_str = tag_content.split(b':')[1].rstrip(b'>').decode('ascii')
                addr = int(addr_str)
                print(f"  Address: {addr} (0x{addr:x})")
                
                # Read the bitmap data at this address
                if addr < len(raw_data):
                    # First 4 bytes should be the length
                    length_bytes = raw_data[addr:addr+4]
                    if len(length_bytes) == 4:
                        length = int.from_bytes(length_bytes, 'little')
                        print(f"  Length field: {length:,} bytes")
                        
                        # Get the actual bitmap data
                        bitmap_data = raw_data[addr+4:addr+4+length]
                        if len(bitmap_data) > 0:
                            print(f"  Actual data size: {len(bitmap_data):,} bytes")
                            print(f"  First 20 bytes: {bitmap_data[:20].hex()}")
                            
                            # Check for RLE markers
                            rle_markers = [0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68]
                            has_rle = any(b in bitmap_data[:100] for b in rle_markers)
                            print(f"  Has RLE markers: {has_rle}")
                            
                            # Check what our parser thinks the size is
                            layer_type_tag = raw_data.rfind(b'<LAYERTYPE:', 0, bitmap_tag)
                            if layer_type_tag != -1:
                                type_end = raw_data.find(b'>', layer_type_tag)
                                if type_end != -1:
                                    layer_type = raw_data[layer_type_tag:type_end+1]
                                    print(f"  Layer type: {layer_type}")
            except Exception as e:
                print(f"  Error parsing: {e}")
                
        pos = tag_end + 1 if tag_end != -1 else bitmap_tag + 1
    
    print(f"\nTotal layers found: {layer_count}")

if __name__ == "__main__":
    analyze_bitmap_extraction()