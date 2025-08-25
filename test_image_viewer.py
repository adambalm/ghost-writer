#!/usr/bin/env python3
"""
Simple web viewer to verify extracted images are actually readable
"""

from flask import Flask, render_template_string, send_file
from pathlib import Path
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Image Extraction Verification</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .image-container { margin: 20px 0; border: 1px solid #ccc; padding: 20px; }
        .image-container img { max-width: 100%; border: 1px solid #ddd; }
        .image-info { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        h1 { color: #333; }
        h2 { color: #666; }
    </style>
</head>
<body>
    <h1>🔍 Supernote Extraction Verification</h1>
    <p>Verifying that extracted images actually contain readable handwritten text</p>
    
    <div class="image-container">
        <h2>Forensic Method (Known Working)</h2>
        <div class="image-info">
            <strong>Page 1 MAINLAYER:</strong> 74,137 content pixels
        </div>
        <img src="/image/forensic_test_Page1_MAINLAYER.png" alt="Forensic Page 1">
        
        <div class="image-info">
            <strong>Page 2 MAINLAYER:</strong> 20,894 content pixels
        </div>
        <img src="/image/forensic_test_Page2_MAINLAYER.png" alt="Forensic Page 2">
    </div>
    
    <div class="image-container">
        <h2>Clean Room Method (Testing)</h2>
        <div class="image-info">
            <strong>Status:</strong> {% if clean_room_exists %}Images found{% else %}No images generated{% endif %}
        </div>
        {% if clean_room_exists %}
        <img src="/image/clean_room_page_1.png" alt="Clean Room Page 1">
        <img src="/image/clean_room_page_2.png" alt="Clean Room Page 2">
        {% else %}
        <p>Clean room parser did not generate visible images</p>
        {% endif %}
    </div>
    
    <div class="image-container">
        <h2>Demo Method (sn2md - Working)</h2>
        <div class="image-info">
            <strong>Page 1:</strong> 346,713 content pixels (from web demo)
        </div>
        <p>Check results folder for demo-generated images</p>
    </div>
    
    <h2>Conclusion</h2>
    <p><strong>Question:</strong> Can you see readable handwritten text in the images above?</p>
    <p><strong>Forensic Method:</strong> ✅ Known to produce readable images</p>
    <p><strong>Clean Room Method:</strong> {% if clean_room_exists %}🔍 Verify manually{% else %}❌ Not producing images{% endif %}</p>
</body>
</html>
"""

@app.route('/')
def index():
    clean_room_exists = (Path('clean_room_page_1.png').exists() and 
                        Path('clean_room_page_2.png').exists())
    return render_template_string(HTML_TEMPLATE, clean_room_exists=clean_room_exists)

@app.route('/image/<filename>')
def serve_image(filename):
    if os.path.exists(filename):
        return send_file(filename)
    return "Image not found", 404

if __name__ == '__main__':
    print("🔍 Starting Image Verification Viewer")
    print("📱 Access at: http://localhost:5002")
    print("🎯 Purpose: Verify extracted images are actually readable")
    app.run(host='0.0.0.0', port=5002, debug=True)