#!/usr/bin/env python3
"""
Analyze the actual layer content to find where the handwriting data is
"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')

from sn2md.importers.note import load_notebook

def analyze_layer_content(filepath, label):
    """Deep analysis of layer content"""
    
    print(f"\n🔍 Deep Layer Analysis: {label}")
    print("=" * 50)
    
    try:
        notebook = load_notebook(filepath)
        
        for page_idx in range(min(2, notebook.get_total_pages())):  # Just first 2 pages
            page = notebook.get_page(page_idx)
            layers = page.get_layers()
            
            print(f"\n📄 Page {page_idx + 1}:")
            
            for layer_idx, layer in enumerate(layers):
                print(f"  Layer {layer_idx}:")
                print(f"    Name: {layer.get_name()}")
                print(f"    Type: {layer.get_type()}")
                print(f"    Protocol: {layer.get_protocol()}")
                
                # Get raw content
                content = layer.get_content()
                print(f"    Content size: {len(content)} bytes")
                
                if len(content) > 0:
                    # Show first 100 bytes as hex
                    hex_preview = content[:100].hex()
                    print(f"    Content preview: {hex_preview}")
                    
                    # Look for specific patterns
                    if b'RLE' in content:
                        print(f"    ✅ Contains RLE marker")
                    if len(content) > 1000:
                        print(f"    ✅ Substantial content ({len(content)} bytes)")
                    else:
                        print(f"    ⚠️  Small content ({len(content)} bytes)")
                        
                    # Check metadata
                    if hasattr(layer, 'metadata'):
                        print(f"    Metadata: {layer.metadata}")
                else:
                    print(f"    ❌ Empty content")
                    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

def test_manual_extraction():
    """Try manual extraction approaches"""
    
    print(f"\n🔧 Manual Extraction Test")
    print("=" * 30)
    
    try:
        import supernotelib as sn
        from supernotelib.converter import ImageConverter, VisibilityOverlay
        
        notebook = load_notebook("/home/ed/ghost-writer/temp_20250807_035920.note")
        converter = ImageConverter(notebook)
        
        # Try all available visibility options
        available_options = [attr for attr in dir(VisibilityOverlay) if not attr.startswith('_')]
        print(f"Available visibility options: {available_options}")
        
        for option_name in available_options:
            if option_name.isupper():  # Likely constants
                try:
                    option_value = getattr(VisibilityOverlay, option_name)
                    print(f"\nTesting {option_name} ({option_value}):")
                    
                    vo = sn.converter.build_visibility_overlay(background=option_value)
                    img = converter.convert(0, vo)
                    
                    import numpy as np
                    arr = np.array(img)
                    mean_val = arr.mean()
                    non_white = np.sum(arr < 250)
                    
                    print(f"  Result: mean={mean_val:.1f}, content={non_white:,}")
                    
                    if non_white > 1000:
                        print(f"  🎉 SUCCESS with {option_name}!")
                        img.save(f"/home/ed/ghost-writer/success_extraction_{option_name}.png")
                        return True
                        
                except Exception as e:
                    print(f"  ❌ {option_name} failed: {e}")
        
        # Try individual layer extraction
        print(f"\n🔧 Individual Layer Extraction:")
        page = notebook.get_page(0)
        layers = page.get_layers()
        
        for i, layer in enumerate(layers):
            content = layer.get_content()
            if len(content) > 100:  # Only try layers with content
                print(f"  Testing Layer {i} ({len(content)} bytes):")
                try:
                    # Try to decode this layer manually
                    from supernotelib.decoder import RleDecoder
                    decoder = RleDecoder()
                    
                    # Try direct decoding (this might fail but shows us the approach)
                    result = decoder.decode(content, notebook.get_width(), notebook.get_height())
                    print(f"    Direct decode result: {type(result)}")
                    
                    if result is not None:
                        print(f"    ✅ Layer {i} decoded successfully!")
                        
                except Exception as e:
                    print(f"    ❌ Layer {i} decode failed: {e}")
                    
    except Exception as e:
        print(f"❌ Manual extraction failed: {e}")
        import traceback
        traceback.print_exc()
        
    return False

if __name__ == "__main__":
    your_file = "/home/ed/ghost-writer/temp_20250807_035920.note"
    community_file = "/home/ed/ghost-writer/Visual_Library.note"
    
    print("🚀 DEEP CONTENT ANALYSIS")
    print("=" * 40)
    
    # Analyze both files' layer content
    analyze_layer_content(your_file, "Your File")
    analyze_layer_content(community_file, "Community File") 
    
    # Try manual extraction methods
    success = test_manual_extraction()
    
    if not success:
        print(f"\n💡 The issue is likely:")
        print("1. Your file format (20230015) stores data differently than expected")
        print("2. The handwriting might be in a different layer or format")
        print("3. Need to reverse-engineer the newer format structure")
        print("4. May need to improve the RLE decoder for newer formats")