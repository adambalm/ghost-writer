#!/usr/bin/env python3
"""
Test GPT-4 Vision on our RLE decoded images
"""

import sys
import base64
from pathlib import Path
import os

def test_rle_images_with_vision():
    """Test GPT-4 Vision on our RLE decoded images"""
    
    print("🧪 Testing GPT-4 Vision on RLE Decoded Images")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        print("   Run: export OPENAI_API_KEY='your-key'")
        return
    
    # Test images to compare
    test_images = [
        {
            "name": "iPhone Photo (Ground Truth)",
            "path": "/home/ed/ghost-writer/iphone_photo.png",
            "expected": "Should read handwriting clearly"
        },
        {
            "name": "Our RLE Decoded Page 1", 
            "path": "/home/ed/ghost-writer/fixed_Page1_MainLayer.png",
            "expected": "Should show handwriting strokes if decoder works"
        },
        {
            "name": "Our RLE Decoded Page 2",
            "path": "/home/ed/ghost-writer/fixed_Page2_MainLayer.png", 
            "expected": "Should show handwriting strokes if decoder works"
        },
        {
            "name": "sn2md Blank Image",
            "path": "/home/ed/ghost-writer/sn2md_png_extraction/temp_20250807_035920.note_0.png",
            "expected": "Should be completely blank"
        }
    ]
    
    import openai
    client = openai.OpenAI(api_key=api_key)
    
    for test in test_images:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"   Expected: {test['expected']}")
        
        if not Path(test['path']).exists():
            print("   ❌ Image not found")
            continue
        
        # Encode image
        with open(test['path'], "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": "What do you see in this image? If there is handwritten text, transcribe it exactly. If the image is blank, say 'BLANK IMAGE'."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }}
                    ]
                }],
                max_tokens=500,
                temperature=0
            )
            
            result = response.choices[0].message.content
            cost = (response.usage.prompt_tokens * 0.01 / 1000) + (response.usage.completion_tokens * 0.03 / 1000)
            
            print(f"   💰 Cost: ${cost:.4f}")
            print(f"   🤖 Response: {result[:150]}{'...' if len(result) > 150 else ''}")
            
            # Save full result
            safe_name = test['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
            output_file = f"/home/ed/ghost-writer/vision_test_{safe_name}.txt"
            with open(output_file, 'w') as f:
                f.write(f"Image: {test['name']}\n")
                f.write(f"Path: {test['path']}\n")
                f.write(f"Expected: {test['expected']}\n")
                f.write(f"Cost: ${cost:.4f}\n")
                f.write("=" * 40 + "\n")
                f.write(result)
            
            print(f"   💾 Full result saved to: {output_file}")
            
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
    
    print(f"\n🎯 Vision Test Summary:")
    print("- iPhone photo should transcribe clearly")
    print("- RLE decoded should show if our decoder works") 
    print("- sn2md blank should confirm it's truly blank")
    print("- This will tell us if our RLE approach has merit")

if __name__ == "__main__":
    test_rle_images_with_vision()