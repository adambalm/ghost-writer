#!/usr/bin/env python3
from PIL import Image
import numpy as np

img = Image.open('/home/ed/ghost-writer/temp_20250807_035920.note_page1.png')
print(f'Image size: {img.size}')
print(f'Image mode: {img.mode}')
print(f'Image format: {img.format}')

arr = np.array(img)
print(f'Image shape: {arr.shape}')
print(f'Min pixel value: {arr.min()}')
print(f'Max pixel value: {arr.max()}')
print(f'Mean pixel value: {arr.mean():.1f}')

# Check if mostly white (blank)
if arr.mean() > 250:
    print("⚠️  Image appears to be mostly white/blank")
elif arr.mean() < 50:
    print("⚠️  Image appears to be mostly black")
else:
    print("✅ Image contains varying content")

# Count non-white pixels
non_white = np.sum(arr < 250)
total_pixels = arr.size
print(f'Non-white pixels: {non_white:,} / {total_pixels:,} ({100*non_white/total_pixels:.1f}%)')