#!/usr/bin/env python3
"""
Test supernotelib correctly to parse and render our .note file
"""

import sys
from pathlib import Path

try:
    import supernotelib as sn
    print("✅ supernotelib imported successfully")
    
    # Try to parse our file using the correct API
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    print(f"📄 Parsing file: {note_path}")
    
    # Load the notebook
    notebook = sn.load_notebook(note_path)
    print(f"✅ Notebook loaded: {len(notebook)} pages found")
    
    # Try to get a converter from the converter module
    from supernotelib.converter import ImageConverter
    converter = ImageConverter()
    print("✅ ImageConverter created")
    
    for i, page in enumerate(notebook):
        print(f"📄 Page {i+1}: width={page.get_width()}, height={page.get_height()}")
        
        # Try to convert to image
        output_path = f"/home/ed/ghost-writer/supernotelib_page_{i+1}.png"
        converter.convert(page, output_path)
        print(f"✅ Page {i+1} rendered to: {output_path}")
        
        # Show file size
        if Path(output_path).exists():
            size = Path(output_path).stat().st_size
            print(f"   📊 Image size: {size:,} bytes")
            
            # Quick check if image has content
            from PIL import Image
            import numpy as np
            img = Image.open(output_path)
            arr = np.array(img)
            if arr.mean() < 250:
                print(f"   ✅ Image contains content (mean pixel value: {arr.mean():.1f})")
            else:
                print(f"   ⚠️  Image appears blank (mean pixel value: {arr.mean():.1f})")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()