#!/usr/bin/env python3
"""
Final comparison: iPhone photo vs our best RLE decoded images
"""

import sys
import base64
from pathlib import Path
import os

def test_final_comparison():
    """Compare iPhone photo vs our RLE decoded images with GPT-4 Vision"""
    
    print("🏁 Final Vision Comparison Test")
    print("=" * 40)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Set API key: export OPENAI_API_KEY='your-key'")
        return
    
    # Test the best candidates
    test_images = [
        {
            "name": "iPhone Photo (Ground Truth)",
            "path": "/home/ed/ghost-writer/iphone_photo.png",
            "description": "Original handwriting photo taken with iPhone"
        },
        {
            "name": "Our RLE Decoded (Coordinate-based)", 
            "path": "/home/ed/ghost-writer/fixed_Page1_MainLayer.png",
            "description": "Our reverse-engineered RLE decoder output"
        }
    ]
    
    import openai
    client = openai.OpenAI(api_key=api_key)
    
    results = []
    
    for test in test_images:
        print(f"\n🔍 Testing: {test['name']}")
        
        if not Path(test['path']).exists():
            print("   ❌ Image not found")
            continue
        
        with open(test['path'], "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please transcribe any handwritten text you see in this image. If you can read it clearly, transcribe it exactly. If it's unclear or you see no text, say 'NO TEXT DETECTED'."},
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
            print(f"   📝 Result: {result[:100]}{'...' if len(result) > 100 else ''}")
            
            results.append({
                "name": test['name'],
                "result": result,
                "cost": cost,
                "readable": "NO TEXT DETECTED" not in result.upper()
            })
            
            # Save detailed result
            filename = test['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
            output_path = f"/home/ed/ghost-writer/final_test_{filename}.txt"
            with open(output_path, 'w') as f:
                f.write(f"Test: {test['name']}\n")
                f.write(f"Description: {test['description']}\n")
                f.write(f"Cost: ${cost:.4f}\n")
                f.write("=" * 40 + "\n")
                f.write(result)
            
            print(f"   💾 Saved: {output_path}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Final comparison
    print(f"\n📊 Final Comparison:")
    print("=" * 50)
    
    for result in results:
        status = "✅ READABLE" if result['readable'] else "❌ NOT READABLE"
        print(f"{status:15} | {result['name']}")
    
    # Determine next steps
    rle_readable = any(r['readable'] and 'RLE' in r['name'] for r in results)
    
    if rle_readable:
        print(f"\n🎉 SUCCESS! Our RLE decoder produces readable content!")
        print("   Next: Build complete pipeline with this decoder")
    else:
        print(f"\n⚠️  RLE decoder needs more work")
        print("   Options: 1) Improve RLE algorithm, 2) Use Cloud export, 3) Photo workflow")

if __name__ == "__main__":
    test_final_comparison()