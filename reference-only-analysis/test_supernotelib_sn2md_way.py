#!/usr/bin/env python3
"""
Test supernotelib using the exact same approach as sn2md
"""

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay
from pathlib import Path

def test_sn2md_approach():
    """Test the exact approach sn2md uses"""
    
    print("🔍 Testing sn2md's Approach to supernotelib")
    print("=" * 50)
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    # Load notebook (same as sn2md)
    print(f"📄 Loading notebook: {note_path}")
    notebook = sn.load_notebook(note_path)
    print(f"✅ Notebook loaded")
    
    # Create converter (same as sn2md)
    converter = ImageConverter(notebook)
    print("✅ ImageConverter created")
    
    # Build visibility overlay (same as sn2md)
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)
    print(f"✅ Visibility overlay created: {vo}")
    
    # Get total pages
    total_pages = notebook.get_total_pages()
    print(f"✅ Total pages: {total_pages}")
    
    # Convert each page (same as sn2md)
    for i in range(total_pages):
        print(f"\n📄 Processing page {i+1}/{total_pages}...")
        
        try:
            # Convert page using visibility overlay (this is the key difference)
            img = converter.convert(i, vo)
            
            # Save image
            output_path = f"/home/ed/ghost-writer/sn2md_approach_page_{i+1}.png"
            img.save(output_path, format="PNG")
            print(f"✅ Saved: {output_path}")
            
            # Check if image has content
            import numpy as np
            arr = np.array(img)
            mean_val = arr.mean()
            
            if mean_val < 250:
                print(f"   ✅ Image contains content (mean: {mean_val:.1f})")
                
                # Count non-white pixels
                non_white = np.sum(arr < 250)
                print(f"   📊 Non-white pixels: {non_white:,}")
                
            else:
                print(f"   ⚠️  Image appears blank (mean: {mean_val:.1f})")
            
            # Check image properties
            print(f"   📐 Size: {img.size}")
            print(f"   🎨 Mode: {img.mode}")
            
        except Exception as e:
            print(f"❌ Failed to process page {i+1}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_sn2md_approach()