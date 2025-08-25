#!/usr/bin/env python3
"""
Test supernotelib with 'loose' policy to handle newer formats
"""

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay
from pathlib import Path
import numpy as np

def test_loose_policy():
    """Test supernotelib with loose parsing policy"""
    
    print("🔄 Testing supernotelib with 'loose' policy")
    print("=" * 50)
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    # Try with loose policy
    print(f"📄 Loading with 'loose' policy: {note_path}")
    
    try:
        # Use loose policy for unknown signatures
        notebook = sn.load_notebook(note_path, policy='loose')
        print(f"✅ Notebook loaded successfully with loose policy")
        
        # Check what signature was detected
        print(f"🔍 Detected signature: {notebook.get_signature()}")
        print(f"🔍 Notebook type: {type(notebook)}")
        print(f"🔍 Supports highres grayscale: {notebook.supports_highres_grayscale}")
        print(f"🔍 Is realtime recognition: {notebook.is_realtime_recognition}")
        
        # Create converter
        converter = ImageConverter(notebook) 
        print("✅ ImageConverter created")
        
        # Try different visibility overlays
        visibility_options = [
            ("DEFAULT", VisibilityOverlay.DEFAULT),
            ("VISIBLE", VisibilityOverlay.VISIBLE), 
            ("HIDDEN", VisibilityOverlay.HIDDEN)
        ]
        
        total_pages = notebook.get_total_pages()
        print(f"📊 Total pages: {total_pages}")
        
        for vo_name, vo_value in visibility_options:
            print(f"\n🎨 Testing {vo_name} visibility overlay...")
            
            try:
                vo = sn.converter.build_visibility_overlay(background=vo_value, mainlayer=vo_value)
                print(f"   Built overlay: {vo}")
                
                for i in range(min(2, total_pages)):  # Test first 2 pages
                    print(f"   📄 Converting page {i+1}...")
                    
                    # Try high-res and normal
                    for highres in [True, False]:
                        try:
                            img = converter.convert(i, vo, highres_grayscale=highres)
                            
                            # Check content
                            arr = np.array(img)
                            mean_val = arr.mean()
                            non_white = np.sum(arr < 250)
                            
                            label = f"highres_{highres}_{vo_name}_page_{i+1}"
                            output_path = f"/home/ed/ghost-writer/loose_policy_{label}.png"
                            img.save(output_path)
                            
                            print(f"   ✅ {label}: mean={mean_val:.1f}, non-white={non_white:,}")
                            
                            if non_white > 0:
                                print(f"   🎉 FOUND CONTENT! Saved to: {output_path}")
                                return True  # Success!
                                
                        except Exception as e:
                            print(f"   ❌ {label} failed: {e}")
                            
            except Exception as e:
                print(f"   ❌ {vo_name} overlay failed: {e}")
        
        print(f"\n⚠️  All visibility overlays produced blank images")
        return False
        
    except Exception as e:
        print(f"❌ Failed to load with loose policy: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_metadata_parsing():
    """Test direct metadata parsing to see what supernotelib detects"""
    
    print(f"\n🔍 Testing direct metadata parsing")
    print("=" * 40)
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    try:
        with open(note_path, 'rb') as f:
            # Test both strict and loose policies
            for policy in ['strict', 'loose']:
                print(f"\n📋 Testing {policy} policy...")
                
                try:
                    f.seek(0)
                    metadata = sn.parser.parse_metadata(f, policy=policy)
                    
                    print(f"   ✅ Metadata parsed with {policy} policy")
                    print(f"   🔍 Signature: {metadata.signature}")
                    print(f"   📊 File size: {metadata.file_size}")
                    print(f"   📄 Total pages: {metadata.total_pages}")
                    
                    return True
                    
                except Exception as e:
                    print(f"   ❌ {policy} policy failed: {e}")
        
    except Exception as e:
        print(f"❌ File access failed: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 Comprehensive supernotelib Testing")
    print("=" * 60)
    
    # Test metadata parsing first
    metadata_success = test_direct_metadata_parsing()
    
    if metadata_success:
        # Test image conversion
        image_success = test_loose_policy()
        
        if image_success:
            print(f"\n🎉 SUCCESS: Found working configuration!")
        else:
            print(f"\n⚠️  Metadata parsing works, but image conversion produces blanks")
    else:
        print(f"\n❌ Metadata parsing failed completely")