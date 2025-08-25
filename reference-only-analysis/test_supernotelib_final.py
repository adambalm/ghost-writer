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
    print(f"✅ Notebook loaded successfully")
    
    # Try to get a converter from the converter module
    from supernotelib.converter import ImageConverter
    converter = ImageConverter(notebook)
    print("✅ ImageConverter created")
    
    # Check what methods are available on notebook
    print("📋 Notebook attributes:")
    for attr in dir(notebook):
        if not attr.startswith('_') and not attr.startswith('get'):
            print(f"  - {attr}")
    
    # Access pages using the correct API
    try:
        total_pages = notebook.get_total_pages()
        print(f"✅ Found {total_pages} pages via get_total_pages()")
        
        for i in range(total_pages):
            page = notebook.get_page(i)
            
            # Check page attributes
            print(f"📄 Page {i+1} attributes:")
            for attr in dir(page):
                if not attr.startswith('_') and ('width' in attr or 'height' in attr or 'get' in attr):
                    print(f"  - {attr}")
            
            # Try to convert to image using page number (not page object)
            output_path = f"/home/ed/ghost-writer/supernotelib_page_{i+1}.png"
            converter.convert(i, output_path)  # Pass page number, not page object
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
        
        print(f"\n📋 Total pages processed: {total_pages}")
        
    except Exception as pages_error:
        print(f"❌ Error accessing pages: {pages_error}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()