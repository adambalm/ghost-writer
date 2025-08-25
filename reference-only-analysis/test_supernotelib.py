#!/usr/bin/env python3
"""
Test supernotelib directly to parse and render our .note file
"""

import sys
from pathlib import Path

# Test if we can use the supernotelib that sn2md installed
try:
    import supernotelib as sn
    print("✅ supernotelib imported successfully")
    
    # Try to parse our file
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    print(f"📄 Parsing file: {note_path}")
    
    # Create a converter
    converter = sn.ImageConverter()
    print("✅ ImageConverter created")
    
    # Try to parse the file
    notebook = sn.Notebook.open(note_path)
    print(f"✅ Notebook opened: {len(notebook)} pages found")
    
    for i, page in enumerate(notebook):
        print(f"📄 Page {i+1}: {page}")
        
        # Try to convert to image
        output_path = f"/home/ed/ghost-writer/supernotelib_page_{i+1}.png"
        converter.convert(page, output_path)
        print(f"✅ Page {i+1} rendered to: {output_path}")
        
        # Show file size
        if Path(output_path).exists():
            size = Path(output_path).stat().st_size
            print(f"   📊 Image size: {size:,} bytes")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()