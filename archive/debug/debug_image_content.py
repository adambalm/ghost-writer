#!/usr/bin/env python3
"""
Debug what's actually in the extracted images
"""

from PIL import Image
import numpy as np

def analyze_image_deeply(image_path):
    """Deep analysis of what's in an image"""
    
    print(f"🔍 Deep Image Analysis: {image_path}")
    print("=" * 50)
    
    try:
        img = Image.open(image_path)
        arr = np.array(img)
        
        print(f"📊 Basic Stats:")
        print(f"   Size: {img.size}")
        print(f"   Mode: {img.mode}")
        print(f"   Array shape: {arr.shape}")
        print(f"   Data type: {arr.dtype}")
        
        print(f"\n📊 Pixel Value Analysis:")
        print(f"   Min value: {arr.min()}")
        print(f"   Max value: {arr.max()}")
        print(f"   Mean: {arr.mean():.2f}")
        print(f"   Std dev: {arr.std():.2f}")
        
        # Count pixels by value
        unique_vals, counts = np.unique(arr, return_counts=True)
        print(f"\n📊 Pixel Value Distribution:")
        for val, count in zip(unique_vals[:10], counts[:10]):  # Show top 10
            percentage = (count / arr.size) * 100
            print(f"   Value {val}: {count:,} pixels ({percentage:.1f}%)")
        
        if len(unique_vals) > 10:
            print(f"   ... and {len(unique_vals) - 10} more unique values")
        
        # Check different thresholds
        print(f"\n📊 Content Detection (different thresholds):")
        thresholds = [255, 254, 250, 240, 200, 150]
        for thresh in thresholds:
            non_white = np.sum(arr < thresh)
            percentage = (non_white / arr.size) * 100
            print(f"   < {thresh}: {non_white:,} pixels ({percentage:.1f}%)")
        
        # Look for patterns
        print(f"\n📊 Pattern Analysis:")
        if arr.ndim == 3:  # Color image
            for i, channel in enumerate(['R', 'G', 'B']):
                channel_data = arr[:, :, i]
                unique_channel_vals = len(np.unique(channel_data))
                print(f"   {channel} channel: {unique_channel_vals} unique values")
        
        # Check if image is actually grayscale
        if arr.ndim == 3 and arr.shape[2] == 3:
            is_grayscale = np.all(arr[:,:,0] == arr[:,:,1]) and np.all(arr[:,:,1] == arr[:,:,2])
            print(f"   Is grayscale: {is_grayscale}")
        
        # Sample some pixel values from different areas
        height, width = arr.shape[:2]
        print(f"\n📊 Sample Pixels:")
        locations = [
            ("Top-left", 0, 0),
            ("Top-right", 0, width-1),
            ("Center", height//2, width//2),
            ("Bottom-left", height-1, 0),
            ("Bottom-right", height-1, width-1)
        ]
        
        for name, y, x in locations:
            if arr.ndim == 3:
                pixel_val = arr[y, x, :]
                print(f"   {name} ({y},{x}): {pixel_val}")
            else:
                pixel_val = arr[y, x]
                print(f"   {name} ({y},{x}): {pixel_val}")
        
        return {
            "has_visible_content": arr.min() < 240,
            "unique_values": len(unique_vals),
            "non_white_250": int(np.sum(arr < 250)),
            "non_white_240": int(np.sum(arr < 240))
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def compare_images():
    """Compare our extraction vs the working community example"""
    
    print("🔍 COMPARATIVE IMAGE ANALYSIS")
    print("=" * 60)
    
    images_to_test = [
        "/home/ed/ghost-writer/results/20250814_041548_page_1_invisible.png",
        "/home/ed/ghost-writer/results/20250814_041548_page_1_default.png",
        "/home/ed/ghost-writer/visual_library_test/visual_library_test_0.png"
    ]
    
    for image_path in images_to_test:
        if Path(image_path).exists():
            result = analyze_image_deeply(image_path)
            print()
        else:
            print(f"❌ Not found: {image_path}\n")

if __name__ == "__main__":
    from pathlib import Path
    compare_images()