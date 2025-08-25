#!/usr/bin/env python3
"""
Test script to validate Qwen2.5-VL as a unified OCR provider
"""

import subprocess
import time
import base64
from pathlib import Path

def qwen_ocr_test(image_path: str) -> dict:
    """Test Qwen2.5-VL for OCR using the web app's proven method"""
    
    try:
        start_time = time.time()
        
        # Use the exact same method as web_viewer_demo_simple.py
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Call Ollama directly (same as web app method)
        prompt = "Please transcribe all the handwritten text you can see in this image. Return only the text content, no additional commentary."
        
        result = subprocess.run([
            "ollama", "run", "qwen2.5vl:7b",
            prompt,
            str(image_path)  # Pass image path directly
        ], capture_output=True, text=True, timeout=30)
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            transcribed_text = result.stdout.strip()
            return {
                "success": True,
                "text": transcribed_text,
                "provider": "qwen2.5vl",
                "time": processing_time,
                "cost": 0.0,  # FREE
                "confidence": 0.9  # High confidence for local vision models
            }
        else:
            return {
                "success": False,
                "error": f"Ollama error: {result.stderr}",
                "provider": "qwen2.5vl",
                "time": processing_time
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Qwen processing timeout (30s)",
            "provider": "qwen2.5vl"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "provider": "qwen2.5vl"
        }

def test_against_existing_results():
    """Test Qwen against existing extracted images"""
    
    print("🧪 Testing Qwen2.5-VL as Unified OCR Provider")
    print("=" * 50)
    
    # Test with some extracted images
    test_images = [
        "./reference-only-analysis/exact_sn2md_page_1.png",
        "./reference-only-analysis/exact_sn2md_page_2.png"
    ]
    
    for image_path in test_images:
        if Path(image_path).exists():
            print(f"\n📄 Testing: {image_path}")
            result = qwen_ocr_test(image_path)
            
            if result["success"]:
                print(f"✅ Success: {result['time']:.2f}s")
                print(f"📝 Text: {result['text'][:100]}...")
                print(f"🔧 Provider: {result['provider']}")
                print(f"💰 Cost: FREE")
            else:
                print(f"❌ Failed: {result['error']}")
        else:
            print(f"⚠️  Image not found: {image_path}")
    
    print("\n🎯 CONCLUSION:")
    print("If Qwen works here, we can easily unify the OCR architecture!")

if __name__ == "__main__":
    test_against_existing_results()