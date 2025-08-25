#!/usr/bin/env python3
"""
Test vision AI transcription on handwriting sample
"""

import sys
import base64
from pathlib import Path
import json
import os

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_gpt4_vision_transcription():
    """Test GPT-4 Vision on handwriting transcription"""
    
    print("🔍 Testing GPT-4 Vision for Handwriting Transcription")
    print("=" * 60)
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Export your key: export OPENAI_API_KEY='your-key-here'")
        return
    
    image_path = "/home/ed/ghost-writer/iphone_photo.png"
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"📱 Testing image: {image_path}")
    
    # Encode image
    base64_image = encode_image(image_path)
    
    # Test with OpenAI API
    import openai
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Optimized prompt for handwriting transcription
        prompt = """Please transcribe the handwritten text in this image. 

Rules:
1. Transcribe exactly what you see, word for word
2. Preserve line breaks and paragraph structure  
3. Use [unclear] for any text you cannot read clearly
4. Do not add punctuation that isn't clearly written
5. Do not interpret or correct apparent mistakes

Transcription:"""
        
        print("🤖 Calling GPT-4 Vision API...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0
        )
        
        transcription = response.choices[0].message.content
        
        print("✅ Transcription completed!")
        print("=" * 40)
        print(transcription)
        print("=" * 40)
        
        # Save transcription
        output_file = "/home/ed/ghost-writer/transcription_gpt4v.txt"
        with open(output_file, 'w') as f:
            f.write(transcription)
        
        print(f"💾 Saved to: {output_file}")
        
        # Calculate cost
        # GPT-4o Vision: $0.01 per 1k input tokens (images ~1k tokens)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.01 / 1000) + (output_tokens * 0.03 / 1000)
        
        print(f"💰 Cost: ~${cost:.4f}")
        print(f"📊 Tokens: {input_tokens} in, {output_tokens} out")
        
        return transcription
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return None

def test_basic_semantic_search(transcription):
    """Test basic semantic search on transcription"""
    
    if not transcription:
        return
    
    print(f"\n🔍 Testing Basic Semantic Search")
    print("=" * 40)
    
    # Simple keyword search to start
    test_queries = [
        "Joe",
        "Italian", 
        "Korean",
        "temper",
        "swings"
    ]
    
    for query in test_queries:
        if query.lower() in transcription.lower():
            # Find context around the match
            text_lower = transcription.lower()
            pos = text_lower.find(query.lower())
            start = max(0, pos - 30)
            end = min(len(transcription), pos + len(query) + 30)
            context = transcription[start:end].strip()
            
            print(f"✅ '{query}' found: ...{context}...")
        else:
            print(f"❌ '{query}' not found")

if __name__ == "__main__":
    transcription = test_gpt4_vision_transcription()
    test_basic_semantic_search(transcription)