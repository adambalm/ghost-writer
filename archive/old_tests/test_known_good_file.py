#!/usr/bin/env python3
"""
Test sn2md with a known-good .note file from the community
"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')

from sn2md.importers.note import convert_notebook_to_pngs, load_notebook

def test_visual_library_file():
    """Test with Visual_Library.note from awesome-supernote"""
    
    print("🔍 Testing sn2md with Visual_Library.note")
    print("=" * 50)
    
    note_file = "/home/ed/ghost-writer/Visual_Library.note"
    output_path = "/home/ed/ghost-writer/visual_library_test"
    
    try:
        print(f"📄 Loading: {note_file}")
        notebook = load_notebook(note_file)
        print(f"✅ Loaded notebook successfully!")
        print(f"📊 Pages: {notebook.get_total_pages()}")
        
        print(f"🖼️  Converting to PNGs...")
        png_files = convert_notebook_to_pngs(notebook, output_path)
        
        print(f"✅ Created {len(png_files)} images:")
        for png_file in png_files:
            print(f"   - {png_file}")
            
        # Check image content
        if png_files:
            from PIL import Image
            import numpy as np
            
            for i, png_file in enumerate(png_files):
                img = Image.open(png_file)
                arr = np.array(img)
                mean_val = arr.mean()
                non_white = np.sum(arr < 250)
                
                print(f"📊 Image {i+1} stats:")
                print(f"   - Size: {img.size}")
                print(f"   - Mean: {mean_val:.1f}")
                print(f"   - Non-white pixels: {non_white:,}")
                
                if non_white > 1000:
                    print(f"   🎉 Image {i+1} has substantial content!")
                else:
                    print(f"   ⚠️  Image {i+1} appears mostly blank")
        
        # Summary
        total_content_pixels = 0
        for png_file in png_files:
            img = Image.open(png_file)
            arr = np.array(img)
            total_content_pixels += np.sum(arr < 250)
        
        if total_content_pixels > 5000:
            print(f"\n🎉 SUCCESS! Found {total_content_pixels:,} content pixels across all images")
            print("✅ This proves sn2md + supernotelib work with proper .note files!")
            return True
        else:
            print(f"\n⚠️  Only found {total_content_pixels:,} content pixels")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visual_library_file()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. This confirms sn2md works with proper .note files")
        print("2. Our original test file was likely corrupted/incompatible") 
        print("3. We can now build on sn2md as the foundation")
    else:
        print("\n🤔 Still having issues - may need to investigate further")