#!/usr/bin/env python3
"""
Enhance RLE decoded images specifically for AI vision model readability
"""

from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from pathlib import Path

def enhance_for_ai_vision(image_path: str) -> str:
    """Enhance an RLE decoded image specifically for AI vision models"""
    
    print(f"🎨 Enhancing {Path(image_path).name} for AI vision...")
    
    # Load the image
    img = Image.open(image_path)
    arr = np.array(img)
    
    print(f"   📊 Original: {np.sum(arr < 255):,} non-white pixels")
    
    # Step 1: Make any non-white pixels much darker
    enhanced = arr.copy()
    enhanced = np.where(arr < 255, arr // 4, 255)  # Make dark pixels much darker
    
    # Step 2: Thicken strokes by dilation
    from scipy.ndimage import binary_dilation
    
    # Create binary mask of content
    content_mask = enhanced < 200
    
    if np.any(content_mask):
        # Dilate to thicken strokes
        structure = np.ones((3, 3))  # 3x3 dilation kernel
        dilated_mask = binary_dilation(content_mask, structure=structure, iterations=2)
        
        # Apply dilation - make dilated areas dark
        enhanced = np.where(dilated_mask, 64, 255)  # Very dark strokes on white background
        
        print(f"   ✅ Enhanced: {np.sum(enhanced < 255):,} non-white pixels")
    else:
        print(f"   ⚠️  No content found to enhance")
        return image_path
    
    # Step 3: Increase contrast even more
    enhanced_img = Image.fromarray(enhanced.astype(np.uint8))
    
    # Apply additional contrast enhancement
    enhancer = ImageEnhance.Contrast(enhanced_img)
    enhanced_img = enhancer.enhance(3.0)  # Very high contrast
    
    # Save enhanced version
    output_path = image_path.replace('.png', '_ai_enhanced.png')
    enhanced_img.save(output_path)
    
    print(f"   💾 Saved enhanced version: {output_path}")
    
    return output_path

def enhance_all_rle_images():
    """Enhance all our RLE decoded images for AI vision"""
    
    print("🚀 Enhancing All RLE Images for AI Vision")
    print("=" * 50)
    
    # Images to enhance
    rle_images = [
        "/home/ed/ghost-writer/fixed_Page1_MainLayer.png",
        "/home/ed/ghost-writer/fixed_Page2_MainLayer.png"
    ]
    
    enhanced_paths = []
    
    for image_path in rle_images:
        if Path(image_path).exists():
            try:
                enhanced_path = enhance_for_ai_vision(image_path)
                enhanced_paths.append(enhanced_path)
            except Exception as e:
                print(f"❌ Failed to enhance {image_path}: {e}")
        else:
            print(f"❌ Not found: {image_path}")
    
    return enhanced_paths

def test_enhanced_images_with_vision():
    """Test the enhanced images with GPT-4 Vision"""
    
    import os
    import base64
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Set API key first: export OPENAI_API_KEY='your-key'")
        return
    
    print(f"\n🤖 Testing Enhanced Images with GPT-4 Vision")
    print("=" * 55)
    
    enhanced_images = [
        "/home/ed/ghost-writer/fixed_Page1_MainLayer_ai_enhanced.png",
        "/home/ed/ghost-writer/fixed_Page2_MainLayer_ai_enhanced.png"
    ]
    
    import openai
    client = openai.OpenAI(api_key=api_key)
    
    for image_path in enhanced_images:
        if not Path(image_path).exists():
            print(f"❌ Enhanced image not found: {image_path}")
            continue
        
        print(f"\n🔍 Testing: {Path(image_path).name}")
        
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Can you see any handwritten text or marks in this image? If yes, transcribe what you can read. If the image appears blank, say 'BLANK IMAGE'."},
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
            
            print(f"   💰 Cost: ${cost:.4f}")
            print(f"   📝 Result: {result}")
            
            # Save result
            result_file = image_path.replace('.png', '_vision_result.txt')
            with open(result_file, 'w') as f:
                f.write(f"Image: {image_path}\n")
                f.write(f"Cost: ${cost:.4f}\n")
                f.write("Result:\n")
                f.write(result)
            
            if "BLANK IMAGE" not in result.upper():
                print(f"   🎉 SUCCESS! AI can see content!")
                return True
            else:
                print(f"   ❌ Still appears blank to AI")
                
        except Exception as e:
            print(f"   ❌ Vision test failed: {e}")
    
    return False

if __name__ == "__main__":
    # Step 1: Enhance images
    enhanced_paths = enhance_all_rle_images()
    
    if enhanced_paths:
        print(f"\n✅ Enhanced {len(enhanced_paths)} images")
        
        # Step 2: Test with AI vision
        success = test_enhanced_images_with_vision()
        
        if success:
            print(f"\n🎉 BREAKTHROUGH! Enhanced RLE images are readable by AI!")
            print("   Next: Integrate this enhancement into the main pipeline")
        else:
            print(f"\n⚠️  Enhancement didn't make images AI-readable")
            print("   Next: Explore Cloud export API or photo workflow")
    else:
        print(f"\n❌ No images were enhanced successfully")