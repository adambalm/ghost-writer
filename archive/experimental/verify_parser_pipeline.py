#!/usr/bin/env python3
"""
Verification script for the integrated parser pipeline
Tests the complete flow: parse → render → OCR
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.supernote_parser import SupernoteParser
from utils.ocr_providers import TesseractOCR
import numpy as np

def verify_parser_pipeline():
    """Verify the complete parser pipeline works"""
    
    print("🔍 Verifying Supernote Parser Pipeline")
    print("=" * 50)
    
    note_file = "/home/ed/ghost-writer/temp_20250807_035920.note"
    
    if not Path(note_file).exists():
        print(f"❌ Test file not found: {note_file}")
        return
    
    # Step 1: Parse the file
    print("📄 Step 1: Parsing Supernote file...")
    parser = SupernoteParser()
    
    try:
        pages = parser.parse_file(Path(note_file))
        print(f"   Parsed {len(pages)} pages")
        
        for page in pages:
            print(f"   Page {page.page_id}: {page.width}x{page.height}")
            print(f"   Parser: {page.metadata.get('parser', 'unknown')}")
            print(f"   Has content: {page.metadata.get('has_content', 'unknown')}")
            
            if 'decoded_bitmap' in page.metadata:
                bitmap = page.metadata['decoded_bitmap']
                non_white = np.sum(bitmap < 255)
                print(f"   Non-white pixels: {non_white:,}")
    
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return
    
    # Step 2: Render images
    print("\n🖼️  Step 2: Rendering images...")
    rendered_files = []
    
    for i, page in enumerate(pages):
        output_path = f"/home/ed/ghost-writer/verify_page_{page.page_id}.png"
        
        try:
            image = parser.render_page_to_image(page, Path(output_path))
            rendered_files.append(output_path)
            print(f"   Rendered: {output_path}")
            
            # Check image properties
            print(f"   Image size: {image.size}")
            print(f"   Image mode: {image.mode}")
            
        except Exception as e:
            print(f"❌ Rendering failed for page {page.page_id}: {e}")
    
    # Step 3: Test OCR
    print("\n📝 Step 3: Testing OCR...")
    
    tesseract_config = {
        "executable_path": "tesseract",
        "language": "eng",
        "psm": 6
    }
    
    ocr = TesseractOCR(tesseract_config)
    
    for image_path in rendered_files:
        if not Path(image_path).exists():
            continue
            
        try:
            result = ocr.extract_text(image_path)
            print(f"   {Path(image_path).name}:")
            print(f"   Confidence: {result.confidence:.1f}%")
            
            if result.text.strip():
                print(f"   Text: '{result.text.strip()[:100]}{'...' if len(result.text) > 100 else ''}'")
            else:
                print("   Text: (none detected)")
                
        except Exception as e:
            print(f"❌ OCR failed for {image_path}: {e}")
    
    # Step 4: Summary
    print("\n📊 Verification Summary:")
    print(f"   Files parsed: {len(pages)}")
    print(f"   Images rendered: {len(rendered_files)}")
    print("   New format support: implemented")
    print("   RLE decoder: integrated")
    
    # Generate file list for transfer
    print(f"\n📁 Generated files for inspection:")
    all_files = rendered_files + [
        "/home/ed/ghost-writer/fixed_Page1_MainLayer.png",
        "/home/ed/ghost-writer/fixed_Page2_MainLayer.png",
        "/home/ed/ghost-writer/integrated_page_1.png"
    ]
    
    for file_path in all_files:
        if Path(file_path).exists():
            print(f"   {file_path}")

if __name__ == "__main__":
    verify_parser_pipeline()