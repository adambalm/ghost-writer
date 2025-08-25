#!/usr/bin/env python3
"""
Enhanced Web Interface for Supernote Demo with Auto-Auth and Fallback
Features: Auto-authentication, joe.note fallback, Demo Mode, Cloud Sync
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_socketio import SocketIO, emit
import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import base64
import secrets
import hashlib
import requests

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "sn2md"))

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
UPLOAD_FOLDER = project_root / "uploads"
RESULTS_FOLDER = project_root / "results"
DB_PATH = project_root / "demo_notes.db"
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)

# Demo mode state
demo_mode_active = False
demo_mode_thread = None
last_check_time = None
poll_interval = 60  # Default to 60 seconds in normal mode

# Auto-auth credentials (provided by user)
AUTO_AUTH_PHONE = "4139491742"
AUTO_AUTH_PASSWORD = "cesterCAT50supernote"

class CloudSyncManager:
    """Manages Supernote Cloud synchronization"""
    
    def __init__(self):
        self.base_url = "https://cloud.supernote.com/api"
        self.token = None
        self.authenticated = False
        self.init_database()
        # Auto-authenticate on startup
        self.auto_authenticate()
        
    def init_database(self):
        """Initialize SQLite database for note caching"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                size INTEGER,
                modified_time INTEGER,
                page_count INTEGER,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_fresh BOOLEAN DEFAULT 0,
                file_path TEXT,
                is_demo BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id TEXT,
                page_number INTEGER,
                transcription TEXT,
                provider TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (note_id) REFERENCES notes (id)
            )
        ''')
        
        # Add joe.note as a demo fallback
        self.add_demo_note()
        
        conn.commit()
        conn.close()
    
    def add_demo_note(self):
        """Add joe.note as a permanent demo fallback"""
        joe_note_path = project_root / "joe.note"
        if joe_note_path.exists():
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            # Check if joe.note already exists
            cursor.execute("SELECT id FROM notes WHERE name = ?", ("joe.note",))
            if not cursor.fetchone():
                # Add joe.note as a demo note
                cursor.execute('''
                    INSERT INTO notes (id, name, size, modified_time, page_count, is_fresh, file_path, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    "demo_joe_note",
                    "joe.note (Demo)",
                    joe_note_path.stat().st_size,
                    int(joe_note_path.stat().st_mtime),
                    2,  # joe.note has 2 pages
                    0,  # Not fresh
                    str(joe_note_path),
                    1   # Is demo note
                ))
                print("Added joe.note as demo fallback")
            
            conn.commit()
            conn.close()
    
    def auto_authenticate(self):
        """Auto-authenticate with provided credentials"""
        print("Auto-authenticating with Supernote Cloud...")
        success = self.authenticate(AUTO_AUTH_PHONE, AUTO_AUTH_PASSWORD)
        if success:
            print("✅ Auto-authentication successful!")
            self.authenticated = True
        else:
            print("⚠️ Auto-authentication failed, but demo note is available")
        return success
    
    def authenticate(self, phone_number, password):
        """Authenticate with Supernote Cloud"""
        try:
            # Get random code
            random_params = {"countryCode": "1", "account": phone_number}
            response = requests.post(
                f"{self.base_url}/official/user/query/random/code",
                json=random_params,
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                if data.get("success"):
                    random_code = data.get("randomCode")
                    
                    # Authenticate with provided password
                    password_md5 = hashlib.md5(password.encode()).hexdigest().lower()
                    password_hash = hashlib.sha256(
                        (password_md5 + random_code).encode()
                    ).hexdigest().lower()
                    
                    auth_params = {
                        "countryCode": "1",
                        "account": phone_number,
                        "password": password_hash,
                        "isEmail": False
                    }
                    
                    auth_response = requests.post(
                        f"{self.base_url}/official/user/account/login/new",
                        json=auth_params,
                        timeout=10
                    )
                    
                    if auth_response.ok:
                        auth_data = auth_response.json()
                        if auth_data.get("success"):
                            self.token = auth_data.get("token")
                            self.authenticated = True
                            return True
        except Exception as e:
            print(f"Authentication error: {e}")
        return False
    
    def get_recent_notes(self, since_minutes=5):
        """Get notes modified in the last N minutes"""
        # First try cloud notes if authenticated
        cloud_notes = []
        if self.token:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {
                    "directoryId": "",
                    "order": "time",
                    "pageNo": 0,
                    "pageSize": 50
                }
                
                response = requests.get(
                    f"{self.base_url}/file/list/query",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.ok:
                    data = response.json()
                    if data.get("success"):
                        files = data.get("fileList", [])
                        
                        # Filter for recent .note files
                        cutoff_time = datetime.now() - timedelta(minutes=since_minutes)
                        
                        for file in files:
                            if file.get("name", "").endswith(".note"):
                                # Check modification time
                                mod_time = file.get("modifyTime", 0) / 1000  # Convert from ms
                                mod_datetime = datetime.fromtimestamp(mod_time)
                                
                                is_fresh = mod_datetime > cutoff_time
                                
                                note = {
                                    "id": file.get("id"),
                                    "name": file.get("name"),
                                    "size": file.get("size"),
                                    "modified_time": mod_time,
                                    "is_fresh": is_fresh,
                                    "page_count": file.get("pageCount", 1),
                                    "is_demo": False
                                }
                                cloud_notes.append(note)
                        
                        # Store in database
                        if cloud_notes:
                            self.cache_notes(cloud_notes)
                            
            except Exception as e:
                print(f"Error fetching cloud notes: {e}")
        
        # Always include demo notes from database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, size, modified_time, page_count, is_fresh, file_path, is_demo
            FROM notes
            ORDER BY is_demo DESC, modified_time DESC
        ''')
        
        all_notes = []
        for row in cursor.fetchall():
            note = {
                "id": row[0],
                "name": row[1],
                "size": row[2],
                "modified_time": row[3],
                "page_count": row[4],
                "is_fresh": bool(row[5]),
                "file_path": row[6],
                "is_demo": bool(row[7])
            }
            all_notes.append(note)
        
        conn.close()
        
        # Return combined list (demo notes first)
        return all_notes
    
    def cache_notes(self, notes):
        """Cache notes in SQLite database"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        for note in notes:
            if not note.get('is_demo'):  # Don't overwrite demo notes
                cursor.execute('''
                    INSERT OR REPLACE INTO notes (id, name, size, modified_time, page_count, is_fresh, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    note['id'],
                    note['name'],
                    note['size'],
                    note['modified_time'],
                    note.get('page_count', 1),
                    note['is_fresh'],
                    0  # Not a demo note
                ))
        
        conn.commit()
        conn.close()
    
    def download_note(self, note_id):
        """Download a note file from Supernote Cloud"""
        # Check if it's a demo note first
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, is_demo FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            file_path, is_demo = row
            if is_demo and file_path and Path(file_path).exists():
                return Path(file_path)
        
        # Try to download from cloud
        if not self.token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get download URL
            url_response = requests.get(
                f"{self.base_url}/file/download/url",
                headers=headers,
                params={"id": note_id},
                timeout=10
            )
            
            if url_response.ok:
                url_data = url_response.json()
                if url_data.get("success"):
                    download_url = url_data.get("url")
                    
                    # Download file
                    file_response = requests.get(download_url, timeout=30)
                    if file_response.ok:
                        # Save to temp folder
                        note_name = self.get_note_name(note_id)
                        file_path = UPLOAD_FOLDER / f"{note_id}_{note_name}"
                        
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)
                        
                        # Update database
                        conn = sqlite3.connect(str(DB_PATH))
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE notes SET file_path = ? WHERE id = ?",
                            (str(file_path), note_id)
                        )
                        conn.commit()
                        conn.close()
                        
                        return file_path
        except Exception as e:
            print(f"Error downloading note: {e}")
        return None
    
    def get_note_name(self, note_id):
        """Get note name from database"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM notes WHERE id = ?", (note_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "unknown.note"

class SupernoteProcessor:
    """Process Supernote files for display and transcription"""
    
    def __init__(self):
        self.results = []
        
    def process_file(self, note_file_path):
        """Process a Supernote file - VISIBLE mode only for demo"""
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
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.15)  # 15% contrast boost
                
                # Save image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{timestamp}_page_{page_idx + 1}.png"
                image_path = RESULTS_FOLDER / image_filename
                img.save(str(image_path))
                
                # Analyze content
                import numpy as np
                arr = np.array(img)
                mean_val = arr.mean()
                non_white = np.sum(arr < 250)
                
                # Skip nearly empty pages (unless it's joe.note which we know has content)
                content_ratio = non_white / arr.size
                if content_ratio < 0.0001 and "joe" not in str(note_file_path).lower():
                    continue
                
                result = {
                    "page": int(page_idx + 1),
                    "image_path": str(image_filename),
                    "mean_brightness": float(round(mean_val, 2)),
                    "content_pixels": int(non_white),
                    "has_content": True,  # Assume all kept pages have content
                    "timestamp": str(timestamp),
                    "transcription": None,
                    "status": "extracted"
                }
                
                results.append(result)
                print(f"  Page {page_idx + 1}: {non_white:,} pixels")
            
            return results
            
        except Exception as e:
            print(f"Processing failed: {e}")
            import traceback
            traceback.print_exc()
            return [{"error": str(e)}]
    
    def transcribe_image(self, image_path, api_key):
        """Transcribe using OpenAI GPT-4 Vision"""
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
                "provider": "openai",
                "confidence": 0.95
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def transcribe_image_local(self, image_path, model_name="qwen2.5vl:7b"):
        """Transcribe using local Ollama model"""
        try:
            import subprocess
            import time
            
            start_time = time.time()
            
            prompt = "Transcribe this handwritten text carefully. Use context clues to correct obvious OCR errors and ensure the text makes semantic sense."
            
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
                
                # Clean up output
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
                    "provider": "ollama",
                    "confidence": 0.85
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

# Initialize managers
sync_manager = CloudSyncManager()
processor = SupernoteProcessor()

def demo_mode_polling():
    """Background thread for demo mode polling"""
    global demo_mode_active, last_check_time
    
    while demo_mode_active:
        check_for_new_notes()
        time.sleep(15)  # Poll every 15 seconds in demo mode

def check_for_new_notes():
    """Check for new notes and emit updates via WebSocket"""
    global last_check_time
    
    last_check_time = datetime.now()
    new_notes = sync_manager.get_recent_notes(since_minutes=5)
    
    # Count fresh notes (excluding demo notes)
    fresh_count = sum(1 for n in new_notes if n.get('is_fresh') and not n.get('is_demo'))
    
    # Emit update via WebSocket
    socketio.emit('notes_updated', {
        'notes': new_notes,
        'fresh_count': fresh_count,
        'last_check': last_check_time.isoformat(),
        'total_count': len(new_notes)
    })
    
    return new_notes

@app.route('/')
def index():
    """Main interface"""
    # Load initial notes on page load
    initial_notes = sync_manager.get_recent_notes(since_minutes=60)
    return render_template('demo_interface.html')

@app.route('/toggle_demo_mode', methods=['POST'])
def toggle_demo_mode():
    """Toggle demo mode on/off"""
    global demo_mode_active, demo_mode_thread, poll_interval
    
    data = request.json
    enable = data.get('enable', False)
    
    if enable and not demo_mode_active:
        # Start demo mode
        demo_mode_active = True
        poll_interval = 15
        demo_mode_thread = threading.Thread(target=demo_mode_polling)
        demo_mode_thread.daemon = True
        demo_mode_thread.start()
        
        # Do immediate check
        check_for_new_notes()
        
        return jsonify({
            "success": True,
            "mode": "demo",
            "poll_interval": poll_interval,
            "message": "Demo mode activated - checking every 15 seconds"
        })
    
    elif not enable and demo_mode_active:
        # Stop demo mode
        demo_mode_active = False
        poll_interval = 60
        
        return jsonify({
            "success": True,
            "mode": "normal",
            "poll_interval": poll_interval,
            "message": "Demo mode deactivated - manual checking only"
        })
    
    return jsonify({
        "success": True,
        "mode": "demo" if demo_mode_active else "normal",
        "poll_interval": poll_interval
    })

@app.route('/check_notes', methods=['POST'])
def check_notes():
    """Manual check for new notes"""
    notes = check_for_new_notes()
    
    return jsonify({
        "success": True,
        "notes": notes,
        "last_check": last_check_time.isoformat() if last_check_time else None,
        "fresh_count": sum(1 for n in notes if n.get('is_fresh') and not n.get('is_demo'))
    })

@app.route('/get_notes')
def get_notes():
    """Get all cached notes from database"""
    notes = sync_manager.get_recent_notes(since_minutes=60)
    return jsonify({"notes": notes})

@app.route('/process_notes', methods=['POST'])
def process_notes():
    """Process selected notes"""
    data = request.json
    note_ids = data.get('note_ids', [])
    
    if not note_ids:
        return jsonify({"error": "No notes selected"})
    
    all_results = []
    
    for note_id in note_ids:
        # Get note info from database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, name, is_demo FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            continue
        
        file_path = row[0]
        note_name = row[1]
        is_demo = row[2]
        
        # For demo notes, use existing path
        if is_demo and file_path:
            file_path = Path(file_path)
        # For cloud notes, download if needed
        elif not file_path or not Path(file_path).exists():
            file_path = sync_manager.download_note(note_id)
            if not file_path:
                continue
        else:
            file_path = Path(file_path)
        
        # Process the file
        results = processor.process_file(file_path)
        
        # Add note info to results
        for result in results:
            if not result.get('error'):
                result['note_id'] = note_id
                result['note_name'] = note_name
                result['is_demo'] = is_demo
        
        all_results.extend(results)
        
        # Emit progress
        socketio.emit('processing_progress', {
            'current': len(all_results),
            'total': len(note_ids),
            'note_name': note_name
        })
    
    return jsonify({
        "success": True,
        "results": all_results,
        "processed_count": len(note_ids)
    })

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe with OpenAI"""
    data = request.json
    image_path = data.get('image_path')
    api_key = data.get('api_key')
    note_id = data.get('note_id')
    page_number = data.get('page_number')
    
    if not api_key:
        return jsonify({"error": "API key required"})
    
    result = processor.transcribe_image(image_path, api_key)
    
    # Store in database if successful
    if result.get('transcription') and note_id:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transcriptions (note_id, page_number, transcription, provider, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (note_id, page_number, result['transcription'], 'openai', result.get('confidence', 0.95)))
        conn.commit()
        conn.close()
    
    return jsonify(result)

@app.route('/transcribe_local', methods=['POST'])
def transcribe_local():
    """Transcribe with local Ollama"""
    data = request.json
    image_path = data.get('image_path')
    model_name = data.get('model_name', 'qwen2.5vl:7b')
    note_id = data.get('note_id')
    page_number = data.get('page_number')
    
    result = processor.transcribe_image_local(image_path, model_name)
    
    # Store in database if successful
    if result.get('transcription') and note_id:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transcriptions (note_id, page_number, transcription, provider, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (note_id, page_number, result['transcription'], 'ollama', result.get('confidence', 0.85)))
        conn.commit()
        conn.close()
    
    return jsonify(result)

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve extracted images"""
    return send_from_directory(RESULTS_FOLDER, filename)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {
        'demo_mode': demo_mode_active,
        'poll_interval': poll_interval,
        'authenticated': sync_manager.authenticated
    })
    
    # Send initial notes
    initial_notes = sync_manager.get_recent_notes(since_minutes=60)
    emit('notes_updated', {
        'notes': initial_notes,
        'fresh_count': sum(1 for n in initial_notes if n.get('is_fresh') and not n.get('is_demo')),
        'last_check': datetime.now().isoformat(),
        'total_count': len(initial_notes)
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("🚀 Starting Enhanced Supernote Demo Web Viewer")
    print("=" * 50)
    print("📱 Access at: http://100.111.114.84:5000")
    print("✅ Auto-authentication enabled")
    print("📄 joe.note loaded as demo fallback")
    print("🎬 Features: Demo Mode, Cloud Sync, Note Selection")
    print("💡 Toggle Demo Mode for 15-second auto-refresh")
    print()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)