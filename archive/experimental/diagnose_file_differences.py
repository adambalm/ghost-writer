#!/usr/bin/env python3
"""
Diagnose why your note file produces blank images vs community file
"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')
sys.path.insert(0, '/home/ed/ghost-writer/src')

import supernotelib as sn
from sn2md.importers.note import load_notebook
import struct

def analyze_file_structure(filepath, label):
    """Analyze the internal structure of a .note file"""
    
    print(f"\n🔍 Analyzing {label}: {filepath}")
    print("=" * 60)
    
    try:
        # Load with supernotelib
        notebook = load_notebook(filepath)
        print(f"✅ Loaded successfully")
        print(f"📊 Pages: {notebook.get_total_pages()}")
        print(f"📐 Dimensions: {notebook.get_width()} x {notebook.get_height()}")
        
        # Check each page
        for i in range(notebook.get_total_pages()):
            page = notebook.get_page(i)
            print(f"\n📄 Page {i+1}:")
            print(f"   - Page object: {type(page)}")
            
            # Try to get layer information
            try:
                layers = page.get_layers()
                print(f"   - Layers: {len(layers)}")
                
                for j, layer in enumerate(layers):
                    print(f"     Layer {j}: {type(layer)}")
                    
                    # Check if layer has stroke data
                    if hasattr(layer, 'get_strokes'):
                        strokes = layer.get_strokes()
                        print(f"       Strokes: {len(strokes) if strokes else 0}")
                        
                        if strokes and len(strokes) > 0:
                            stroke = strokes[0]
                            print(f"       First stroke: {type(stroke)}")
                            if hasattr(stroke, 'get_points'):
                                points = stroke.get_points()
                                print(f"       Points: {len(points) if points else 0}")
                                if points and len(points) > 0:
                                    print(f"       First point: {points[0]}")
                    
                    # Check layer properties
                    print(f"       Layer attrs: {[attr for attr in dir(layer) if not attr.startswith('_')]}")
                        
            except Exception as e:
                print(f"   ❌ Layer analysis failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load: {e}")
        return False

def compare_raw_file_headers(file1, file2):
    """Compare raw file headers to see format differences"""
    
    print(f"\n🔍 Raw File Header Comparison")
    print("=" * 40)
    
    for filepath, label in [(file1, "Your File"), (file2, "Community File")]:
        print(f"\n{label}:")
        try:
            with open(filepath, 'rb') as f:
                header = f.read(100)  # Read first 100 bytes
                
                # Try to find format identifiers
                print(f"   Size: {f.seek(0, 2)} bytes")
                f.seek(0)
                
                # Look for version strings
                first_bytes = f.read(50)
                print(f"   First 50 bytes: {first_bytes}")
                
                # Look for specific format markers
                f.seek(0)
                content = f.read(1000)
                if b'SN_FILE_VER_' in content:
                    start = content.find(b'SN_FILE_VER_')
                    version = content[start:start+30]
                    print(f"   Version found: {version}")
                    
        except Exception as e:
            print(f"   ❌ Error reading: {e}")

def test_extraction_with_debug():
    """Test extraction with detailed debugging"""
    
    print(f"\n🔍 Testing Your File with Debug Info")
    print("=" * 50)
    
    your_file = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    try:
        from supernotelib.converter import ImageConverter, VisibilityOverlay
        
        notebook = load_notebook(your_file)
        converter = ImageConverter(notebook)
        
        # Try different visibility settings
        visibility_options = [
            VisibilityOverlay.DEFAULT,
            VisibilityOverlay.VISIBLE,
            VisibilityOverlay.HIDDEN
        ]
        
        for i, vis_option in enumerate(visibility_options):
            print(f"\nTesting visibility option {i+1}: {vis_option}")
            
            try:
                vo = sn.converter.build_visibility_overlay(background=vis_option)
                img = converter.convert(0, vo)  # Test first page
                
                import numpy as np
                arr = np.array(img)
                mean_val = arr.mean()
                non_white = np.sum(arr < 250)
                
                print(f"   Result: mean={mean_val:.1f}, content pixels={non_white:,}")
                
                if non_white > 1000:
                    print(f"   ✅ SUCCESS with {vis_option}!")
                    
                    # Save this working version
                    img.save(f"/home/ed/ghost-writer/your_file_working_{i}.png")
                    return True
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
    except Exception as e:
        print(f"❌ Overall test failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    your_file = "/home/ed/ghost-writer/temp_20250807_035920.note"
    community_file = "/home/ed/ghost-writer/Visual_Library.note"
    
    # Step 1: Compare file structures
    print("🚀 DIAGNOSTIC: Finding why your file produces blank images")
    print("=" * 70)
    
    your_result = analyze_file_structure(your_file, "Your File")
    community_result = analyze_file_structure(community_file, "Community File")
    
    # Step 2: Compare raw headers
    compare_raw_file_headers(your_file, community_file)
    
    # Step 3: Try different extraction methods
    if your_result:
        success = test_extraction_with_debug()
        
        if not success:
            print(f"\n💡 Potential Solutions:")
            print("1. Your file might use a newer/different format version")
            print("2. Different pen settings/layers might need specific visibility options")
            print("3. The stroke data might be stored differently")
            print("4. Need to investigate the exact RLE format your device uses")
    
    else:
        print(f"\n❌ Your file can't be loaded by supernotelib at all")
        print("This suggests a fundamental format compatibility issue")