#!/usr/bin/env python3
"""
Simplified script to download your note and process it
"""

import sys
from pathlib import Path
import json
from getpass import getpass

# Add paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

def download_note():
    """Download joe.note from Supernote Cloud"""
    
    print("🌐 Downloading YOUR Note from Supernote Cloud")
    print("=" * 55)
    
    try:
        from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
        
        # Get credentials
        print("Enter your Supernote Cloud credentials:")
        username = input("📱 Username: ").strip()
        password = getpass("🔐 Password: ")
        
        # Create API and authenticate
        credentials = SupernoteCredentials(email=username, password=password)
        api = SupernoteCloudAPI(credentials)
        
        print("\n🔑 Authenticating...")
        if not api.authenticate():
            print("❌ Authentication failed")
            return None
        
        print("✅ Authentication successful!")
        
        # Get files
        files = api.list_files()
        note_files = [f for f in files if f.name.endswith('.note') and f.size > 1000]
        
        if not note_files:
            print("❌ No substantial .note files found")
            return None
        
        print(f"\n📋 Your files:")
        for i, file in enumerate(note_files, 1):
            size_mb = file.size / (1024 * 1024)
            print(f"  {i}. {file.name}: {size_mb:.2f} MB")
        
        # Find joe.note or let user choose
        target_file = None
        for file in note_files:
            if 'joe' in file.name.lower():
                target_file = file
                print(f"\n🎯 Found {file.name}")
                break
        
        if not target_file:
            choice = input(f"Choose file (1-{len(note_files)}): ").strip()
            try:
                target_file = note_files[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                return None
        
        # Download
        download_path = project_root / "joe.note"
        print(f"\n💾 Downloading {target_file.name}...")
        
        if api.download_file(target_file, download_path):
            print(f"✅ Downloaded: {download_path}")
            return download_path
        else:
            print("❌ Download failed")
            return None
            
    except ImportError:
        print("❌ Supernote API not available")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def process_note(note_path):
    """Process the note with our pipeline"""
    
    print(f"\n🔧 Processing {note_path.name}")
    print("=" * 40)
    
    try:
        # Import here to avoid path issues
        sys.path.insert(0, str(project_root / "sn2md"))
        from sn2md.importers.note import load_notebook
        import supernotelib as sn
        from supernotelib.converter import ImageConverter, VisibilityOverlay
        
        # Load notebook
        notebook = load_notebook(str(note_path))
        converter = ImageConverter(notebook)
        print(f"✅ Loaded: {notebook.get_total_pages()} pages")
        
        # Test extractions
        results_dir = project_root / "results"
        results_dir.mkdir(exist_ok=True)
        
        visibility_options = [
            ("INVISIBLE", VisibilityOverlay.INVISIBLE),
            ("DEFAULT", VisibilityOverlay.DEFAULT),
            ("VISIBLE", VisibilityOverlay.VISIBLE)
        ]
        
        content_found = []
        
        for vis_name, vis_option in visibility_options:
            print(f"\n📄 Testing {vis_name}:")
            
            try:
                vo = sn.converter.build_visibility_overlay(background=vis_option)
                
                for page_idx in range(notebook.get_total_pages()):
                    img = converter.convert(page_idx, vo)
                    
                    # Save
                    filename = f"joe_note_page_{page_idx + 1}_{vis_name.lower()}.png"
                    img.save(results_dir / filename)
                    
                    # Analyze
                    import numpy as np
                    arr = np.array(img)
                    non_white = np.sum(arr < 250)
                    
                    if non_white > 1000:
                        content_found.append(f"Page {page_idx + 1} ({vis_name}): {non_white:,} pixels")
                        print(f"  ✅ Page {page_idx + 1}: {non_white:,} pixels")
                    else:
                        print(f"  ❌ Page {page_idx + 1}: {non_white:,} pixels (blank)")
                        
            except Exception as e:
                print(f"  ❌ {vis_name} failed: {e}")
        
        # Summary
        if content_found:
            print(f"\n🎉 Found content in {len(content_found)} extractions:")
            for item in content_found:
                print(f"  - {item}")
        else:
            print(f"\n⚠️  No readable content found")
        
        return len(content_found) > 0
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False

def update_web_viewer():
    """Update web viewer to use joe.note"""
    
    print(f"\n🌐 Updating Web Interface")
    print("=" * 30)
    
    web_file = project_root / "web_viewer.py"
    
    # Read and update
    with open(web_file) as f:
        content = f.read()
    
    # Replace the note file path
    old_path = 'Path("/home/ed/ghost-writer/Visual_Library.note")'
    new_path = 'Path("/home/ed/ghost-writer/joe.note")'
    
    if old_path in content:
        content = content.replace(old_path, new_path)
        with open(web_file, 'w') as f:
            f.write(content)
        print("✅ Updated web viewer")
    else:
        print("⚠️  Web viewer already updated")

def main():
    print("🚀 Get My Note - Complete Pipeline")
    print("=" * 45)
    
    # Download
    note_path = download_note()
    if not note_path:
        return
    
    # Process
    has_content = process_note(note_path)
    
    # Update web interface
    update_web_viewer()
    
    # Final instructions
    print(f"\n🎉 DONE!")
    print("=" * 20)
    print("1. Web server should auto-restart")
    print("2. Go to: http://100.111.114.84:5000")
    print("3. Click 'Process Note File'")
    
    if has_content:
        print("4. ✅ You should see YOUR handwriting!")
        print("5. Add OpenAI key and transcribe")
    else:
        print("4. ⚠️  Images may appear blank")
        print("   Your note might be empty or need different settings")

if __name__ == "__main__":
    main()