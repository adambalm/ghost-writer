#!/usr/bin/env python3
"""
Test Supernote extraction and transcription
Verifies:
1. PNG extraction produces legible handwriting
2. Local model (Ollama) transcription works
3. Results can be inspected visually
"""

import sys
from pathlib import Path
import time
import json
import base64
import requests
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def extract_images_from_note(note_path):
    """Extract images from .note file using clean room decoder"""
    from utils.supernote_parser_enhanced import SupernoteParser
    
    print(f"Extracting images from: {note_path}")
    print("-" * 50)
    
    parser = SupernoteParser()
    
    # Parse the note file
    print("Parsing .note file...")
    pages = parser.parse_file(Path(note_path))
    
    if not pages:
        print("No pages found in note file")
        return []
    
    print(f"Found {len(pages)} pages")
    
    results = []
    output_dir = project_root / "extraction_test"
    output_dir.mkdir(exist_ok=True)
    
    for page_num, page in enumerate(pages, 1):
        print(f"\nPage {page_num}:")
        print(f"  Size: {page.width}x{page.height}")
        print(f"  Strokes: {len(page.strokes)}")
        
        # Render the page to an image
        filename = f"page_{page_num}.png"
        output_path = output_dir / filename
        
        # Render page at different scales/backgrounds for better OCR
        for bg_color, suffix in [("white", "white_bg"), ("lightgray", "gray_bg")]:
            img_filename = f"page_{page_num}_{suffix}.png"
            img_path = output_dir / img_filename
            
            # Render the page
            image = parser.render_page_to_image(
                page, 
                output_path=img_path,
                scale=2.0,  # 2x scale for better quality
                background_color=bg_color
            )
            
            # Analyze image content
            import numpy as np
            arr = np.array(image)
            
            # Count non-white pixels (content)
            if bg_color == "white":
                non_white = np.sum(arr < 250)
            else:
                non_white = np.sum(arr < 200)  # Adjust for gray background
            
            mean_brightness = arr.mean()
            
            result = {
                'page': page_num,
                'background': bg_color,
                'path': str(img_path),
                'width': image.width,
                'height': image.height,
                'content_pixels': int(non_white),
                'mean_brightness': float(mean_brightness),
                'has_content': bool(non_white > 1000),
                'stroke_count': len(page.strokes)
            }
            
            print(f"  {bg_color} background: {image.width}x{image.height}, {non_white:,} content pixels")
            results.append(result)
    
    return results

def test_ollama_transcription(image_path):
    """Test transcription with local Ollama model"""
    print(f"\nTesting Ollama transcription for: {Path(image_path).name}")
    print("-" * 40)
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code != 200:
            print("Ollama not running on port 11434")
            print("Start Ollama with: ollama serve")
            return None
    except requests.exceptions.RequestException:
        print("Cannot connect to Ollama on localhost:11434")
        print("Start Ollama with: ollama serve")
        return None
    
    # Encode image
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')
    
    # Try vision models in order of preference
    vision_models = ["qwen2.5vl:7b", "llava", "llava:latest", "bakllava"]
    model = None
    
    # Check which vision model is available
    try:
        models_response = requests.get("http://localhost:11434/api/tags")
        if models_response.status_code == 200:
            available_models = [m['name'] for m in models_response.json().get('models', [])]
            for vm in vision_models:
                if vm in available_models:
                    model = vm
                    break
            
            if not model:
                print(f"No vision model found. Available models: {available_models}")
                print(f"Install a vision model with: ollama pull qwen2.5vl:7b")
                return None
    except:
        pass
    
    print(f"Using model: {model}")
    
    start_time = time.time()
    
    payload = {
        "model": model,
        "prompt": "Transcribe any handwritten text you see in this image. Be precise and complete. If you see no text, say 'NO TEXT DETECTED'.",
        "images": [base64_image],
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result_data = response.json()
            transcription = result_data.get("response", "")
            processing_time = time.time() - start_time
            
            print(f"Time: {processing_time:.2f}s")
            print(f"Transcription: {transcription[:200]}{'...' if len(transcription) > 200 else ''}")
            
            return {
                "transcription": transcription,
                "processing_time": processing_time,
                "model": model,
                "success": "NO TEXT DETECTED" not in transcription.upper()
            }
        else:
            print(f"Ollama API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_html_report(extraction_results, transcription_results):
    """Create HTML report for visual inspection"""
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Extraction and Transcription Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .result { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .image-container { margin: 20px 0; }
        img { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }
        .metadata { background: #f9f9f9; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .transcription { background: #e8f4f8; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .success { color: green; }
        .failure { color: red; }
        h1 { color: #333; }
        h2 { color: #555; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Supernote Extraction and Transcription Test</h1>
        <p>Test Date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p>Note File: joe.note</p>
    </div>
"""
    
    for result in extraction_results:
        if result['has_content']:
            html += f"""
    <div class="result">
        <h2>Page {result['page']} - {result['background']} background</h2>
        
        <div class="metadata">
            <strong>Image Details:</strong><br>
            Size: {result['width']}x{result['height']} pixels<br>
            Content Pixels: {result['content_pixels']:,}<br>
            Mean Brightness: {result['mean_brightness']:.1f}<br>
            Status: <span class="{'success' if result['has_content'] else 'failure'}">
                {'Has Content' if result['has_content'] else 'No Content'}
            </span>
        </div>
        
        <div class="image-container">
            <img src="{Path(result['path']).name}" alt="Page {result['page']} {result['background']}">
        </div>
"""
            
            # Add transcription if available
            trans_key = f"{result['page']}_{result['background']}"
            if trans_key in transcription_results:
                trans = transcription_results[trans_key]
                html += f"""
        <div class="transcription">
            <strong>Transcription (Ollama {trans.get('model', 'unknown')}):</strong><br>
            Processing Time: {trans.get('processing_time', 0):.2f}s<br>
            <p>{trans.get('transcription', 'No transcription available')}</p>
        </div>
"""
            
            html += "</div>"
    
    html += """
</body>
</html>
"""
    
    # Save HTML report
    report_path = project_root / "extraction_test" / "test_report.html"
    with open(report_path, 'w') as f:
        f.write(html)
    
    print(f"\nHTML report saved to: {report_path}")
    print(f"Open in browser: file://{report_path.absolute()}")

def main():
    """Main test function"""
    print("Supernote Extraction and Transcription Test")
    print("=" * 50)
    
    # Test with joe.note
    note_file = project_root / "joe.note"
    
    if not note_file.exists():
        print(f"Error: {note_file} not found")
        return
    
    # Step 1: Extract images
    print("\nStep 1: Extracting Images")
    print("=" * 50)
    extraction_results = extract_images_from_note(note_file)
    
    if not extraction_results:
        print("No images extracted")
        return
    
    # Show extraction summary
    content_pages = [r for r in extraction_results if r['has_content']]
    print(f"\nExtraction Summary:")
    print(f"  Total images: {len(extraction_results)}")
    print(f"  Images with content: {len(content_pages)}")
    
    # Step 2: Test transcription on images with content
    print("\nStep 2: Testing Transcription")
    print("=" * 50)
    
    transcription_results = {}
    
    for result in content_pages[:3]:  # Test first 3 images with content
        trans_result = test_ollama_transcription(result['path'])
        if trans_result:
            key = f"{result['page']}_{result['background']}"
            transcription_results[key] = trans_result
    
    # Step 3: Create inspection report
    print("\nStep 3: Creating Inspection Report")
    print("=" * 50)
    create_html_report(extraction_results, transcription_results)
    
    # Save raw results
    results_file = project_root / "extraction_test" / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'extraction': extraction_results,
            'transcription': transcription_results
        }, f, indent=2)
    
    print(f"Raw results saved to: {results_file}")
    
    print("\nTest Complete!")
    print("Check the extraction_test directory for:")
    print("  - Extracted PNG images")
    print("  - test_report.html (visual inspection)")
    print("  - test_results.json (raw data)")

if __name__ == "__main__":
    main()