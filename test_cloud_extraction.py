#!/usr/bin/env python3
"""
Test Supernote Cloud extraction with provided credentials
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.supernote_api import create_supernote_client
from utils.supernote_parser_enhanced import SupernoteParser

def test_cloud_extraction(phone, password):
    """Test extraction from Supernote Cloud"""
    
    print("Testing Supernote Cloud Extraction")
    print("=" * 50)
    
    # Create client
    config = {}
    client = create_supernote_client(config, email=phone, password=password)
    
    if not client:
        print("Failed to authenticate")
        return
    
    print("Authentication successful")
    
    # List files
    print("\nFetching available notes...")
    files = client.list_files()
    
    print(f"Found {len(files)} files")
    
    # Look for test notes
    note_files = [f for f in files if f.file_type == 'note']
    print(f"Found {len(note_files)} .note files")
    
    if note_files:
        print("\nAvailable notes:")
        for i, note in enumerate(note_files[:10], 1):
            print(f"  {i}. {note.name} ({note.size / 1024:.1f} KB)")
        
        # Download a note with more content (acast.note looks promising at 728KB)
        test_note = None
        for note in note_files:
            if 'acast' in note.name.lower() or note.size > 500000:  # Look for larger notes
                test_note = note
                break
        
        if not test_note:
            test_note = note_files[0]  # Fallback to first note
        print(f"\nDownloading: {test_note.name}")
        
        output_path = Path("test_note.note")
        if client.download_file(test_note, output_path):
            print(f"Downloaded to: {output_path}")
            
            # Extract images
            print("\nExtracting images...")
            parser = SupernoteParser()
            pages = parser.parse_file(output_path)
            
            if pages:
                print(f"Found {len(pages)} pages")
                
                # Render first page
                if pages:
                    page = pages[0]
                    print(f"Page 1: {page.width}x{page.height}, {len(page.strokes)} strokes")
                    
                    # Render to image
                    img_path = Path("test_page_1.png")
                    image = parser.render_page_to_image(
                        page,
                        output_path=img_path,
                        scale=2.0
                    )
                    print(f"Rendered to: {img_path}")
                    
                    # Check content
                    import numpy as np
                    arr = np.array(image)
                    non_white = np.sum(arr < 250)
                    print(f"Content pixels: {non_white:,}")
                    
                    if non_white > 1000:
                        print("Image has content - ready for OCR")
                    else:
                        print("Image appears blank")
            else:
                print("No pages extracted")
        else:
            print("Download failed")
    else:
        print("No .note files found in your account")

if __name__ == "__main__":
    # Use provided credentials
    phone = "4139491742"
    password = "cesterCAT50$"
    
    test_cloud_extraction(phone, password)