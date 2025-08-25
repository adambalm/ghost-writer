#!/usr/bin/env python3
"""
Test Multi-Layer Extraction Against sn2md
==========================================

This script tests our new multi-layer extraction system against sn2md's output
to validate that we're closing the 96% pixel gap by implementing proper layer composition.

Expected results:
- Our multi-layer approach should extract 2.8M+ pixels (matching sn2md INVISIBLE mode)
- Should support RGBA output with transparency
- Should composite BGLAYER + MAINLAYER properly
"""

import sys
import os
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.supernote_parser import SupernoteParser, VisibilityOverlay, build_visibility_overlay
import numpy as np
from PIL import Image

def count_content_pixels(img):
    """Count non-white pixels in an image"""
    if img.mode == 'RGBA':
        # For RGBA images, count non-transparent pixels
        img_array = np.array(img)
        alpha = img_array[:, :, 3]
        # Count pixels that aren't fully transparent
        return np.count_nonzero(alpha > 10)
    else:
        # For RGB/L images, count non-white pixels
        img_array = np.array(img)
        if len(img_array.shape) == 3:
            # RGB - count pixels that aren't white
            return np.count_nonzero(np.any(img_array < 240, axis=2))
        else:
            # Grayscale - count pixels that aren't white
            return np.count_nonzero(img_array < 240)

def test_multilayer_extraction():
    """Test our new multi-layer extraction system"""
    
    print("🧪 Testing Multi-Layer Extraction System")
    print("=" * 50)
    
    # Test file - should be the same joe.note used in parallel tests
    test_file = Path("joe.note")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure joe.note is in the current directory")
        return
    
    parser = SupernoteParser()
    
    try:
        # Read the raw file data
        with open(test_file, 'rb') as f:
            data = f.read()
        
        print(f"📁 File size: {len(data):,} bytes")
        
        # Test different visibility modes
        visibility_modes = {
            'INVISIBLE': build_visibility_overlay(
                background=VisibilityOverlay.INVISIBLE,
                main=VisibilityOverlay.INVISIBLE
            ),
            'DEFAULT': build_visibility_overlay(
                background=VisibilityOverlay.DEFAULT,
                main=VisibilityOverlay.DEFAULT
            ),
            'VISIBLE': build_visibility_overlay(
                background=VisibilityOverlay.VISIBLE,
                main=VisibilityOverlay.VISIBLE
            )
        }
        
        results = []
        
        # Test each page with each visibility mode
        for page_num in [1, 2]:
            print(f"\n📄 Page {page_num}")
            print("-" * 20)
            
            for mode_name, visibility in visibility_modes.items():
                print(f"  {mode_name} mode: ", end="", flush=True)
                
                start_time = time.time()
                
                try:
                    # Use our new multi-layer extraction
                    img = parser.convert_page_with_layers(page_num, data, visibility)
                    
                    processing_time = time.time() - start_time
                    content_pixels = count_content_pixels(img)
                    
                    result = {
                        'page': page_num,
                        'visibility': mode_name,
                        'content_pixels': content_pixels,
                        'image_mode': img.mode,
                        'image_size': img.size,
                        'processing_time': processing_time,
                        'success': True
                    }
                    
                    print(f"{content_pixels:,} pixels ({processing_time:.3f}s)")
                    
                    # Save test image
                    output_path = f"multilayer_test_page{page_num}_{mode_name.lower()}.png"
                    img.save(output_path)
                    print(f"    💾 Saved: {output_path}")
                    
                except Exception as e:
                    print(f"❌ Failed: {e}")
                    result = {
                        'page': page_num,
                        'visibility': mode_name,
                        'error': str(e),
                        'success': False
                    }
                
                results.append(result)
        
        # Save detailed results
        results_file = f"multilayer_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'test_type': 'multilayer_extraction',
                'file': str(test_file),
                'results': results
            }, f, indent=2)
        
        print(f"\n📊 Results saved to: {results_file}")
        
        # Compare with expected sn2md values
        print(f"\n🎯 Comparison with sn2md baseline:")
        print("-" * 40)
        
        sn2md_targets = {
            1: {'INVISIBLE': 2859430, 'DEFAULT': 346713},
            2: {'INVISIBLE': 2693922, 'DEFAULT': 98451}
        }
        
        for result in results:
            if result.get('success') and result['visibility'] in ['INVISIBLE', 'DEFAULT']:
                page = result['page']
                mode = result['visibility']
                our_pixels = result['content_pixels']
                target = sn2md_targets.get(page, {}).get(mode)
                
                if target:
                    ratio = (our_pixels / target) * 100
                    gap = target - our_pixels
                    
                    print(f"Page {page} {mode}:")
                    print(f"  Our result:    {our_pixels:,} pixels")
                    print(f"  sn2md target:  {target:,} pixels")
                    print(f"  Achievement:   {ratio:.1f}% of target")
                    print(f"  Gap:           {gap:,} pixels")
                    
                    if ratio > 80:
                        print(f"  Status:        ✅ Close to target!")
                    elif ratio > 50:
                        print(f"  Status:        🟡 Moderate progress")
                    else:
                        print(f"  Status:        🔴 Still needs work")
                    print()
        
        print("\n🏁 Multi-layer extraction test complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multilayer_extraction()