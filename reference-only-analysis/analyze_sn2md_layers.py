#!/usr/bin/env python3
"""Analyze how sn2md extracts layers from joe.note"""

import sys
import os
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')
sys.path.insert(0, '/home/ed/ghost-writer/supernote-tool')
sys.path.insert(0, '/home/ed/ghost-writer/src')

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay, build_visibility_overlay

def analyze_layers():
    print("Analyzing sn2md layer extraction for joe.note\n")
    print("=" * 60)
    
    # Load the notebook
    notebook = sn.load_notebook('/home/ed/ghost-writer/joe.note')
    print(f"✅ Loaded notebook: {notebook.get_total_pages()} pages")
    print(f"   Dimensions: {notebook.get_width()}x{notebook.get_height()}")
    
    # Check what metadata is available
    metadata = notebook.get_metadata()
    print(f"\n📋 Metadata type: {type(metadata)}")
    
    # Analyze each page
    for page_num in range(notebook.get_total_pages()):
        print(f"\n📄 Page {page_num + 1}:")
        page = notebook.get_page(page_num)
        
        # Check if layers are supported
        if page.is_layer_supported():
            print("   ✅ Layers supported")
            layers = page.get_layers()
            print(f"   Found {len(layers)} layers:")
            
            for layer in layers:
                layer_name = layer.get_name()
                content = layer.get_content()
                if content:
                    print(f"     - {layer_name}: {len(content)} bytes")
                else:
                    print(f"     - {layer_name}: No content")
                    
            # Check visibility settings
            print("\n   Visibility settings:")
            # Try to get layer visibility 
            try:
                # This is how converter does it
                from supernotelib import utils
                page_wrapper = utils.WorkaroundPageWrapper.from_page(page)
                visibility = {}
                for layer in page_wrapper.get_layers():
                    layer_name = layer.get_name()
                    is_visible = layer.is_visible()
                    visibility[layer_name] = is_visible
                    print(f"     - {layer_name}: {'visible' if is_visible else 'invisible'}")
            except Exception as e:
                print(f"     Error getting visibility: {e}")
                
        else:
            print("   ❌ No layer support")
            content = page.get_content()
            if content:
                print(f"   Single layer: {len(content)} bytes")
    
    # Now test the converter with different visibility modes
    print("\n" + "=" * 60)
    print("Testing ImageConverter with different visibility modes:\n")
    
    converter = ImageConverter(notebook)
    
    visibility_modes = [
        ("DEFAULT", build_visibility_overlay(background=VisibilityOverlay.DEFAULT)),
        ("VISIBLE", build_visibility_overlay(background=VisibilityOverlay.VISIBLE)),
        ("INVISIBLE", build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)),
    ]
    
    for mode_name, visibility_overlay in visibility_modes:
        print(f"\n🔍 Testing {mode_name} mode:")
        for page_num in range(notebook.get_total_pages()):
            img = converter.convert(page_num, visibility_overlay)
            # Count non-white pixels
            import numpy as np
            img_array = np.array(img)
            if len(img_array.shape) == 3:
                # RGB/RGBA image
                if img_array.shape[2] == 4:
                    # RGBA - check alpha channel for transparency
                    non_white = np.sum(img_array[:,:,3] > 0)
                else:
                    # RGB - check if not white
                    white = np.all(img_array == 255, axis=2)
                    non_white = np.sum(~white)
            else:
                # Grayscale
                non_white = np.sum(img_array < 255)
            
            print(f"   Page {page_num + 1}: {non_white:,} non-white pixels, mode={img.mode}, size={img.size}")

if __name__ == "__main__":
    analyze_layers()