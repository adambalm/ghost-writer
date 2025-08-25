#!/usr/bin/env python3
"""
Use the EXACT method sn2md uses, no variations
"""

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay
import numpy as np

def test_exact_sn2md_method():
    """Use exactly what sn2md does, word for word"""
    
    print("📋 Testing EXACT sn2md Method")
    print("=" * 40)
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    # Step 1: Load notebook exactly as sn2md
    print("1. Loading notebook...")
    notebook = sn.load_notebook(note_path)  # sn2md uses default policy
    
    print(f"   ✅ Signature: {notebook.get_signature()}")
    print(f"   📊 Pages: {notebook.get_total_pages()}")
    print(f"   🎨 Highres support: {notebook.supports_highres_grayscale()}")
    
    # Step 2: Create converter exactly as sn2md
    print("2. Creating converter...")
    converter = ImageConverter(notebook)
    
    # Step 3: Build visibility overlay exactly as sn2md
    print("3. Building visibility overlay...")
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)
    print(f"   Overlay: {vo}")
    
    # Step 4: Convert pages exactly as sn2md
    print("4. Converting pages...")
    total = notebook.get_total_pages()
    
    for i in range(total):
        print(f"   📄 Page {i+1}/{total}...")
        
        # This is EXACTLY what sn2md does in convert_pages_to_pngs()
        img = converter.convert(i, vo)
        
        # Save and analyze
        output_path = f"/home/ed/ghost-writer/exact_sn2md_page_{i+1}.png" 
        img.save(output_path, format="PNG")
        
        # Check content
        arr = np.array(img)
        mean_val = arr.mean()
        non_white = np.sum(arr < 250)
        
        print(f"      💾 Saved: {output_path}")
        print(f"      📐 Size: {img.size}")
        print(f"      📊 Mean: {mean_val:.1f}")
        print(f"      📈 Non-white: {non_white:,}")
        
        if non_white > 0:
            print(f"      🎉 CONTENT FOUND!")
            
            # Let's examine this more closely
            unique_vals = np.unique(arr)
            print(f"      🎨 Unique pixel values: {len(unique_vals)}")
            print(f"      🔍 Value range: {unique_vals.min()} to {unique_vals.max()}")
            
            # Show where the content is
            dark_pixels = arr < 200
            if np.any(dark_pixels):
                rows_with_content = np.any(dark_pixels, axis=1)
                cols_with_content = np.any(dark_pixels, axis=0)
                
                min_row = np.where(rows_with_content)[0].min()
                max_row = np.where(rows_with_content)[0].max()
                min_col = np.where(cols_with_content)[0].min()
                max_col = np.where(cols_with_content)[0].max()
                
                print(f"      📍 Content area: rows {min_row}-{max_row}, cols {min_col}-{max_col}")
                print(f"      📏 Content size: {max_col-min_col+1} x {max_row-min_row+1}")
        
        else:
            print(f"      ⚠️  Still blank")

if __name__ == "__main__":
    test_exact_sn2md_method()