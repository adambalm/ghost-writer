#!/usr/bin/env python3
"""
Analyze raw RLE data to understand the actual format
"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')

from sn2md.importers.note import load_notebook
import struct

def analyze_raw_rle_data():
    """Look at the raw RLE content to understand the format"""
    
    print("🔍 Raw RLE Data Analysis")
    print("=" * 40)
    
    try:
        notebook = load_notebook("/home/ed/ghost-writer/temp_20250807_035920.note")
        
        for page_idx in range(notebook.get_total_pages()):
            page = notebook.get_page(page_idx)
            layers = page.get_layers()
            
            print(f"\n📄 Page {page_idx + 1}:")
            
            for layer_idx, layer in enumerate(layers):
                if layer is None:
                    continue
                    
                content = layer.get_content()
                if content and len(content) > 0:
                    print(f"  Layer {layer_idx} ({layer.get_name()}):")
                    print(f"    Content size: {len(content)} bytes")
                    print(f"    Protocol: {layer.get_protocol()}")
                    
                    # Examine raw bytes
                    hex_preview = content[:100].hex()
                    print(f"    Hex preview: {hex_preview}")
                    
                    # Look for patterns
                    if content.startswith(b'62ff'):
                        print(f"    ✅ Starts with RLE marker 62ff")
                    
                    # Try to decode as coordinates
                    print(f"    First 20 bytes as uint16: ", end="")
                    try:
                        coords = struct.unpack('<' + 'H' * min(10, len(content)//2), content[:20])
                        print(coords)
                    except:
                        print("decode failed")
                    
                    # Count repeating patterns
                    pattern_counts = {}
                    for i in range(0, len(content)-1, 2):
                        pattern = content[i:i+2].hex()
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                    
                    print(f"    Top patterns: {dict(list(pattern_counts.items())[:5])}")
                    
                    # Try manual RLE decoding approach
                    if len(content) >= 8:
                        try_manual_rle_decode(content, layer.get_name())
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

def try_manual_rle_decode(data, layer_name):
    """Attempt manual RLE decoding with different approaches"""
    
    print(f"    🔧 Manual decode attempt for {layer_name}:")
    
    try:
        # Approach 1: Skip RLE header and decode coordinate pairs
        if data.startswith(b'b\xff'):  # 62ff pattern
            # Skip repeating 62ff pattern
            start_pos = 0
            while start_pos < len(data) - 1 and data[start_pos:start_pos+2] == b'b\xff':
                start_pos += 2
            
            print(f"      Skipped {start_pos} header bytes")
            
            if start_pos < len(data):
                # Try to decode remaining as coordinate pairs
                remaining = data[start_pos:]
                if len(remaining) >= 4:
                    try:
                        # Try different coordinate formats
                        coords = struct.unpack('<HH', remaining[:4])
                        print(f"      First coord pair: {coords}")
                        
                        # Check if coordinates are reasonable
                        if 0 <= coords[0] <= 2000 and 0 <= coords[1] <= 2000:
                            print(f"      ✅ Coordinates look valid!")
                            
                            # Try to extract more coordinates
                            coord_pairs = []
                            for i in range(0, min(20, len(remaining)), 4):
                                if i + 3 < len(remaining):
                                    x, y = struct.unpack('<HH', remaining[i:i+4])
                                    if 0 <= x <= 2000 and 0 <= y <= 2000:
                                        coord_pairs.append((x, y))
                            
                            print(f"      Found {len(coord_pairs)} valid coordinates")
                            if coord_pairs:
                                print(f"      Sample coords: {coord_pairs[:5]}")
                                return coord_pairs
                        
                    except struct.error:
                        print(f"      ❌ Coordinate decode failed")
        
        # Approach 2: Different RLE format
        print(f"      Trying alternative RLE format...")
        
    except Exception as e:
        print(f"      ❌ Manual decode failed: {e}")
    
    return None

def try_alternative_visibility_combinations():
    """Try different combinations of visibility settings"""
    
    print(f"\n🔧 Alternative Visibility Combinations")
    print("=" * 50)
    
    try:
        import supernotelib as sn
        from supernotelib.converter import ImageConverter, VisibilityOverlay
        
        notebook = load_notebook("/home/ed/ghost-writer/temp_20250807_035920.note")
        converter = ImageConverter(notebook)
        
        # Try different layer combinations
        test_combinations = [
            {"background": VisibilityOverlay.VISIBLE, "main": VisibilityOverlay.INVISIBLE},
            {"background": VisibilityOverlay.INVISIBLE, "main": VisibilityOverlay.VISIBLE},
            {"background": VisibilityOverlay.DEFAULT, "main": VisibilityOverlay.INVISIBLE},
            {"background": VisibilityOverlay.INVISIBLE, "main": VisibilityOverlay.DEFAULT},
        ]
        
        for i, combo in enumerate(test_combinations):
            print(f"\nTest {i+1}: background={combo['background'].name}, main={combo.get('main', 'DEFAULT')}")
            
            try:
                # This might not work with current supernotelib API, but worth trying
                vo = sn.converter.build_visibility_overlay(background=combo['background'])
                img = converter.convert(0, vo)
                
                import numpy as np
                arr = np.array(img)
                non_white = np.sum(arr < 250)
                
                print(f"  Result: {non_white:,} content pixels")
                
                if non_white > 5000 and non_white < 1000000:  # Reasonable range
                    print(f"  ✅ Promising result - saving test image")
                    img.save(f"/home/ed/ghost-writer/alternative_test_{i+1}.png")
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
    except Exception as e:
        print(f"❌ Alternative visibility test failed: {e}")

if __name__ == "__main__":
    analyze_raw_rle_data()
    try_alternative_visibility_combinations()
    
    print(f"\n💡 Next steps if no readable content found:")
    print("1. The note file may contain very light strokes")
    print("2. Different Supernote model/firmware may need custom decoder") 
    print("3. Content might be in a different layer or format")
    print("4. May need to use Supernote's official export tools")