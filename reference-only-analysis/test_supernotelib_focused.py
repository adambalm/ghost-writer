#!/usr/bin/env python3
"""
Focused test of supernotelib image conversion with different options
"""

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay
from pathlib import Path
import numpy as np

def test_image_conversion_options():
    """Test different image conversion options systematically"""
    
    print("🎯 Focused supernotelib Image Conversion Test")
    print("=" * 55)
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    # Load notebook - we know this works
    print(f"📄 Loading: {note_path}")
    notebook = sn.load_notebook(note_path, policy='loose')
    
    print(f"✅ Loaded successfully")
    print(f"   🔍 Signature: {notebook.get_signature()}")  
    print(f"   📊 Total pages: {notebook.get_total_pages()}")
    print(f"   🎨 Supports highres: {notebook.supports_highres_grayscale()}")
    
    # Create converter
    converter = ImageConverter(notebook)
    
    # Test different combinations systematically
    test_configs = [
        {
            "name": "Default_Normal",
            "visibility": VisibilityOverlay.DEFAULT,
            "highres": False
        },
        {
            "name": "Default_HighRes", 
            "visibility": VisibilityOverlay.DEFAULT,
            "highres": True
        },
        {
            "name": "Visible_Normal",
            "visibility": VisibilityOverlay.VISIBLE,
            "highres": False  
        },
        {
            "name": "Visible_HighRes",
            "visibility": VisibilityOverlay.VISIBLE,
            "highres": True
        },
        {
            "name": "Invisible_Normal",
            "visibility": VisibilityOverlay.INVISIBLE,
            "highres": False
        }
    ]
    
    successful_configs = []
    
    for config in test_configs:
        print(f"\n🧪 Testing {config['name']}...")
        
        try:
            # Build visibility overlay
            vo = sn.converter.build_visibility_overlay(
                background=config['visibility'],
                mainlayer=config['visibility']
            )
            
            # Test on first page
            page_num = 0
            
            # Convert with specified settings
            img = converter.convert(
                page_num, 
                vo, 
                highres_grayscale=config['highres']
            )
            
            # Analyze result
            arr = np.array(img)
            mean_val = arr.mean()
            non_white = np.sum(arr < 250)
            unique_colors = len(np.unique(arr))
            
            # Save result
            output_path = f"/home/ed/ghost-writer/focused_{config['name']}.png"
            img.save(output_path)
            
            print(f"   📐 Size: {img.size}")
            print(f"   📊 Mean pixel: {mean_val:.1f}")
            print(f"   📈 Non-white pixels: {non_white:,}")
            print(f"   🎨 Unique colors: {unique_colors}")
            print(f"   💾 Saved: {output_path}")
            
            if non_white > 0:
                print(f"   🎉 CONTENT FOUND!")
                successful_configs.append(config)
            else:
                print(f"   ⚠️  Still blank")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Tested {len(test_configs)} configurations")
    print(f"   Found content in {len(successful_configs)} configurations")
    
    if successful_configs:
        print(f"   🎉 Working configurations:")
        for config in successful_configs:
            print(f"      - {config['name']}")
        return True
    else:
        print(f"   ❌ No configurations produced visible content")
        return False

if __name__ == "__main__":
    success = test_image_conversion_options()
    
    if not success:
        print(f"\n💡 Conclusion: supernotelib parses the format correctly")
        print("   but image conversion still produces blank results.")
        print("   This suggests the issue is in the rendering pipeline,")
        print("   not the format parsing. Our RLE approach may be")
        print("   the right path after all.")