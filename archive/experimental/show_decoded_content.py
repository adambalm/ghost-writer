#!/usr/bin/env python3
"""
Show what we decoded from the handwriting in text format
"""

from PIL import Image
import numpy as np

def show_image_as_text(image_path: str, name: str):
    """Convert image to ASCII art to show content"""
    
    print(f"\n📄 {name}")
    print("=" * 60)
    
    img = Image.open(image_path)
    arr = np.array(img)
    
    # Find the area with content
    dark_pixels = arr < 200
    if not np.any(dark_pixels):
        print("No content found")
        return
    
    # Find bounding box
    rows_with_content = np.any(dark_pixels, axis=1)
    cols_with_content = np.any(dark_pixels, axis=0)
    
    min_row = np.where(rows_with_content)[0].min()
    max_row = np.where(rows_with_content)[0].max()
    min_col = np.where(cols_with_content)[0].min()
    max_col = np.where(cols_with_content)[0].max()
    
    print(f"Content found in area: rows {min_row}-{max_row}, cols {min_col}-{max_col}")
    print(f"Content size: {max_col-min_col+1} x {max_row-min_row+1} pixels")
    
    # Extract content area
    content_area = arr[min_row:max_row+1, min_col:max_col+1]
    
    # Show first portion as ASCII
    print("\\nFirst 1000 pixels of content (as ASCII art):")
    print("▓ = dark pixels, ░ = light pixels, · = white")
    
    # Sample the content to fit in terminal
    sample_height = min(20, content_area.shape[0])
    sample_width = min(100, content_area.shape[1])
    
    step_h = max(1, content_area.shape[0] // sample_height)
    step_w = max(1, content_area.shape[1] // sample_width)
    
    sampled = content_area[::step_h, ::step_w]
    
    for row in sampled:
        line = ""
        for pixel in row:
            if pixel < 100:
                line += "▓"  # Very dark
            elif pixel < 180:
                line += "░"  # Medium
            elif pixel < 240:
                line += "·"  # Light
            else:
                line += " "  # White
        print(line)
    
    # Show pixel value histogram
    unique_vals = np.unique(content_area)
    print(f"\\nPixel values in content area: {len(unique_vals)} unique values")
    print(f"Range: {unique_vals.min()} to {unique_vals.max()}")
    
    # Show darkest areas more clearly
    very_dark = content_area < 50
    if np.any(very_dark):
        dark_count = np.sum(very_dark)
        print(f"Very dark pixels (< 50): {dark_count:,}")

# Show both pages
show_image_as_text("/home/ed/ghost-writer/decoded_Page1_MainLayer.png", "Page 1 - Your Handwriting (Decoded)")
show_image_as_text("/home/ed/ghost-writer/decoded_Page2_MainLayer.png", "Page 2 - Your Handwriting (Decoded)")