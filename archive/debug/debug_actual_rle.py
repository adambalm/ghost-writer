#!/usr/bin/env python3
"""Debug the actual RLE format by examining supernotelib's working decoder"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')
sys.path.insert(0, '/home/ed/ghost-writer/supernote-tool')

def analyze_rle():
    # Get the working decoded result from supernotelib
    import supernotelib as sn
    from supernotelib.converter import ImageConverter, VisibilityOverlay, build_visibility_overlay
    import numpy as np
    
    notebook = sn.load_notebook('/home/ed/ghost-writer/joe.note')
    converter = ImageConverter(notebook)
    
    # Get Page 1 with DEFAULT visibility (what we want to match)
    vo = build_visibility_overlay(background=VisibilityOverlay.DEFAULT)
    img = converter.convert(0, vo)  # Page 1
    
    print(f"supernotelib result: {img.mode}, {img.size}")
    arr = np.array(img)
    if len(arr.shape) == 3:
        non_white = np.sum(np.any(arr < 250, axis=2))
    else:
        non_white = np.sum(arr < 250)
    print(f"Non-white pixels (< 250): {non_white:,}")
    
    # Now let's examine what the decoder actually produces
    page = notebook.get_page(0)
    if page.is_layer_supported():
        layers = page.get_layers()
        print(f"\nFound {len(layers)} layers:")
        
        for i, layer in enumerate(layers):
            name = layer.get_name()
            content = layer.get_content()
            if content and name:
                print(f"\nLayer {i}: {name}")
                print(f"  Content size: {len(content):,} bytes")
                
                # Try to decode with supernotelib's decoder
                from supernotelib.decoder import RattaRleDecoder
                from supernotelib import color
                
                decoder = RattaRleDecoder()
                palette = color.DEFAULT_COLORPALETTE
                
                try:
                    result, size, bpp = decoder.decode(content, 1404, 1872, palette=palette)
                    print(f"  Decoded: {len(result)} bytes, {size}, {bpp} bpp")
                    
                    # Convert to numpy for analysis
                    if bpp == 8:
                        decoded_arr = np.frombuffer(result, dtype=np.uint8).reshape(size[::-1])
                    elif bpp == 24:
                        decoded_arr = np.frombuffer(result, dtype=np.uint8).reshape((*size[::-1], 3))
                    elif bpp == 32:
                        decoded_arr = np.frombuffer(result, dtype=np.uint8).reshape((*size[::-1], 4))
                    
                    if len(decoded_arr.shape) == 2:
                        non_white = np.sum(decoded_arr < 250)
                    else:
                        non_white = np.sum(np.any(decoded_arr < 250, axis=-1))
                    
                    print(f"  Non-white pixels: {non_white:,}")
                    print(f"  Shape: {decoded_arr.shape}")
                    print(f"  Min value: {decoded_arr.min()}, Max value: {decoded_arr.max()}")
                    
                    # Show some sample values
                    flat = decoded_arr.flatten()
                    unique_vals = np.unique(flat[:10000])  # First 10k pixels
                    print(f"  Sample unique values: {unique_vals[:10]}")
                    
                except Exception as e:
                    print(f"  Decode error: {e}")

if __name__ == "__main__":
    analyze_rle()