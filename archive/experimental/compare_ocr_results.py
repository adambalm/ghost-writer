#!/usr/bin/env python3
"""
Compare OCR results between iPhone photo and our RLE decoded images
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.ocr_providers import TesseractOCR

def test_image_ocr(image_path: str, description: str):
    """Test OCR on a single image"""
    
    print(f"\n🔍 Testing {description}")
    print(f"   Image: {image_path}")
    
    if not Path(image_path).exists():
        print("   ❌ Image not found")
        return None
    
    try:
        tesseract_config = {
            "executable_path": "tesseract",
            "language": "eng",
            "psm": 6,
            "oem": 3
        }
        
        ocr = TesseractOCR(tesseract_config)
        result = ocr.extract_text(image_path)
        
        print(f"   Confidence: {result.confidence:.1f}%")
        print(f"   Text length: {len(result.text)} characters")
        
        if result.text.strip():
            # Show recognizable words
            words = result.text.split()
            recognizable = [w for w in words if len(w) > 2 and w.isalpha()]
            print(f"   Recognizable words: {recognizable[:10]}")
            print(f"   Sample text: '{result.text.strip()[:100]}{'...' if len(result.text) > 100 else ''}'")
        else:
            print("   Text: (none detected)")
            
        return result
        
    except Exception as e:
        print(f"   ❌ OCR failed: {e}")
        return None

def compare_all_ocr_results():
    """Compare OCR results across all our test images"""
    
    print("📊 OCR Comparison: iPhone Photo vs RLE Decoded Images")
    print("=" * 60)
    
    test_images = [
        ("/home/ed/ghost-writer/iphone_photo.png", "iPhone Photo (Ground Truth)"),
        ("/home/ed/ghost-writer/verify_page_1.png", "Integrated Parser Output"),
        ("/home/ed/ghost-writer/fixed_Page1_MainLayer.png", "Direct RLE Decode - Page 1"),
        ("/home/ed/ghost-writer/fixed_Page2_MainLayer.png", "Direct RLE Decode - Page 2"),
        ("/home/ed/ghost-writer/verification_images/current_parser_output.png", "Current Parser (Verification)"),
    ]
    
    results = []
    
    for image_path, description in test_images:
        result = test_image_ocr(image_path, description)
        results.append((description, result))
    
    # Summary comparison
    print(f"\n📈 Summary Comparison:")
    print("-" * 50)
    
    for description, result in results:
        if result:
            conf = result.confidence
            text_len = len(result.text.strip())
            words = len(result.text.split()) if result.text.strip() else 0
            
            status = "🟢" if conf > 50 else "🟡" if conf > 10 else "🔴"
            print(f"{status} {description:35} | Conf: {conf:5.1f}% | Chars: {text_len:3d} | Words: {words:2d}")
        else:
            print(f"🔴 {description:35} | FAILED")
    
    print(f"\n💡 Analysis:")
    print("- iPhone photo provides baseline for OCR performance on this handwriting")
    print("- RLE decoded images can be compared against this baseline")
    print("- Low confidence across all images suggests handwriting OCR is challenging")
    print("- Text length and word count indicate if content is being extracted")

if __name__ == "__main__":
    compare_all_ocr_results()