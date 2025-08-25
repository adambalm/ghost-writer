#!/usr/bin/env python3
"""
Fix transparency issues in extracted Supernote images
"""

from PIL import Image
import numpy as np
from pathlib import Path

def fix_transparent_strokes(image_path, output_path=None):
    """Convert transparent 'content' pixels to visible strokes"""
    
    print(f"🔧 Fixing transparency in: {image_path}")
    
    try:
        img = Image.open(image_path)
        arr = np.array(img)
        
        print(f"   Original: {img.mode} {img.size}")
        
        if img.mode == 'RGBA':
            # RGBA image with transparency
            rgb = arr[:, :, :3]  # RGB channels
            alpha = arr[:, :, 3]  # Alpha channel
            
            print(f"   Alpha channel stats: min={alpha.min()}, max={alpha.max()}")
            print(f"   Transparent pixels: {np.sum(alpha < 255):,}")
            
            # Method 1: Convert transparent areas to black strokes
            # Where alpha is 0 (transparent), make it black (0, 0, 0)
            # Where alpha is 255 (opaque), keep original (should be white)
            
            fixed_rgb = rgb.copy()
            transparent_mask = alpha < 255
            
            print(f"   Converting {np.sum(transparent_mask):,} transparent pixels to black strokes")
            
            # Set transparent pixels to black
            fixed_rgb[transparent_mask] = [0, 0, 0]  # Black strokes
            
            # Create opaque RGB image
            fixed_img = Image.fromarray(fixed_rgb, 'RGB')
            
        elif img.mode == 'RGB':
            print("   Already RGB - no transparency to fix")
            fixed_img = img
        else:
            print(f"   Unsupported mode: {img.mode}")
            return None
        
        # Save fixed image
        if output_path is None:
            output_path = str(image_path).replace('.png', '_fixed.png')
        
        fixed_img.save(output_path)
        print(f"   ✅ Saved fixed image: {output_path}")
        
        # Analyze the fixed image
        fixed_arr = np.array(fixed_img)
        unique_vals, counts = np.unique(fixed_arr.flatten(), return_counts=True)
        content_pixels = np.sum(fixed_arr < 250)
        
        print(f"   📊 Fixed image: {len(unique_vals)} unique values, {content_pixels:,} content pixels")
        
        return output_path
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None

def fix_all_extractions():
    """Fix all extracted images that have transparency issues"""
    
    print("🚀 Fixing All Transparent Extractions")
    print("=" * 50)
    
    results_dir = Path("/home/ed/ghost-writer/results")
    invisible_images = list(results_dir.glob("*_invisible.png"))
    
    fixed_files = []
    
    for img_path in invisible_images:
        fixed_path = fix_transparent_strokes(str(img_path))
        if fixed_path:
            fixed_files.append(fixed_path)
    
    print(f"\n✅ Fixed {len(fixed_files)} images")
    
    # Test one with vision if API key available
    if fixed_files:
        test_with_vision(fixed_files[0])
    
    return fixed_files

def test_with_vision(image_path):
    """Test a fixed image with GPT-4 Vision"""
    
    print(f"\n🤖 Testing Fixed Image with Vision: {image_path}")
    print("=" * 60)
    
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  Set OPENAI_API_KEY to test vision")
        return
    
    try:
        import openai
        import base64
        
        client = openai.OpenAI(api_key=api_key)
        
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Can you see any handwritten text, drawings, or marks in this image? If yes, describe or transcribe what you see. If the image appears blank, say 'BLANK IMAGE'."},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "high"
                    }}
                ]
            }],
            max_tokens=300,
            temperature=0
        )
        
        result = response.choices[0].message.content
        cost = (response.usage.prompt_tokens * 0.01 / 1000) + (response.usage.completion_tokens * 0.03 / 1000)
        
        print(f"💰 Cost: ${cost:.4f}")
        print(f"📝 Result: {result}")
        
        if "BLANK" not in result.upper():
            print(f"\n🎉 SUCCESS! Fixed image is readable by AI!")
            
            # Save result
            result_file = str(image_path).replace('.png', '_vision_result.txt')
            with open(result_file, 'w') as f:
                f.write(f"Fixed image: {image_path}\n")
                f.write(f"Cost: ${cost:.4f}\n")
                f.write("=" * 40 + "\n")
                f.write(result)
            
            return True
        else:
            print(f"\n⚠️  Still appears blank - may need different approach")
            return False
            
    except Exception as e:
        print(f"❌ Vision test failed: {e}")
        return False

if __name__ == "__main__":
    fixed_files = fix_all_extractions()
    
    if fixed_files:
        print(f"\n💡 Fixed images ready for testing:")
        for file_path in fixed_files:
            print(f"   - {file_path}")
        print(f"\n🌐 Restart web server to see fixed images")
    else:
        print(f"\n❌ No images were fixed")