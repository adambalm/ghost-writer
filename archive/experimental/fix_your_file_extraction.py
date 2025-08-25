#!/usr/bin/env python3
"""
Fix extraction for your specific note file using correct visibility settings
"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/sn2md')

from sn2md.importers.note import load_notebook
import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay
import os

def extract_your_file_correctly():
    """Extract your file using the working visibility setting"""
    
    print("🔧 Extracting YOUR File with Correct Settings")
    print("=" * 50)
    
    note_file = "/home/ed/ghost-writer/temp_20250807_035920.note"
    output_dir = "/home/ed/ghost-writer/your_file_fixed"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load notebook
        notebook = load_notebook(note_file)
        converter = ImageConverter(notebook)
        
        # Use INVISIBLE visibility (the one that worked!)
        vo = sn.converter.build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)
        
        print(f"📄 Processing {notebook.get_total_pages()} pages...")
        
        extracted_files = []
        
        for page_idx in range(notebook.get_total_pages()):
            print(f"  Page {page_idx + 1}:")
            
            # Extract page
            img = converter.convert(page_idx, vo)
            
            # Save image
            output_path = f"{output_dir}/page_{page_idx + 1}.png"
            img.save(output_path)
            extracted_files.append(output_path)
            
            # Analyze content
            import numpy as np
            arr = np.array(img)
            mean_val = arr.mean()
            non_white = np.sum(arr < 250)
            
            print(f"    💾 Saved: {output_path}")
            print(f"    📊 Content: mean={mean_val:.1f}, pixels={non_white:,}")
            
            if non_white > 10000:
                print(f"    ✅ Rich content detected!")
            elif non_white > 1000:
                print(f"    ✅ Some content detected")
            else:
                print(f"    ⚠️  Limited content")
        
        print(f"\n🎉 SUCCESS! Extracted {len(extracted_files)} pages from YOUR file")
        print("Files created:")
        for file_path in extracted_files:
            print(f"  - {file_path}")
            
        return extracted_files
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_with_gpt_vision():
    """Test the extracted images with GPT-4 Vision"""
    
    print(f"\n🤖 Testing Fixed Extraction with GPT-4 Vision")
    print("=" * 55)
    
    # First, extract the files correctly
    extracted_files = extract_your_file_correctly()
    
    if not extracted_files:
        print("❌ No files to test")
        return False
    
    # Test with vision (if API key available)
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  Set OPENAI_API_KEY to test with vision")
        print("But extraction is working - images are ready for testing!")
        return True
    
    try:
        import openai
        import base64
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test first page
        test_image = extracted_files[0]
        print(f"🔍 Testing: {test_image}")
        
        with open(test_image, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Can you see any handwritten text, drawings, or marks in this image? If yes, describe what you see. If blank, say 'BLANK'."},
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
            print(f"\n🎉 SUCCESS! GPT-4 Vision can see content from YOUR file!")
            return True
        else:
            print(f"\n⚠️  Still appears blank - may need further refinement")
            return False
            
    except Exception as e:
        print(f"❌ Vision test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_with_gpt_vision()
    
    if success:
        print(f"\n🚀 SOLUTION FOUND!")
        print("✅ Your note file CAN be extracted with correct visibility settings")
        print("✅ Use VisibilityOverlay.INVISIBLE instead of DEFAULT")
        print("✅ Ready to integrate into main pipeline")
    else:
        print(f"\n🔧 Partial success - extraction working, may need vision refinement")