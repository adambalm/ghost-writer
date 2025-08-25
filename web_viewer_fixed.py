#!/usr/bin/env python3
"""
Web interface to view extracted Supernote images and transcriptions
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import base64

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "sn2md"))

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = project_root / "uploads"
RESULTS_FOLDER = project_root / "results"
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)

class SupernoteProcessor:
    def __init__(self):
        self.results = []
        
    def process_file(self, note_file_path):
        """Process a Supernote file and return results"""
        try:
            from sn2md.importers.note import load_notebook
            import supernotelib as sn
            from supernotelib.converter import ImageConverter, VisibilityOverlay
            
            print(f"Processing: {note_file_path}")
            
            # Load notebook
            notebook = load_notebook(note_file_path)
            converter = ImageConverter(notebook)
            
            # Try both visibility settings to see which works
            visibility_options = [
                ("INVISIBLE", VisibilityOverlay.INVISIBLE),
                ("DEFAULT", VisibilityOverlay.DEFAULT),
                ("VISIBLE", VisibilityOverlay.VISIBLE)
            ]
            
            results = []
            
            for vis_name, vis_option in visibility_options:
                try:
                    vo = sn.converter.build_visibility_overlay(background=vis_option)
                    
                    for page_idx in range(notebook.get_total_pages()):
                        img = converter.convert(page_idx, vo)
                        
                        # Save image
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_filename = f"{timestamp}_page_{page_idx + 1}_{vis_name.lower()}.png"
                        image_path = RESULTS_FOLDER / image_filename
                        img.save(str(image_path))
                        
                        # Analyze content
                        import numpy as np
                        arr = np.array(img)
                        mean_val = arr.mean()
                        non_white = np.sum(arr < 250)
                        
                        result = {
                            "filename": str(note_file_path.name),
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
                        
                        results.append(result)
                        print(f"  {vis_name} Page {page_idx + 1}: {non_white:,} pixels")
                        
                except Exception as e:
                    print(f"  Failed {vis_name}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Processing failed: {e}")
            return [{"error": str(e), "filename": note_file_path.name}]
    
    def transcribe_image(self, image_path, api_key):
        """Transcribe an image using GPT-4 Vision"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=api_key)
            
            with open(RESULTS_FOLDER / image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please transcribe any handwritten text you see in this image. If you can read text clearly, transcribe it exactly. If you see drawings or diagrams, describe them. If the image appears blank or you cannot read anything, say 'NO CONTENT DETECTED'."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }}
                    ]
                }],
                max_tokens=500,
                temperature=0
            )
            
            result = response.choices[0].message.content
            cost = (response.usage.prompt_tokens * 0.01 / 1000) + (response.usage.completion_tokens * 0.03 / 1000)
            
            return {
                "transcription": result,
                "cost": round(cost, 4),
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens
                },
                "model": "gpt-4o",
                "provider": "openai"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def transcribe_image_local(self, image_path, model_name="qwen2.5vl:7b"):
        """Transcribe an image using local Ollama model"""
        try:
            import subprocess
            import time
            
            start_time = time.time()
            
            # Build the improved contextual prompt
            prompt = "Transcribe this handwritten text carefully. Use context clues to correct obvious OCR errors and ensure the text makes semantic sense. If you see unclear words, choose the most contextually appropriate word that fits the meaning of the sentence."
            
            # Full path to image
            full_image_path = RESULTS_FOLDER / image_path
            
            # Call Ollama directly
            cmd = [
                "ollama", "run", model_name,
                prompt,
                str(full_image_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                transcription = result.stdout.strip()
                
                # Clean up any control characters from terminal output
                lines = transcription.split('\n')
                # Skip lines that might be loading indicators or control sequences
                clean_lines = []
                for line in lines:
                    # Skip empty lines and lines with control characters
                    if line.strip() and not line.startswith('Added image') and not '[?' in line:
                        clean_lines.append(line.strip())
                
                final_transcription = '\n'.join(clean_lines) if clean_lines else transcription
                
                return {
                    "transcription": final_transcription,
                    "cost": 0.0,  # Local model is free
                    "processing_time": round(processing_time, 2),
                    "model": model_name,
                    "provider": "ollama"
                }
            else:
                return {
                    "error": f"Ollama error: {result.stderr}",
                    "provider": "ollama"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "error": "Local model timed out (>2 minutes)",
                "provider": "ollama"
            }
        except Exception as e:
            return {
                "error": str(e),
                "provider": "ollama"
            }

processor = SupernoteProcessor()

@app.route('/')
def index():
    """Main interface"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_note():
    """Process uploaded note file"""
    try:
        # Use the Visual Library file that has rich handwriting content
        note_file = Path("/home/ed/ghost-writer/joe.note")
        
        print(f"Looking for note file: {note_file}")
        print(f"File exists: {note_file.exists()}")
        
        if not note_file.exists():
            return jsonify({"error": f"Test note file not found at {note_file}"})
        
        print("Starting file processing...")
        results = processor.process_file(note_file)
        print(f"Processing complete. Got {len(results)} results")
        
        # Debug: print first result
        if results:
            print(f"First result: {results[0]}")
        
        return jsonify({
            "success": True,
            "results": results,
            "message": f"Processed {len(results)} extractions"
        })
        
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_msg)
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe a specific image using OpenAI"""
    try:
        data = request.json
        image_path = data.get('image_path')
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({"error": "API key required"})
        
        if not image_path:
            return jsonify({"error": "Image path required"})
        
        result = processor.transcribe_image(image_path, api_key)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/transcribe_local', methods=['POST'])
def transcribe_local():
    """Transcribe a specific image using local Ollama model"""
    try:
        data = request.json
        image_path = data.get('image_path')
        model_name = data.get('model_name', 'qwen2.5vl:7b')
        
        if not image_path:
            return jsonify({"error": "Image path required"})
        
        result = processor.transcribe_image_local(image_path, model_name)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve extracted images"""
    return send_from_directory(RESULTS_FOLDER, filename)

@app.route('/results')
def get_results():
    """Get all processing results"""
    try:
        # Load results from files
        results_files = list(RESULTS_FOLDER.glob("*.json"))
        all_results = []
        
        for results_file in results_files:
            with open(results_file) as f:
                data = json.load(f)
                all_results.extend(data.get('results', []))
        
        return jsonify({"results": all_results})
        
    except Exception as e:
        return jsonify({"error": str(e)})

# Create templates directory and HTML template
templates_dir = project_root / "templates"
templates_dir.mkdir(exist_ok=True)

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Supernote Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .results { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .result-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .image-container { text-align: center; margin-bottom: 15px; }
        .image-container img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
        .meta-info { background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; }
        .transcription { background: #e3f2fd; padding: 15px; border-radius: 4px; border-left: 4px solid #2196F3; }
        .button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .button:hover { background: #45a049; }
        .button.secondary { background: #2196F3; }
        .button.secondary:hover { background: #0b7dda; }
        .api-key-input { width: 300px; padding: 8px; margin: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Supernote Viewer & Transcriber</h1>
            <p>Extract images from Supernote files and transcribe with AI</p>
            
            <div style="margin: 20px 0;">
                <button class="button" onclick="processNote()">📄 Process Note File</button>
                <br>
                <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9;">
                    <h3>Transcription Options:</h3>
                    <div style="margin: 10px 0;">
                        <strong>🖥️ Local Model (Free):</strong>
                        <button class="button secondary" onclick="transcribeAllLocal()">🚀 Transcribe All (Local)</button>
                        <span style="margin-left: 10px; font-size: 12px; color: #666;">Uses Qwen2.5-VL 7B</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <strong>☁️ OpenAI (Paid):</strong>
                        <input type="password" class="api-key-input" id="apiKey" placeholder="OpenAI API Key" style="width: 250px;" />
                        <button class="button secondary" onclick="transcribeAll()">🤖 Transcribe All (OpenAI)</button>
                    </div>
                </div>
            </div>
            
            <div id="status"></div>
        </div>
        
        <div id="results" class="results"></div>
    </div>

    <script>
        let currentResults = [];
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.innerHTML = `<div class="status ${type}">${message}</div>`;
            if (type !== 'error') {
                setTimeout(() => status.innerHTML = '', 5000);
            }
        }
        
        async function processNote() {
            showStatus('🔄 Processing note file...', 'info');
            
            try {
                const response = await fetch('/process', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    currentResults = data.results;
                    displayResults(currentResults);
                    showStatus(`✅ ${data.message}`, 'success');
                } else {
                    showStatus(`❌ Error: ${data.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Error: ${error.message}`, 'error');
            }
        }
        
        async function transcribeImage(imagePath, index) {
            const apiKey = document.getElementById('apiKey').value;
            if (!apiKey) {
                showStatus('❌ Please enter OpenAI API key', 'error');
                return;
            }
            
            showStatus(`🤖 Transcribing image ${index + 1}...`, 'info');
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_path: imagePath, api_key: apiKey })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showStatus(`❌ Transcription failed: ${data.error}`, 'error');
                } else {
                    currentResults[index].transcription = data.transcription;
                    currentResults[index].cost = data.cost;
                    displayResults(currentResults);
                    showStatus(`✅ Transcribed image ${index + 1} (cost: $${data.cost})`, 'success');
                }
            } catch (error) {
                showStatus(`❌ Error: ${error.message}`, 'error');
            }
        }
        
        async function transcribeImage(imagePath, index) {
            const apiKey = document.getElementById('apiKey').value;
            if (!apiKey) {
                showStatus('❌ Please enter OpenAI API key', 'error');
                return;
            }
            
            showStatus(`🤖 Transcribing image ${index + 1} with OpenAI...`, 'info');
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_path: imagePath, api_key: apiKey })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showStatus(`❌ Transcription failed: ${data.error}`, 'error');
                } else {
                    currentResults[index].transcription = data.transcription;
                    currentResults[index].cost = data.cost;
                    currentResults[index].provider = data.provider;
                    currentResults[index].model = data.model;
                    displayResults(currentResults);
                    showStatus(`✅ Transcribed image ${index + 1} (OpenAI, cost: $${data.cost})`, 'success');
                }
            } catch (error) {
                showStatus(`❌ Error: ${error.message}`, 'error');
            }
        }

        async function transcribeImageLocal(imagePath, index) {
            showStatus(`🖥️ Transcribing image ${index + 1} with local model...`, 'info');
            
            try {
                const response = await fetch('/transcribe_local', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_path: imagePath, model_name: 'qwen2.5vl:7b' })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showStatus(`❌ Local transcription failed: ${data.error}`, 'error');
                } else {
                    currentResults[index].transcription = data.transcription;
                    currentResults[index].cost = data.cost;
                    currentResults[index].processing_time = data.processing_time;
                    currentResults[index].provider = data.provider;
                    currentResults[index].model = data.model;
                    displayResults(currentResults);
                    showStatus(`✅ Transcribed image ${index + 1} (Local, ${data.processing_time}s, FREE)`, 'success');
                }
            } catch (error) {
                showStatus(`❌ Error: ${error.message}`, 'error');
            }
        }
        
        async function transcribeAll() {
            const contentImages = currentResults.filter(r => r.has_content);
            if (contentImages.length === 0) {
                showStatus('❌ No images with content to transcribe', 'error');
                return;
            }
            
            for (let i = 0; i < currentResults.length; i++) {
                if (currentResults[i].has_content) {
                    await transcribeImage(currentResults[i].image_path, i);
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Rate limiting
                }
            }
        }

        async function transcribeAllLocal() {
            const contentImages = currentResults.filter(r => r.has_content);
            if (contentImages.length === 0) {
                showStatus('❌ No images with content to transcribe', 'error');
                return;
            }
            
            for (let i = 0; i < currentResults.length; i++) {
                if (currentResults[i].has_content) {
                    await transcribeImageLocal(currentResults[i].image_path, i);
                    // No rate limiting needed for local model
                }
            }
        }
        
        function displayResults(results) {
            const container = document.getElementById('results');
            
            container.innerHTML = results.map((result, index) => `
                <div class="result-card">
                    <h3>📄 ${result.filename} - Page ${result.page}</h3>
                    
                    <div class="meta-info">
                        <strong>Visibility:</strong> ${result.visibility}<br>
                        <strong>Content Pixels:</strong> ${result.content_pixels.toLocaleString()}<br>
                        <strong>Mean Brightness:</strong> ${result.mean_brightness}<br>
                        <strong>Has Content:</strong> ${result.has_content ? '✅ Yes' : '❌ No'}<br>
                        <strong>Status:</strong> ${result.status}
                    </div>
                    
                    <div class="image-container">
                        <img src="/images/${result.image_path}" alt="Page ${result.page}" />
                    </div>
                    
                    ${result.transcription ? `
                        <div class="transcription">
                            <h4>🤖 AI Transcription</h4>
                            <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
                                Provider: ${result.provider || 'unknown'} | 
                                Model: ${result.model || 'unknown'} | 
                                ${result.cost !== undefined ? `Cost: $${result.cost}` : ''} 
                                ${result.processing_time ? `| Time: ${result.processing_time}s` : ''}
                            </div>
                            <p>${result.transcription}</p>
                        </div>
                    ` : result.has_content ? `
                        <div style="margin: 10px 0;">
                            <button class="button secondary" onclick="transcribeImageLocal('${result.image_path}', ${index})" style="margin-right: 10px;">
                                🖥️ Transcribe (Local)
                            </button>
                            <button class="button secondary" onclick="transcribeImage('${result.image_path}', ${index})">
                                ☁️ Transcribe (OpenAI)
                            </button>
                        </div>
                    ` : '<p style="color: #666;">No content detected - skipping transcription</p>'}
                </div>
            `).join('');
        }
        
        // Auto-load results on page load
        window.onload = function() {
            showStatus('💡 Click "Process Note File" to extract images from your Supernote file', 'info');
        };
    </script>
</body>
</html>'''

with open(templates_dir / "index.html", "w") as f:
    f.write(html_template)

if __name__ == '__main__':
    print("🚀 Starting Supernote Web Viewer")
    print("=" * 40)
    print("📱 Access at: http://localhost:5000")
    print("🔧 This will show extracted images and transcriptions")
    print("💡 Have your OpenAI API key ready for transcription")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)