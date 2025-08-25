#!/usr/bin/env python3
"""
Test local models vs OpenAI for transcription
"""

import sys
from pathlib import Path
import time
import json
import base64
from datetime import datetime

project_root = Path("/home/ed/ghost-writer")

def test_openai_transcription(image_path, api_key):
    """Test OpenAI GPT-4 Vision transcription"""
    
    print("🌐 Testing OpenAI GPT-4 Vision")
    print("-" * 35)
    
    if not api_key:
        return {"error": "No API key provided", "approach": "openai"}
    
    try:
        import openai
        
        start_time = time.time()
        
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe any handwritten text you see in this image. Be precise and complete. If you see no text, say 'NO TEXT DETECTED'."},
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
        processing_time = time.time() - start_time
        
        print(f"⏱️  Time: {processing_time:.2f}s")
        print(f"💰 Cost: ${cost:.4f}")
        print(f"📝 Result: {result[:100]}{'...' if len(result) > 100 else ''}")
        
        return {
            "approach": "openai",
            "model": "gpt-4o",
            "transcription": result,
            "cost": cost,
            "processing_time": processing_time,
            "tokens": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens
            },
            "success": "NO TEXT DETECTED" not in result.upper()
        }
        
    except Exception as e:
        return {"error": str(e), "approach": "openai"}

def test_ollama_transcription(image_path, model_name="llava"):
    """Test local Ollama model transcription"""
    
    print(f"🖥️  Testing Ollama {model_name}")
    print("-" * 35)
    
    try:
        import requests
        
        start_time = time.time()
        
        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            if response.status_code != 200:
                return {"error": "Ollama not running", "approach": "ollama"}
        except requests.exceptions.RequestException:
            return {"error": "Ollama not accessible", "approach": "ollama"}
        
        # Encode image
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        # Call Ollama API
        payload = {
            "model": model_name,
            "prompt": "Transcribe any handwritten text you see in this image. Be precise and complete. If you see no text, say 'NO TEXT DETECTED'.",
            "images": [base64_image],
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60  # Local models can be slow
        )
        
        if response.status_code == 200:
            result_data = response.json()
            result = result_data.get("response", "")
            processing_time = time.time() - start_time
            
            print(f"⏱️  Time: {processing_time:.2f}s")
            print(f"💰 Cost: $0.00 (local)")
            print(f"📝 Result: {result[:100]}{'...' if len(result) > 100 else ''}")
            
            return {
                "approach": "ollama",
                "model": model_name,
                "transcription": result,
                "cost": 0.0,
                "processing_time": processing_time,
                "success": "NO TEXT DETECTED" not in result.upper()
            }
        else:
            return {"error": f"Ollama API error: {response.status_code}", "approach": "ollama"}
            
    except Exception as e:
        return {"error": str(e), "approach": "ollama"}

def test_llamacpp_transcription(image_path):
    """Test llama.cpp with vision model"""
    
    print("🦙 Testing llama.cpp Vision")
    print("-" * 30)
    
    try:
        # This would require llama.cpp with vision model
        # For now, return placeholder
        return {
            "error": "llama.cpp vision not implemented yet", 
            "approach": "llamacpp",
            "note": "Would need llama.cpp compiled with vision support and a vision model like LLaVA"
        }
        
    except Exception as e:
        return {"error": str(e), "approach": "llamacpp"}

def compare_transcription_approaches(image_path, openai_key=None):
    """Compare different transcription approaches"""
    
    print(f"🔬 Transcription Approach Comparison")
    print("=" * 50)
    print(f"📄 Testing image: {image_path}")
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return None
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "image_path": str(image_path),
        "approaches": []
    }
    
    # Test OpenAI
    if openai_key:
        openai_result = test_openai_transcription(image_path, openai_key)
        results["approaches"].append(openai_result)
    else:
        print("⚠️  Skipping OpenAI (no API key)")
    
    print()
    
    # Test Ollama
    ollama_result = test_ollama_transcription(image_path)
    results["approaches"].append(ollama_result)
    
    print()
    
    # Test llama.cpp (placeholder)
    llamacpp_result = test_llamacpp_transcription(image_path)
    results["approaches"].append(llamacpp_result)
    
    # Summary
    print(f"\n📊 Comparison Summary:")
    print("=" * 30)
    
    for approach in results["approaches"]:
        if "error" in approach:
            print(f"❌ {approach['approach']}: {approach['error']}")
        else:
            success = "✅" if approach.get("success", False) else "❌"
            cost = f"${approach['cost']:.4f}" if approach['cost'] > 0 else "Free"
            time_str = f"{approach['processing_time']:.1f}s"
            print(f"{success} {approach['approach']} ({approach.get('model', 'unknown')}): {time_str}, {cost}")
    
    # Recommendations
    working_approaches = [a for a in results["approaches"] if "error" not in a and a.get("success", False)]
    
    print(f"\n💡 Recommendations:")
    if not working_approaches:
        print("  ❌ No approaches successfully transcribed the image")
        print("  - Check if image contains readable handwriting")
        print("  - Try different image extraction settings")
    elif len(working_approaches) == 1:
        approach = working_approaches[0]
        print(f"  ✅ Use {approach['approach']} (only working option)")
    else:
        # Compare working approaches
        fastest = min(working_approaches, key=lambda x: x['processing_time'])
        cheapest = min(working_approaches, key=lambda x: x['cost'])
        
        print(f"  🏎️  Fastest: {fastest['approach']} ({fastest['processing_time']:.1f}s)")
        print(f"  💰 Cheapest: {cheapest['approach']} (${cheapest['cost']:.4f})")
        
        if fastest['cost'] == 0:
            print(f"  🎯 Recommended: {fastest['approach']} (fast + free)")
        elif cheapest['processing_time'] < 10:
            print(f"  🎯 Recommended: {cheapest['approach']} (good speed + cost)")
    
    # Save results
    results_file = project_root / "transcription_comparison.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

def main():
    """Test transcription with the best extracted image"""
    
    print("🔬 Local vs Cloud Transcription Testing")
    print("=" * 45)
    
    # Find the best extracted image
    results_dir = project_root / "results"
    if not results_dir.exists():
        print("❌ No results directory found. Run extraction first.")
        return
    
    # Look for images with good content
    image_files = list(results_dir.glob("*.png"))
    if not image_files:
        print("❌ No extracted images found")
        return
    
    # Pick a good candidate (look for default visibility first, then others)
    test_image = None
    for img in image_files:
        if "default" in img.name.lower():
            test_image = img
            break
    
    if not test_image:
        test_image = image_files[0]  # Fallback to first image
    
    print(f"📄 Testing with: {test_image.name}")
    
    # Get OpenAI key if available
    import os
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        openai_key = input("OpenAI API key (optional, press Enter to skip): ").strip()
        if not openai_key:
            openai_key = None
    
    # Run comparison
    results = compare_transcription_approaches(test_image, openai_key)
    
    return results

if __name__ == "__main__":
    main()