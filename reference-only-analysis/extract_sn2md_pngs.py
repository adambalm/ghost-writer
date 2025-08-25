#!/usr/bin/env python3
"""
Extract the PNG files that sn2md generates so we can examine them
"""

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay
from pathlib import Path
import os

def extract_sn2md_pngs():
    """Extract PNG files exactly as sn2md does"""
    
    print("🔍 Extracting PNG files using sn2md's exact method")
    print("=" * 55)
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    output_dir = "/home/ed/ghost-writer/sn2md_png_extraction"
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Load notebook exactly as sn2md does
    print(f"📄 Loading: {note_path}")
    notebook = sn.load_notebook(note_path)
    
    # Create converter exactly as sn2md does  
    converter = ImageConverter(notebook)
    
    # Build visibility overlay exactly as sn2md does
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)
    
    print(f"🎨 Visibility overlay: {vo}")
    
    # Use sn2md's exact file naming and conversion
    total_pages = notebook.get_total_pages()
    
    # This is sn2md's exact naming logic
    file_name = output_dir + "/" + os.path.basename(note_path) + ".png"
    basename, extension = os.path.splitext(file_name)
    max_digits = len(str(total_pages))
    
    print(f"📊 Converting {total_pages} pages...")
    
    files = []
    for i in range(total_pages):
        # Exact sn2md naming
        numbered_filename = basename + "_" + str(i).zfill(max_digits) + extension
        
        print(f"🔄 Processing page {i+1}: {numbered_filename}")
        
        # Convert exactly as sn2md does
        img = converter.convert(i, vo)
        
        # Save exactly as sn2md does  
        img.save(numbered_filename, format="PNG")
        files.append(numbered_filename)
        
        print(f"✅ Saved: {numbered_filename}")
        
        # Check content
        import numpy as np
        arr = np.array(img)
        mean_val = arr.mean()
        non_white = np.sum(arr < 250)
        
        print(f"   📐 Size: {img.size}")
        print(f"   🎨 Mode: {img.mode}")  
        print(f"   📊 Mean pixel: {mean_val:.1f}")
        print(f"   📈 Non-white pixels: {non_white:,}")
        
        if mean_val < 250:
            print(f"   ✅ Contains content")
        else:
            print(f"   ⚠️  Appears blank")
    
    print(f"\n📋 Summary:")
    print(f"   Generated {len(files)} files")
    print(f"   Output directory: {output_dir}")
    
    return files

if __name__ == "__main__":
    files = extract_sn2md_pngs()
    
    print(f"\n🔍 Files generated:")
    for f in files:
        print(f"   {f}")