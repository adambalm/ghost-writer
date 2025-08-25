#!/usr/bin/env python3
"""
Download joe.note (or any of your notes) from Supernote Cloud and process through the complete pipeline
"""

import sys
import os
from pathlib import Path
from getpass import getpass
import json

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "sn2md"))

from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
from sn2md.importers.note import load_notebook
import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay

def download_your_note():
    """Download joe.note or let you pick from your files"""
    
    print("🌐 Downloading YOUR Note from Supernote Cloud")
    print("=" * 55)
    
    # Get credentials
    print("Enter your Supernote Cloud credentials:")
    username = input("📱 Username (email or phone): ").strip()
    password = getpass("🔐 Password: ")
    
    # Create API client
    credentials = SupernoteCredentials(email=username, password=password)
    api = SupernoteCloudAPI(credentials)
    
    print("\n🔑 Authenticating...")
    if not api.authenticate():
        print("❌ Authentication failed")
        return None
    
    print("✅ Authentication successful!")
    
    # List your note files
    print("\n📁 Fetching your note files...")
    files = api.list_files()
    note_files = [f for f in files if f.name.endswith('.note') and f.size > 1000]  # Filter out tiny/empty files
    
    if not note_files:
        print("❌ No substantial .note files found in your cloud")
        return None
    
    print(f"\n📋 Your .note files:")
    for i, file in enumerate(note_files, 1):
        size_mb = file.size / (1024 * 1024)
        print(f"  {i}. {file.name}: {file.size:,} bytes ({size_mb:.2f} MB)")
    
    # Let user choose or auto-pick joe.note
    joe_file = None
    for file in note_files:
        if 'joe' in file.name.lower():
            joe_file = file
            print(f"\n🎯 Found joe.note: {file.name}")
            break
    
    if not joe_file:
        print(f"\n🤔 No 'joe.note' found. Choose a file to test:")
        while True:
            try:
                choice = input(f"Enter number (1-{len(note_files)}) or filename: ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(note_files):
                        joe_file = note_files[idx]
                        break
                else:
                    # Look for matching filename
                    for file in note_files:
                        if choice.lower() in file.name.lower():
                            joe_file = file
                            break
                    if joe_file:
                        break
                
                print("Invalid choice, try again")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                return None
    
    print(f"\n💾 Downloading {joe_file.name}...")
    download_path = project_root / "joe.note"  # Standard name for web interface
    
    if api.download_file(joe_file, download_path):
        print(f"✅ Downloaded to {download_path} ({download_path.stat().st_size:,} bytes)")
        return download_path
    else:
        print("❌ Download failed")
        return None

def process_with_web_pipeline(note_path):
    """Process the downloaded note using our web pipeline extraction"""
    
    print(f"\n🔧 Processing {note_path.name} with Web Pipeline")
    print("=" * 55)
    
    try:
        # Load with sn2md/supernotelib
        notebook = load_notebook(str(note_path))
        converter = ImageConverter(notebook)
        
        print(f"✅ Loaded notebook: {notebook.get_total_pages()} pages")
        
        # Test all visibility settings like the web interface does
        visibility_options = [
            ("INVISIBLE", VisibilityOverlay.INVISIBLE),
            ("DEFAULT", VisibilityOverlay.DEFAULT), 
            ("VISIBLE", VisibilityOverlay.VISIBLE)
        ]
        
        results = []
        results_dir = project_root / "results"
        results_dir.mkdir(exist_ok=True)
        
        for vis_name, vis_option in visibility_options:
            print(f"\n📄 Testing {vis_name} visibility:")
            
            try:
                vo = sn.converter.build_visibility_overlay(background=vis_option)
                
                for page_idx in range(notebook.get_total_pages()):
                    img = converter.convert(page_idx, vo)
                    
                    # Save image
                    timestamp = "joe_note"
                    image_filename = f"{timestamp}_page_{page_idx + 1}_{vis_name.lower()}.png"
                    image_path = results_dir / image_filename
                    img.save(str(image_path))
                    
                    # Analyze content
                    import numpy as np
                    arr = np.array(img)
                    mean_val = arr.mean()
                    non_white = np.sum(arr < 250)
                    
                    result = {
                        "filename": str(note_path.name),
                        "page": int(page_idx + 1),
                        "visibility": str(vis_name),
                        "image_path": str(image_filename),
                        "mean_brightness": float(round(mean_val, 2)),
                        "content_pixels": int(non_white),
                        "has_content": bool(non_white > 1000),
                        "timestamp": str(timestamp),
                        "transcription": None,
                        "status": "extracted"
                    }
                    
                    status = "✅ CONTENT" if result["has_content"] else "❌ BLANK"
                    print(f"  Page {page_idx + 1}: {non_white:,} pixels - {status}")
                    
                    results.append(result)
                    
            except Exception as e:
                print(f"  ❌ {vis_name} failed: {e}")
        
        # Save results for web interface
        results_file = project_root / "joe_note_results.json"
        with open(results_file, 'w') as f:
            json.dump({"results": results, "source_file": str(note_path)}, f, indent=2)
        
        print(f"\n📊 Processing Summary:")
        content_results = [r for r in results if r["has_content"]]
        print(f"  📄 Total extractions: {len(results)}")
        print(f"  ✅ With content: {len(content_results)}")
        print(f"  ❌ Blank/empty: {len(results) - len(content_results)}")
        
        if content_results:
            print(f"\n🎉 SUCCESS! Found content in {len(content_results)} extractions")
            print("Best extractions:")
            sorted_results = sorted(content_results, key=lambda x: x["content_pixels"], reverse=True)
            for result in sorted_results[:3]:
                print(f"  - Page {result['page']} ({result['visibility']}): {result['content_pixels']:,} pixels")
        else:
            print(f"\n⚠️  No readable content found")
            print("Your note file may be:")
            print("  1. Mostly blank/empty")
            print("  2. Using very light strokes")
            print("  3. Incompatible format version")
        
        return results
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def update_web_interface():
    """Update the web interface to use the downloaded joe.note"""
    
    print(f"\n🌐 Updating Web Interface to Use joe.note")
    print("=" * 45)
    
    web_viewer_path = project_root / "web_viewer.py"
    
    # Read current content
    with open(web_viewer_path) as f:
        content = f.read()
    
    # Update the file path
    old_line = 'note_file = Path("/home/ed/ghost-writer/Visual_Library.note")'
    new_line = 'note_file = Path("/home/ed/ghost-writer/joe.note")'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        with open(web_viewer_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated web_viewer.py to use joe.note")
        return True
    else:
        print("⚠️  Web viewer already configured or needs manual update")
        return False

def main():
    """Download your note and set up complete pipeline"""
    
    print("🚀 YOUR Note Complete Pipeline Test")
    print("=" * 50)
    
    # Step 1: Download your note
    note_path = download_your_note()
    if not note_path:
        print("❌ Failed to download note")
        return
    
    # Step 2: Process with our pipeline
    results = process_with_web_pipeline(note_path)
    if not results:
        print("❌ Failed to process note")
        return
    
    # Step 3: Update web interface
    update_web_interface()
    
    # Step 4: Instructions
    print(f"\n🎉 COMPLETE! Your pipeline is ready:")
    print("=" * 40)
    print(f"✅ Downloaded: {note_path}")
    print(f"✅ Processed: {len(results)} extractions")
    print(f"✅ Updated: Web interface")
    print()
    print("🌐 Next steps:")
    print("1. Restart the web server (it should auto-restart)")
    print("2. Go to http://100.111.114.84:5000")
    print("3. Click 'Process Note File'")
    print("4. You should see YOUR handwriting in the extracted images")
    print("5. Add your OpenAI API key and transcribe!")
    
    content_count = len([r for r in results if r["has_content"]])
    if content_count > 0:
        print(f"\n🎉 Found content in {content_count} extractions - ready for transcription!")
    else:
        print(f"\n⚠️  No content detected - your note may be blank or need different settings")

if __name__ == "__main__":
    main()