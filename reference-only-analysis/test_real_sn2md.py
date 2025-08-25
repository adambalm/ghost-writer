#!/usr/bin/env python3
"""
Test the real sn2md functionality directly
"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')

from sn2md.importers.note import convert_notebook_to_pngs, load_notebook

def test_with_layer_file():
    """Test with their actual spd file"""
    
    print("🔍 Testing Real sn2md with Layer File")
    print("=" * 45)
    
    spd_file = "/home/ed/ghost-writer/sn2md/tests/sn2md/importers/fixtures/20250325_165308-Layers.spd"
    output_path = "/home/ed/ghost-writer/real_sn2md_test"
    
    try:
        print(f"📄 Loading: {spd_file}")
        notebook = load_notebook(spd_file)
        print(f"✅ Loaded notebook")
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
            
            img = Image.open(png_files[0])
            arr = np.array(img)
            mean_val = arr.mean()
            non_white = np.sum(arr < 250)
            
            print(f"📊 First image stats:")
            print(f"   - Size: {img.size}")
            print(f"   - Mean: {mean_val:.1f}")
            print(f"   - Non-white pixels: {non_white:,}")
            
            if non_white > 1000:
                print("🎉 SUCCESS! Image has content!")
                return True
            else:
                print("⚠️  Image appears mostly blank")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    test_with_layer_file()