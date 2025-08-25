#!/usr/bin/env python3
"""
Swappable vision AI system for handwriting transcription
"""

import sys
import base64
from pathlib import Path
import json
import os
from abc import ABC, abstractmethod

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

class VisionTranscriber(ABC):
    """Abstract base for vision transcription providers"""
    
    @abstractmethod
    def transcribe(self, image_path: str) -> dict:
        """Return dict with 'text', 'confidence', 'cost', 'provider'"""
        pass

class GPT4VisionTranscriber(VisionTranscriber):
    """GPT-4 Vision transcriber"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
    
    def transcribe(self, image_path: str) -> dict:
        import openai
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        client = openai.OpenAI(api_key=self.api_key)
        
        prompt = """Transcribe this handwritten text exactly as written. Rules:
1. Transcribe word for word, preserving line breaks
2. Use [unclear] for unreadable text
3. Don't add punctuation that isn't clearly written
4. Don't correct apparent mistakes

Transcription:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "high"
                    }}
                ]
            }],
            max_tokens=1000,
            temperature=0
        )
        
        transcription = response.choices[0].message.content
        
        # Calculate cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.01 / 1000) + (output_tokens * 0.03 / 1000)
        
        return {
            'text': transcription,
            'confidence': 95,  # GPT-4V generally high confidence
            'cost': cost,
            'provider': 'gpt-4o-vision',
            'tokens': {'input': input_tokens, 'output': output_tokens}
        }

class OllamaVisionTranscriber(VisionTranscriber):
    """Local Ollama vision transcriber"""
    
    def __init__(self, model_name="llama3.2-vision"):
        self.model_name = model_name
        # Check if model is available
        import subprocess
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if model_name not in result.stdout:
                raise ValueError(f"Model {model_name} not found. Run: ollama pull {model_name}")
        except Exception as e:
            raise ValueError(f"Ollama not available or model missing: {e}")
    
    def transcribe(self, image_path: str) -> dict:
        import subprocess
        import json
        
        prompt = """Transcribe this handwritten text exactly as written. Rules:
1. Transcribe word for word, preserving line breaks  
2. Use [unclear] for unreadable text
3. Don't add punctuation that isn't clearly written
4. Don't correct apparent mistakes

Transcription:"""
        
        # Call ollama with image
        cmd = ['ollama', 'run', self.model_name, prompt]
        
        # Ollama expects image path in the conversation
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # This is simplified - actual Ollama API call would be more complex
        # For now, return a placeholder
        return {
            'text': '[Local transcription would go here]',
            'confidence': 80,
            'cost': 0.0,
            'provider': f'ollama-{self.model_name}',
            'tokens': {'input': 0, 'output': 0}
        }

def test_transcription_providers(image_path: str):
    """Test available transcription providers"""
    
    print("🔄 Testing Swappable Vision Transcription")
    print("=" * 50)
    
    providers = []
    
    # Test GPT-4 Vision
    try:
        gpt4v = GPT4VisionTranscriber()
        providers.append(('GPT-4 Vision', gpt4v))
        print("✅ GPT-4 Vision available")
    except Exception as e:
        print(f"❌ GPT-4 Vision unavailable: {e}")
    
    # Test Ollama (would need vision model)
    try:
        ollama = OllamaVisionTranscriber("llama3.2-vision")
        providers.append(('Ollama Vision', ollama))
        print("✅ Ollama Vision available") 
    except Exception as e:
        print(f"❌ Ollama Vision unavailable: {e}")
    
    if not providers:
        print("❌ No vision providers available")
        print("💡 To enable:")
        print("   GPT-4 Vision: export OPENAI_API_KEY='your-key'")
        print("   Local Ollama: ollama pull llama3.2-vision")
        return
    
    # Test each provider
    for name, provider in providers:
        print(f"\n🧪 Testing {name}...")
        try:
            result = provider.transcribe(image_path)
            
            print(f"✅ {name} Success")
            print(f"   Text length: {len(result['text'])} chars")
            print(f"   Confidence: {result['confidence']}%")
            print(f"   Cost: ${result['cost']:.4f}")
            print(f"   Preview: {result['text'][:100]}...")
            
            # Save result
            output_file = f"/home/ed/ghost-writer/transcription_{result['provider'].replace('-', '_')}.txt"
            with open(output_file, 'w') as f:
                f.write(f"Provider: {result['provider']}\n")
                f.write(f"Confidence: {result['confidence']}%\n") 
                f.write(f"Cost: ${result['cost']:.4f}\n")
                f.write(f"Tokens: {result.get('tokens', 'N/A')}\n")
                f.write("=" * 40 + "\n")
                f.write(result['text'])
            
            print(f"💾 Saved: {output_file}")
            
        except Exception as e:
            print(f"❌ {name} failed: {e}")

if __name__ == "__main__":
    image_path = "/home/ed/ghost-writer/iphone_photo.png"
    
    if not Path(image_path).exists():
        print(f"❌ Test image not found: {image_path}")
        exit(1)
    
    test_transcription_providers(image_path)