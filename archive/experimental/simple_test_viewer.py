#!/usr/bin/env python3
"""
Simple test viewer for enhanced clean room decoder
No assumptions, no exaggerations - just test the decoder and show results
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

app = Flask(__name__)

# Configuration
RESULTS_FOLDER = project_root / "results"
RESULTS_FOLDER.mkdir(exist_ok=True)

class SimpleProcessor:
    def __init__(self):
        self.enhanced_parser = None
        
    def initialize_parser(self):
        """Initialize the enhanced parser"""
        try:
            from utils.supernote_parser_enhanced import SupernoteParser
            self.enhanced_parser = SupernoteParser()
            return True
        except Exception as e:
            print(f"Failed to initialize parser: {e}")
            return False
    
    def process_file(self, note_file_path):
        """Process note file and return basic results"""
        if not self.enhanced_parser:
            return {"error": "Parser not initialized"}
            
        try:
            print(f"Processing: {note_file_path}")
            
            # Parse with enhanced decoder
            pages = self.enhanced_parser.parse_file(note_file_path)
            
            if not pages:
                return {"error": "No pages extracted"}
            
            results = []
            
            for page_idx, page in enumerate(pages, 1):
                try:
                    # Generate image filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"{timestamp}_page_{page_idx}.png"
                    image_path = RESULTS_FOLDER / image_filename
                    
                    # Render page to image
                    self.enhanced_parser.render_page_to_image(page, image_path, scale=2.0)
                    
                    # Get pixel statistics
                    content_pixels = 0
                    total_pixels = page.width * page.height
                    
                    if 'decoded_bitmap' in page.metadata:
                        bitmap = page.metadata['decoded_bitmap']
                        if hasattr(bitmap, 'sum'):
                            content_pixels = int((bitmap < 255).sum())
                        if hasattr(bitmap, 'size'):
                            total_pixels = int(bitmap.size)
                    
                    result = {
                        "page": page_idx,
                        "image_path": image_filename,
                        "width": page.width,
                        "height": page.height,
                        "content_pixels": content_pixels,
                        "total_pixels": total_pixels,
                        "parser": page.metadata.get('parser', 'unknown'),
                        "layer_name": page.metadata.get('layer_name', 'unknown'),
                        "bitmap_size": page.metadata.get('bitmap_size', 0)
                    }
                    
                    results.append(result)
                    print(f"Page {page_idx}: {content_pixels} content pixels")
                    
                except Exception as e:
                    print(f"Failed to process page {page_idx}: {e}")
                    results.append({"page": page_idx, "error": str(e)})
            
            total_content = sum(r.get('content_pixels', 0) for r in results)
            print(f"Total content pixels: {total_content}")
            
            return {"success": True, "results": results, "total_pixels": total_content}
            
        except Exception as e:
            print(f"Processing failed: {e}")
            return {"error": str(e)}

processor = SimpleProcessor()

@app.route('/')
def index():
    """Simple test interface"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Simple Test Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .result { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 4px; }
        .image-container { text-align: center; margin: 15px 0; }
        .image-container img { max-width: 100%; border: 1px solid #ccc; }
        .stats { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .error { background: #ffebee; color: #c62828; padding: 15px; border-radius: 4px; }
        .success { background: #e8f5e9; color: #2e7d32; padding: 15px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Simple Test Viewer</h1>
        <p>Test the enhanced clean room decoder with available note files.</p>
        
        <button class="button" onclick="testDecoder()">Test Enhanced Decoder</button>
        <button class="button" onclick="testWithJoeNote()">Test with joe.note</button>
        
        <div id="status"></div>
        <div id="results"></div>
    </div>

    <script>
        function showStatus(message, isError = false) {
            const status = document.getElementById('status');
            const className = isError ? 'error' : 'success';
            status.innerHTML = `<div class="${className}">${message}</div>`;
        }
        
        async function testDecoder() {
            showStatus('Testing enhanced decoder...');
            
            try {
                const response = await fetch('/test');
                const data = await response.json();
                
                if (data.error) {
                    showStatus('Error: ' + data.error, true);
                } else {
                    showStatus(`Processed ${data.results.length} pages, ${data.total_pixels} total pixels`);
                    displayResults(data.results);
                }
            } catch (error) {
                showStatus('Request failed: ' + error.message, true);
            }
        }
        
        async function testWithJoeNote() {
            showStatus('Testing with joe.note...');
            
            try {
                const response = await fetch('/test_joe');
                const data = await response.json();
                
                if (data.error) {
                    showStatus('Error: ' + data.error, true);
                } else {
                    showStatus(`Processed joe.note: ${data.results.length} pages, ${data.total_pixels} total pixels`);
                    displayResults(data.results);
                }
            } catch (error) {
                showStatus('Request failed: ' + error.message, true);
            }
        }
        
        function displayResults(results) {
            const container = document.getElementById('results');
            
            container.innerHTML = results.map(result => {
                if (result.error) {
                    return `<div class="result"><strong>Page ${result.page}</strong><div class="error">Error: ${result.error}</div></div>`;
                }
                
                return `
                    <div class="result">
                        <h3>Page ${result.page}</h3>
                        <div class="stats">
                            <strong>Dimensions:</strong> ${result.width} x ${result.height}<br>
                            <strong>Content Pixels:</strong> ${result.content_pixels.toLocaleString()}<br>
                            <strong>Total Pixels:</strong> ${result.total_pixels.toLocaleString()}<br>
                            <strong>Parser:</strong> ${result.parser}<br>
                            <strong>Layer:</strong> ${result.layer_name}<br>
                            <strong>Bitmap Size:</strong> ${result.bitmap_size} bytes
                        </div>
                        <div class="image-container">
                            <img src="/images/${result.image_path}" alt="Page ${result.page}" />
                        </div>
                    </div>
                `;
            }).join('');
        }
    </script>
</body>
</html>'''

@app.route('/test')
def test_decoder():
    """Test with any available note file"""
    try:
        if not processor.initialize_parser():
            return jsonify({"error": "Failed to initialize parser"})
        
        # Look for any .note file
        test_files = [
            project_root / "joe.note",
            project_root / "Visual_Library.note",
            project_root / "temp_20250807_035920.note"
        ]
        
        for test_file in test_files:
            if test_file.exists():
                result = processor.process_file(test_file)
                return jsonify(result)
        
        return jsonify({"error": "No test .note files found"})
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/test_joe')
def test_joe_note():
    """Test specifically with joe.note"""
    try:
        if not processor.initialize_parser():
            return jsonify({"error": "Failed to initialize parser"})
        
        joe_file = project_root / "joe.note"
        if not joe_file.exists():
            return jsonify({"error": "joe.note not found"})
        
        result = processor.process_file(joe_file)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve extracted images"""
    return send_from_directory(RESULTS_FOLDER, filename)

if __name__ == '__main__':
    print("Simple Test Viewer")
    print("==================")
    print("Access at: http://localhost:5002")
    print("Tests the enhanced clean room decoder")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5003)