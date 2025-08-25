#!/usr/bin/env python3
"""
Test script to download and process joe.note through the full pipeline
"""

import sys
from pathlib import Path
from getpass import getpass

# Add the src directory to Python path using absolute path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
from utils.supernote_parser import SupernoteParser
from utils.ocr_providers import TesseractOCR

def test_joe_note_processing():
    """Download joe.note and process it through OCR"""
    
    print("🎯 Joe.note Processing Test")
    print("=" * 40)
    
    # Get credentials from user
    print("Enter your Supernote Cloud credentials:")
    username = input("📱 Username (email or phone): ").strip()
    password = getpass("🔐 Password: ")
    
    # Create API client
    credentials = SupernoteCredentials(email=username, password=password)
    api = SupernoteCloudAPI(credentials)
    
    print("\n🔑 Authenticating...")
    if not api.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful!")
    
    # List files and show sizes
    print("\n📁 Fetching file list with sizes...")
    files = api.list_files()
    
    print("\n📊 File sizes:")
    note_files = [f for f in files if f.name.endswith('.note')]
    non_zero_files = []
    
    for file in note_files:
        size_mb = file.size / (1024 * 1024) if file.size > 0 else 0
        if file.size > 0:
            non_zero_files.append(file)
            print(f"  ✅ {file.name}: {file.size:,} bytes ({size_mb:.2f} MB)")
        else:
            print(f"  ⚠️  {file.name}: {file.size} bytes (empty/zero)")
    
    print(f"\n📈 Summary: {len(non_zero_files)} non-empty files out of {len(note_files)} total .note files")
    
    if not non_zero_files:
        print("❌ No non-empty .note files found")
        return
    
    # Pick the first non-empty file, or let user choose
    if len(non_zero_files) == 1:
        test_file = non_zero_files[0]
        print(f"\n🎯 Testing with only non-empty file: {test_file.name}")
    else:
        print(f"\n🎯 Multiple non-empty files found. Testing with: {non_zero_files[0].name}")
        test_file = non_zero_files[0]
        print("   (You can modify the script to test a different file)")
    
    # Debug: Show file details
    print(f"📋 File details: ID={test_file.file_id}, Name={test_file.name}, Path={test_file.path}, Size={test_file.size}")
    
    # Download the file
    print(f"\n💾 Downloading {test_file.name}...")
    download_path = project_root / f"temp_{test_file.name}"
    
    if api.download_file(test_file, download_path):
        print(f"✅ Downloaded to {download_path} ({download_path.stat().st_size} bytes)")
    else:
        print("❌ Download failed")
        return
    
    # Parse the .note file
    print("\n🔧 Parsing .note file...")
    parser = SupernoteParser()
    
    try:
        pages = parser.parse_file(download_path)
        print(f"✅ Parsed {len(pages)} pages")
        
        if pages:
            page = pages[0]
            print(f"📋 Page metadata: {page.metadata}")
            
            # Check if this is a format we can actually render
            if page.metadata.get("status") == "unsupported":
                print(f"❌ {page.metadata.get('message')}")
                print(f"\n💡 This file uses format: {page.metadata.get('format')}")
                print("   Our parser only supports older formats (NOTE magic signature)")
                print("   The file downloaded correctly, but we need a specialized parser")
                print("   for this newer format to extract the actual drawing data.")
                return
            
            # Render first page to image for OCR
            print("\n🖼️  Rendering page 1 to image...")
            image = parser.render_page_to_image(pages[0])
            
            # Save image for debugging
            image_path = project_root / f"temp_{test_file.name}_page1.png"
            image.save(image_path)
            print(f"✅ Saved page image: {image_path}")
            
            # Run OCR on the image
            print("\n👁️  Running OCR on page 1...")
            tesseract_config = {
                "executable_path": "tesseract",  # Default system tesseract
                "language": "eng",
                "psm": 6  # Page segmentation mode
            }
            ocr = TesseractOCR(tesseract_config)
            ocr_result = ocr.extract_text(image_path)
            
            print(f"✅ OCR completed with {ocr_result.confidence:.1f}% confidence")
            print("\n📝 Extracted Text:")
            print("-" * 40)
            print(ocr_result.text)
            print("-" * 40)
            
            # Keep files for debugging
            print(f"\n🔍 Files saved for inspection:")
            print(f"  📄 Note file: {download_path}")
            print(f"  🖼️  Image file: {image_path}")
            print("  (Not cleaning up so you can examine the files)")
            
        else:
            print("❌ No pages found in the note file")
            
    except Exception as e:
        print(f"❌ Error processing note: {e}")
        # Clean up on error
        if download_path.exists():
            download_path.unlink()

if __name__ == "__main__":
    test_joe_note_processing()