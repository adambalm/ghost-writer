#!/usr/bin/env python3
"""
Test OCR on the iPhone photo of the original Supernote handwriting
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.ocr_providers import TesseractOCR

def test_iphone_photo_ocr():
    """Test OCR on the iPhone photo of original handwriting"""
    
    print("📱 Testing OCR on iPhone Photo of Original Handwriting")
    print("=" * 60)
    
    image_path = "/home/ed/ghost-writer/iphone_photo.png"
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    # Test multiple OCR configurations
    configs = [
        {"name": "Default", "psm": 6, "oem": 3},
        {"name": "Single Block", "psm": 6, "oem": 1},
        {"name": "Sparse Text", "psm": 11, "oem": 3},
        {"name": "Raw Line", "psm": 13, "oem": 3}
    ]
    
    print(f"🖼️  Testing: {image_path}")
    
    for config in configs:
        print(f"\n🔍 Testing {config['name']} configuration...")
        
        try:
            tesseract_config = {
                "executable_path": "tesseract",
                "language": "eng",
                "psm": config["psm"],
                "oem": config["oem"]
            }
            
            ocr = TesseractOCR(tesseract_config)
            result = ocr.extract_text(image_path)
            
            print(f"   Confidence: {result.confidence:.1f}%")
            print(f"   Text length: {len(result.text)} characters")
            
            if result.text.strip():
                print(f"   First 200 chars: '{result.text.strip()[:200]}{'...' if len(result.text) > 200 else ''}'")
                
                # Show full text if confidence is good
                if result.confidence > 50:
                    print(f"\n📝 Full extracted text:")
                    print("-" * 40)
                    print(result.text)
                    print("-" * 40)
            else:
                print("   Text: (none detected)")
                
        except Exception as e:
            print(f"❌ OCR failed with {config['name']}: {e}")
    
    print(f"\n🎯 iPhone Photo OCR Test Complete")
    print("This establishes baseline OCR performance on clear handwriting")

if __name__ == "__main__":
    test_iphone_photo_ocr()