#!/usr/bin/env python3
"""
Simple Demo Web Interface - Based on working web_viewer_fixed.py
Adds: Demo Mode Toggle, Manual Check, Always shows joe.note
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import base64
import hashlib
import requests
import threading
import time

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

# Demo mode state
demo_mode_active = False
demo_mode_thread = None
last_check_time = None
supernote_token = None

# Demo mode requires user to provide credentials via environment variables or login prompt
# Never hardcode credentials in source code

class SupernoteProcessor:
    def __init__(self):
        self.results = []
        
    def process_file(self, note_file_path):
        """Process a Supernote file and return results - VISIBLE mode only"""
        try:
            from sn2md.importers.note import load_notebook
            import supernotelib as sn
            from supernotelib.converter import ImageConverter, VisibilityOverlay
            
            print(f"Processing: {note_file_path}")
            
            # Load notebook
            notebook = load_notebook(note_file_path)
            converter = ImageConverter(notebook)
            
            # Use VISIBLE mode only for clear demo display
            vo = sn.converter.build_visibility_overlay(background=VisibilityOverlay.VISIBLE)
            
            results = []
            
            for page_idx in range(notebook.get_total_pages()):
                img = converter.convert(page_idx, vo)
                
                # Add contrast boost for demo visibility
                try:
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.15)  # 15% contrast boost
                except:
                    pass  # If PIL not available, use original
                
                # Save image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{timestamp}_page_{page_idx + 1}_{Path(note_file_path).stem}.png"
                image_path = RESULTS_FOLDER / image_filename
                img.save(str(image_path))
                
                # Analyze content
                import numpy as np
                arr = np.array(img)
                mean_val = arr.mean()
                non_white = np.sum(arr < 250)
                
                result = {
                    "filename": str(Path(note_file_path).name),
                    "page": int(page_idx + 1),
                    "visibility": "VISIBLE",
                    "image_path": str(image_filename),
                    "mean_brightness": float(round(mean_val, 2)),
                    "content_pixels": int(non_white),
                    "has_content": bool(non_white > 1000),
                    "timestamp": str(timestamp),
                    "transcription": None,
                    "status": "extracted"
                }
                
                results.append(result)
                print(f"  Page {page_idx + 1}: {non_white:,} pixels")
                        
            return results
            
        except Exception as e:
            print(f"Processing failed: {e}")
            return [{"error": str(e), "filename": Path(note_file_path).name}]
    
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
            
            prompt = "Transcribe this handwritten text carefully. Use context clues to correct obvious OCR errors and ensure the text makes semantic sense. If you see unclear words, choose the most contextually appropriate word that fits the meaning of the sentence."
            
            full_image_path = RESULTS_FOLDER / image_path
            
            cmd = [
                "ollama", "run", model_name,
                prompt,
                str(full_image_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                transcription = result.stdout.strip()
                
                # Clean up any control characters from terminal output
                lines = transcription.split('\n')
                clean_lines = []
                for line in lines:
                    if line.strip() and not line.startswith('Added image') and not '[?' in line:
                        clean_lines.append(line.strip())
                
                final_transcription = '\n'.join(clean_lines) if clean_lines else transcription
                
                return {
                    "transcription": final_transcription,
                    "cost": 0.0,
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

def authenticate_supernote(phone, password):
    """Authenticate with Supernote Cloud"""
    global supernote_token
    
    try:
        base_url = "https://cloud.supernote.com/api"
        
        # Get random code
        random_params = {"countryCode": "1", "account": phone}
        response = requests.post(f"{base_url}/official/user/query/random/code", json=random_params, timeout=10)
        
        if response.ok:
            data = response.json()
            if data.get("success"):
                random_code = data.get("randomCode")
                
                # Authenticate
                password_md5 = hashlib.md5(password.encode()).hexdigest().lower()
                password_hash = hashlib.sha256((password_md5 + random_code).encode()).hexdigest().lower()
                
                auth_params = {
                    "countryCode": "1",
                    "account": phone,
                    "password": password_hash,
                    "isEmail": False
                }
                
                auth_response = requests.post(f"{base_url}/official/user/account/login/new", json=auth_params, timeout=10)
                
                if auth_response.ok:
                    auth_data = auth_response.json()
                    if auth_data.get("success"):
                        supernote_token = auth_data.get("token")
                        return True
    except Exception as e:
        print(f"Auth error: {e}")
    return False

def get_supernote_files():
    """Get files from Supernote Cloud"""
    global supernote_token
    
    if not supernote_token:
        return []
    
    try:
        base_url = "https://cloud.supernote.com/api"
        headers = {"Authorization": f"Bearer {supernote_token}"}
        params = {"directoryId": "", "order": "time", "pageNo": 0, "pageSize": 20}
        
        response = requests.get(f"{base_url}/file/list/query", headers=headers, params=params, timeout=10)
        
        if response.ok:
            data = response.json()
            if data.get("success"):
                files = data.get("fileList", [])
                note_files = []
                
                for file in files:
                    if file.get("name", "").endswith(".note"):
                        # Check if it's recent (last 5 minutes)
                        mod_time = file.get("modifyTime", 0) / 1000
                        mod_datetime = datetime.fromtimestamp(mod_time)
                        is_fresh = (datetime.now() - mod_datetime).total_seconds() < 300  # 5 minutes
                        
                        note_files.append({
                            "id": file.get("id"),
                            "name": file.get("name"),
                            "size": file.get("size"),
                            "modified_time": mod_time,
                            "is_fresh": is_fresh
                        })
                
                return note_files
                
    except Exception as e:
        print(f"File list error: {e}")
    
    return []

def demo_mode_polling():
    """Background thread for demo mode"""
    global demo_mode_active, last_check_time, supernote_token
    
    # Auto-authenticate when demo mode starts (currently disabled due to password issue)
    if not supernote_token:
        print("Demo mode: Cloud authentication temporarily disabled")
        print("Demo will work with joe.note fallback")
        # authenticate_supernote(DEMO_PHONE, DEMO_PASSWORD)
    
    while demo_mode_active:
        last_check_time = datetime.now()
        print(f"Demo mode check at {last_check_time}")
        time.sleep(15)  # Check every 15 seconds

processor = SupernoteProcessor()

@app.route('/')
def index():
    """Main interface"""
    return render_template('demo_simple.html')

@app.route('/toggle_demo_mode', methods=['POST'])
def toggle_demo_mode():
    """Toggle demo mode"""
    global demo_mode_active, demo_mode_thread
    
    data = request.json
    enable = data.get('enable', False)
    
    if enable and not demo_mode_active:
        demo_mode_active = True
        demo_mode_thread = threading.Thread(target=demo_mode_polling)
        demo_mode_thread.daemon = True
        demo_mode_thread.start()
        
        return jsonify({
            "success": True,
            "mode": "demo",
            "message": "Demo mode ON - checking every 15 seconds"
        })
    
    elif not enable and demo_mode_active:
        demo_mode_active = False
        
        return jsonify({
            "success": True,
            "mode": "normal", 
            "message": "Demo mode OFF - manual only"
        })
    
    return jsonify({
        "success": True,
        "mode": "demo" if demo_mode_active else "normal"
    })

@app.route('/check_for_new_notes', methods=['POST'])
def check_for_new_notes():
    """Manual check for new notes"""
    global last_check_time, supernote_token
    
    # Authenticate if needed
    if not supernote_token:
        auth_success = authenticate_supernote(DEMO_PHONE, DEMO_PASSWORD)
        if not auth_success:
            return jsonify({
                "success": False,
                "error": "Authentication failed"
            })
    
    last_check_time = datetime.now()
    cloud_files = get_supernote_files()
    
    # Always include joe.note as an option
    available_notes = [{
        "id": "joe_note",
        "name": "joe.note (Demo File)",
        "size": 1024000,  # Approximate
        "is_demo": True,
        "is_fresh": False
    }]
    
    # Add cloud files
    fresh_count = 0
    for file in cloud_files:
        available_notes.append(file)
        if file.get('is_fresh'):
            fresh_count += 1
    
    return jsonify({
        "success": True,
        "notes": available_notes,
        "fresh_count": fresh_count,
        "last_check": last_check_time.isoformat()
    })

@app.route('/process_note', methods=['POST'])
def process_note():
    """Process a specific note"""
    data = request.json
    note_id = data.get('note_id')
    
    if note_id == 'joe_note':
        # Process the local joe.note file
        note_file = project_root / "joe.note"
        if not note_file.exists():
            return jsonify({"error": "joe.note not found"})
        
        results = processor.process_file(note_file)
        
        return jsonify({
            "success": True,
            "results": results,
            "note_name": "joe.note (Demo)"
        })
    
    else:
        # TODO: Download and process cloud file
        return jsonify({"error": "Cloud file processing not yet implemented"})

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

@app.route('/get_demo_status')
def get_demo_status():
    """Get current demo mode status"""
    return jsonify({
        "demo_mode": demo_mode_active,
        "last_check": last_check_time.isoformat() if last_check_time else None,
        "authenticated": bool(supernote_token)
    })

if __name__ == '__main__':
    print("🚀 Starting Simple Supernote Demo Viewer")
    print("=" * 50)
    print("📱 Access at: http://100.111.114.84:5000")
    print("📄 joe.note always available as demo fallback")
    print("🎬 Toggle Demo Mode for 15-second cloud checking")
    print("🔄 Manual 'Check for New Notes' button")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)