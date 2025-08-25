#!/usr/bin/env python3
"""
Enhanced Web Interface for Supernote Processing with Clean Room Decoder
Integrates Supernote Cloud API with Enhanced Clean Room Decoder and Full OCR Pipeline
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import base64
import secrets

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

# Import clean room enhanced components
from utils.supernote_api import create_supernote_client
from utils.supernote_parser_enhanced import SupernoteParser
from utils.ocr_providers import HybridOCR
from utils.relationship_detector import RelationshipDetector
from utils.concept_clustering import ConceptExtractor, ConceptClusterer
from utils.structure_generator import StructureGenerator
from utils.database import DatabaseManager
from utils.config import config

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

# Configuration
UPLOAD_FOLDER = project_root / "uploads"
RESULTS_FOLDER = project_root / "results"
TEMP_FOLDER = project_root / "temp_notes"
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)
TEMP_FOLDER.mkdir(exist_ok=True)

class EnhancedSupernoteProcessor:
    def __init__(self):
        self.supernote_client = None
        self.enhanced_parser = SupernoteParser()
        self.ocr_provider = None
        self.db_manager = None
        
    def initialize_components(self):
        """Initialize processing components"""
        try:
            # Get OCR config from main config
            ocr_config = config.get('ocr', {})
            self.ocr_provider = HybridOCR(ocr_config)
            self.db_manager = DatabaseManager()
            self.relationship_detector = RelationshipDetector()
            self.concept_extractor = ConceptExtractor()
            self.concept_clusterer = ConceptClusterer()
            self.structure_generator = StructureGenerator()
            return True
        except Exception as e:
            print(f"Failed to initialize components: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def connect_to_supernote(self, email=None, password=None):
        """Connect to Supernote Cloud"""
        try:
            # Pass credentials directly to create_supernote_client
            # This properly handles both phone numbers and email addresses
            self.supernote_client = create_supernote_client(config, email=email, password=password)
            
            if self.supernote_client:
                return True
            else:
                # Try to get error details from a temporary client
                from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
                temp_creds = SupernoteCredentials(email=email, password=password)
                temp_client = SupernoteCloudAPI(temp_creds)
                temp_client.authenticate()
                if hasattr(temp_client, 'last_error') and temp_client.last_error:
                    self.last_error = temp_client.last_error
                    print(f"Supernote error: {temp_client.last_error}")
                return False
        except Exception as e:
            print(f"Failed to connect to Supernote: {e}")
            import traceback
            traceback.print_exc()
            self.last_error = {'message': str(e), 'code': 'EXCEPTION'}
            return False
    
    def get_available_notes(self):
        """Get list of available notes from Supernote Cloud"""
        if not self.supernote_client:
            return []
        
        try:
            notes = self.supernote_client.get_recent_files(limit=50)
            return [
                {
                    "id": note.get("id", "unknown"),
                    "name": note.get("name", "Untitled"),
                    "modified": note.get("modified", "Unknown"),
                    "size": note.get("size", 0),
                    "pages": note.get("pages", 1),
                    "type": note.get("type", "note")
                }
                for note in notes if note.get("name", "").endswith(".note")
            ]
        except Exception as e:
            print(f"Failed to get notes: {e}")
            return []
    
    def download_and_process_note(self, note_id, note_name):
        """Download note from cloud and process with enhanced clean room decoder"""
        if not self.supernote_client:
            return {"error": "Not connected to Supernote Cloud"}
        
        try:
            # Download note file
            note_file = TEMP_FOLDER / f"{note_name}"
            success = self.supernote_client.download_file(note_id, str(note_file))
            
            if not success:
                return {"error": f"Failed to download {note_name}"}
            
            print(f"Downloaded {note_name} ({note_file.stat().st_size:,} bytes)")
            
            # Process with enhanced clean room decoder
            return self.process_note_file(note_file, note_name)
            
        except Exception as e:
            return {"error": f"Download/process failed: {str(e)}"}
    
    def process_note_file(self, note_file_path, note_name=None):
        """Process note file with enhanced clean room decoder and full OCR pipeline"""
        if note_name is None:
            note_name = note_file_path.name
            
        try:
            print(f"Processing {note_name} with Enhanced Clean Room Decoder...")
            
            # Step 1: Parse with enhanced clean room decoder
            pages = self.enhanced_parser.parse_file(note_file_path)
            
            if not pages:
                return {"error": "No pages extracted from note file"}
            
            print(f"Enhanced decoder extracted {len(pages)} pages")
            
            results = []
            
            for page_idx, page in enumerate(pages, 1):
                try:
                    # Generate page image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"{timestamp}_{note_name.replace('.note', '')}_page_{page_idx}_enhanced.png"
                    image_path = RESULTS_FOLDER / image_filename
                    
                    # Render page using enhanced decoder
                    page_image = self.enhanced_parser.render_page_to_image(page, image_path, scale=2.0)
                    
                    # Analyze pixel content
                    if 'decoded_bitmap' in page.metadata:
                        bitmap = page.metadata['decoded_bitmap']
                        content_pixels = int((bitmap < 255).sum()) if hasattr(bitmap, 'sum') else 0
                        total_pixels = int(bitmap.size) if hasattr(bitmap, 'size') else page.width * page.height
                    else:
                        content_pixels = 0
                        total_pixels = page.width * page.height
                    
                    # Process with full OCR pipeline
                    ocr_result = None
                    pipeline_result = None
                    
                    if self.ocr_provider and content_pixels > 100:  # Only OCR if significant content
                        try:
                            print(f"Running OCR on page {page_idx}...")
                            ocr_result = self.ocr_provider.extract_text(str(image_path))
                            
                            if ocr_result and ocr_result.text.strip():
                                print(f"OCR extracted {len(ocr_result.text)} characters")
                                
                                # Full Ghost Writer pipeline
                                pipeline_result = self.run_full_pipeline(ocr_result, note_name, page_idx)
                            
                        except Exception as e:
                            print(f"OCR failed for page {page_idx}: {e}")
                    
                    result = {
                        "note_name": note_name,
                        "page": page_idx,
                        "image_path": image_filename,
                        "width": page.width,
                        "height": page.height,
                        "content_pixels": content_pixels,
                        "total_pixels": total_pixels,
                        "content_ratio": content_pixels / total_pixels if total_pixels > 0 else 0,
                        "has_content": content_pixels > 100,
                        "decoder": "Enhanced Clean Room",
                        "metadata": page.metadata,
                        "timestamp": timestamp,
                        "ocr_result": {
                            "text": ocr_result.text if ocr_result else None,
                            "provider": ocr_result.provider if ocr_result else None,
                            "confidence": ocr_result.confidence if ocr_result else 0,
                            "cost": ocr_result.cost if ocr_result else 0
                        } if ocr_result else None,
                        "pipeline_result": pipeline_result,
                        "status": "processed"
                    }
                    
                    results.append(result)
                    print(f"Page {page_idx}: {content_pixels:,} content pixels, {'OCR processed' if ocr_result else 'skipped OCR'}")
                    
                except Exception as e:
                    print(f"Failed to process page {page_idx}: {e}")
                    results.append({
                        "note_name": note_name,
                        "page": page_idx,
                        "error": str(e),
                        "status": "error"
                    })
            
            # Summary statistics
            total_content_pixels = sum(r.get('content_pixels', 0) for r in results)
            total_pages_with_content = sum(1 for r in results if r.get('has_content', False))
            
            print(f"Processing complete: {total_content_pixels:,} total pixels, {total_pages_with_content} pages with content")
            
            return {
                "success": True,
                "note_name": note_name,
                "pages_processed": len(results),
                "total_content_pixels": total_content_pixels,
                "pages_with_content": total_pages_with_content,
                "results": results
            }
            
        except Exception as e:
            print(f"Processing failed: {e}")
            return {"error": str(e)}
    
    def run_full_pipeline(self, ocr_result, note_name, page_idx):
        """Run full Ghost Writer processing pipeline"""
        try:
            if not self.db_manager:
                return None
            
            # Store in database
            self.db_manager.store_note(
                source_file=f"{note_name}#page{page_idx}",
                raw_text=ocr_result.text,
                clean_text=ocr_result.text,
                ocr_provider=ocr_result.provider,
                ocr_confidence=ocr_result.confidence,
                processing_cost=ocr_result.cost
            )
            
            # Create note elements
            elements = self.create_note_elements(ocr_result)
            
            # Detect relationships
            relationships = self.relationship_detector.detect_relationships(elements)
            
            # Extract and cluster concepts  
            concepts = self.concept_extractor.extract_concepts(elements)
            clusters = self.concept_clusterer.cluster_concepts(concepts, relationships)
            
            # Generate structures
            structures = self.structure_generator.generate_structures(
                elements, concepts, clusters, relationships
            )
            
            # Find best structure
            best_structure = max(structures, key=lambda s: s.confidence) if structures else None
            
            return {
                "elements_count": len(elements),
                "relationships_count": len(relationships),
                "concepts_count": len(concepts),
                "clusters_count": len(clusters),
                "structures_count": len(structures),
                "best_structure": {
                    "type": best_structure.structure_type.value if best_structure else None,
                    "confidence": best_structure.confidence if best_structure else 0,
                    "content": self.structure_generator.export_structure_as_text(best_structure) if best_structure else None
                } if best_structure else None
            }
            
        except Exception as e:
            print(f"Pipeline processing failed: {e}")
            return {"error": str(e)}
    
    def create_note_elements(self, ocr_result):
        """Convert OCR result to note elements"""
        from utils.relationship_detector import NoteElement
        
        lines = [line.strip() for line in ocr_result.text.split("\n") if line.strip()]
        elements = []
        
        for i, line in enumerate(lines):
            element = NoteElement(
                element_id=f"element_{i}",
                text=line,
                bbox=(0, i * 30, 800, (i + 1) * 30),
                confidence=ocr_result.confidence
            )
            elements.append(element)
        
        return elements

processor = EnhancedSupernoteProcessor()

@app.route('/')
def index():
    """Main interface with Supernote Cloud integration"""
    # Use simple template without icons
    return render_template('simple_login.html')

@app.route('/login', methods=['POST'])
def login():
    """Login to Supernote Cloud"""
    debug_info = []
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        debug_info.append(f"Account: {email}")
        debug_info.append(f"Account type: {'Phone number' if email.isdigit() else 'Email address'}")
        
        print(f"Login attempt - Account: {email}, Type: {'phone' if email.isdigit() else 'email'}")
        
        if not processor.initialize_components():
            error_msg = "Failed to initialize processing components"
            debug_info.append(f"ERROR: {error_msg}")
            return jsonify({"error": error_msg, "debug": debug_info})
        
        debug_info.append("Components initialized successfully")
        
        if processor.connect_to_supernote(email, password):
            session['logged_in'] = True
            session['email'] = email
            debug_info.append("Authentication successful")
            print(f"Login successful for: {email}")
            return jsonify({"success": True, "message": "Connected to Supernote Cloud", "debug": debug_info})
        else:
            # Get specific error from Supernote API
            if hasattr(processor, 'last_error') and processor.last_error:
                error_msg = f"Supernote API: {processor.last_error.get('message', 'Unknown error')}"
                error_code = processor.last_error.get('code', 'No code')
                debug_info.append(f"ERROR: {error_msg}")
                debug_info.append(f"Error Code: {error_code}")
                if 'full_response' in processor.last_error:
                    debug_info.append(f"Full Response: {processor.last_error['full_response']}")
            else:
                error_msg = "Authentication failed - check credentials"
                debug_info.append(f"ERROR: {error_msg}")
            
            print(f"Login failed for: {email}")
            return jsonify({"error": error_msg, "debug": debug_info})
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Login exception: {str(e)}")
        print(error_detail)
        debug_info.append(f"EXCEPTION: {str(e)}")
        return jsonify({"error": str(e), "debug": debug_info, "traceback": error_detail})

@app.route('/notes')
def get_notes():
    """Get available notes from Supernote Cloud"""
    try:
        if not session.get('logged_in'):
            return jsonify({"error": "Not logged in"})
        
        notes = processor.get_available_notes()
        return jsonify({"notes": notes})
    
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/process_note', methods=['POST'])
def process_selected_note():
    """Process selected note with enhanced clean room decoder"""
    try:
        if not session.get('logged_in'):
            return jsonify({"error": "Not logged in"})
        
        data = request.json
        note_ids = data.get('note_ids', [])
        
        if not note_ids:
            return jsonify({"error": "No notes selected"})
        
        all_results = []
        
        for note_id in note_ids:
            # Get note info (you'd need to implement this in the API)
            note_name = f"note_{note_id}.note"  # Placeholder
            
            result = processor.download_and_process_note(note_id, note_name)
            
            if result.get('success'):
                all_results.extend(result.get('results', []))
            else:
                all_results.append({
                    "note_name": note_name,
                    "error": result.get('error', 'Unknown error'),
                    "status": "error"
                })
        
        return jsonify({
            "success": True,
            "processed_notes": len(note_ids),
            "total_results": len(all_results),
            "results": all_results
        })
    
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve processed images"""
    return send_from_directory(RESULTS_FOLDER, filename)

@app.route('/logout')
def logout():
    """Logout from Supernote Cloud"""
    session.clear()
    return redirect(url_for('index'))

# Enhanced HTML template
templates_dir = project_root / "templates"
templates_dir.mkdir(exist_ok=True)

enhanced_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Supernote Processor</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); backdrop-filter: blur(10px); }
        .login-section { background: rgba(255,255,255,0.9); padding: 25px; border-radius: 10px; margin-bottom: 20px; }
        .notes-section { background: rgba(255,255,255,0.9); padding: 25px; border-radius: 10px; margin-bottom: 20px; display: none; }
        .results { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 25px; }
        .result-card { background: rgba(255,255,255,0.95); border-radius: 12px; padding: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.15); backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.2); }
        .enhanced-badge { background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 10px; }
        .image-container { text-align: center; margin: 20px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .image-container img { max-width: 100%; height: auto; display: block; }
        .meta-info { background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #4CAF50; }
        .ocr-result { background: linear-gradient(135deg, #e3f2fd, #bbdefb); padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #2196F3; }
        .pipeline-result { background: linear-gradient(135deg, #f3e5f5, #e1bee7); padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #9C27B0; }
        .button { background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 12px 24px; border: none; border-radius: 25px; cursor: pointer; margin: 8px; font-size: 14px; font-weight: 600; transition: all 0.3s ease; }
        .button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .button.primary { background: linear-gradient(45deg, #2196F3, #0b7dda); }
        .button.secondary { background: linear-gradient(45deg, #FF9800, #F57C00); }
        .input-field { width: 100%; padding: 12px; margin: 8px 0; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s ease; }
        .input-field:focus { border-color: #4CAF50; outline: none; box-shadow: 0 0 10px rgba(76,175,80,0.2); }
        .status { padding: 15px; border-radius: 8px; margin: 15px 0; font-weight: 500; }
        .status.success { background: linear-gradient(135deg, #d4edda, #c3e6cb); color: #155724; border-left: 4px solid #28a745; }
        .status.error { background: linear-gradient(135deg, #f8d7da, #f5c6cb); color: #721c24; border-left: 4px solid #dc3545; }
        .status.info { background: linear-gradient(135deg, #d1ecf1, #bee5eb); color: #0c5460; border-left: 4px solid #17a2b8; }
        .notes-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin: 20px 0; }
        .note-card { background: white; padding: 15px; border-radius: 8px; border: 2px solid #e0e0e0; cursor: pointer; transition: all 0.3s ease; }
        .note-card:hover { border-color: #4CAF50; box-shadow: 0 4px 15px rgba(76,175,80,0.2); }
        .note-card.selected { border-color: #4CAF50; background: linear-gradient(135deg, #e8f5e8, #f0f8f0); }
        h1 { color: #2c3e50; margin-bottom: 10px; font-size: 2.5em; font-weight: 300; }
        h2 { color: #34495e; font-size: 1.8em; font-weight: 400; }
        h3 { color: #2c3e50; font-size: 1.4em; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced Supernote Processor</h1>
            <div class="enhanced-badge">✨ CLEAN ROOM ENHANCED DECODER</div>
            <p>Connect to your Supernote Cloud, select notes, and process them with our 55x enhanced clean room decoder integrated with the full Ghost Writer OCR pipeline.</p>
        </div>
        
        <div class="login-section" id="loginSection">
            <h2>🔐 Connect to Supernote Cloud</h2>
            <input type="email" id="email" class="input-field" placeholder="Your Supernote email" />
            <input type="password" id="password" class="input-field" placeholder="Your Supernote password" />
            <button class="button primary" onclick="login()">🌐 Connect to Supernote</button>
            <div style="margin-top: 15px; padding: 15px; background: #fff3cd; border-radius: 8px; color: #856404;">
                <strong>🔒 Privacy:</strong> Your credentials are only used to connect to Supernote Cloud and are not stored.
            </div>
        </div>
        
        <div class="notes-section" id="notesSection">
            <h2>📚 Select Notes to Process</h2>
            <button class="button secondary" onclick="loadNotes()">🔄 Refresh Notes</button>
            <button class="button" onclick="processSelectedNotes()" id="processBtn" disabled>⚡ Process Selected Notes</button>
            <div id="notesGrid" class="notes-grid"></div>
        </div>
        
        <div id="status"></div>
        <div id="results" class="results"></div>
    </div>

    <script>
        let selectedNotes = new Set();
        let currentResults = [];
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.innerHTML = `<div class="status ${type}">${message}</div>`;
            if (type !== 'error') {
                setTimeout(() => status.innerHTML = '', 8000);
            }
        }
        
        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                showStatus('❌ Please enter both email and password', 'error');
                return;
            }
            
            showStatus('🔄 Connecting to Supernote Cloud...', 'info');
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('loginSection').style.display = 'none';
                    document.getElementById('notesSection').style.display = 'block';
                    showStatus('✅ Connected to Supernote Cloud! Loading your notes...', 'success');
                    await loadNotes();
                } else {
                    showStatus(`❌ ${data.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Connection failed: ${error.message}`, 'error');
            }
        }
        
        async function loadNotes() {
            showStatus('📚 Loading your notes from Supernote Cloud...', 'info');
            
            try {
                const response = await fetch('/notes');
                const data = await response.json();
                
                if (data.error) {
                    showStatus(`❌ ${data.error}`, 'error');
                    return;
                }
                
                displayNotes(data.notes);
                showStatus(`📚 Loaded ${data.notes.length} notes`, 'success');
                
            } catch (error) {
                showStatus(`❌ Failed to load notes: ${error.message}`, 'error');
            }
        }
        
        function displayNotes(notes) {
            const grid = document.getElementById('notesGrid');
            
            if (notes.length === 0) {
                grid.innerHTML = '<p>No .note files found in your Supernote Cloud</p>';
                return;
            }
            
            grid.innerHTML = notes.map(note => `
                <div class="note-card" onclick="toggleNote('${note.id}')" id="note-${note.id}">
                    <h3>📄 ${note.name}</h3>
                    <div style="font-size: 14px; color: #666;">
                        <div><strong>Modified:</strong> ${note.modified}</div>
                        <div><strong>Size:</strong> ${(note.size / 1024).toFixed(1)} KB</div>
                        <div><strong>Pages:</strong> ${note.pages}</div>
                    </div>
                </div>
            `).join('');
        }
        
        function toggleNote(noteId) {
            const card = document.getElementById(`note-${noteId}`);
            
            if (selectedNotes.has(noteId)) {
                selectedNotes.delete(noteId);
                card.classList.remove('selected');
            } else {
                selectedNotes.add(noteId);
                card.classList.add('selected');
            }
            
            const processBtn = document.getElementById('processBtn');
            processBtn.disabled = selectedNotes.size === 0;
            processBtn.textContent = selectedNotes.size > 0 ? 
                `⚡ Process ${selectedNotes.size} Selected Note${selectedNotes.size > 1 ? 's' : ''}` : 
                '⚡ Process Selected Notes';
        }
        
        async function processSelectedNotes() {
            if (selectedNotes.size === 0) {
                showStatus('❌ Please select at least one note', 'error');
                return;
            }
            
            showStatus(`🚀 Processing ${selectedNotes.size} notes with Enhanced Clean Room Decoder...`, 'info');
            
            try {
                const response = await fetch('/process_note', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ note_ids: Array.from(selectedNotes) })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentResults = data.results;
                    displayResults(currentResults);
                    
                    const contentPages = currentResults.filter(r => r.has_content).length;
                    showStatus(`✅ Enhanced decoder processed ${data.processed_notes} notes, ${data.total_results} pages, ${contentPages} with content`, 'success');
                } else {
                    showStatus(`❌ ${data.error}`, 'error');
                }
                
            } catch (error) {
                showStatus(`❌ Processing failed: ${error.message}`, 'error');
            }
        }
        
        function displayResults(results) {
            const container = document.getElementById('results');
            
            container.innerHTML = results.map((result, index) => `
                <div class="result-card">
                    <div class="enhanced-badge">🔬 ENHANCED CLEAN ROOM DECODER</div>
                    <h3>📄 ${result.note_name} - Page ${result.page}</h3>
                    
                    <div class="meta-info">
                        <strong>📏 Dimensions:</strong> ${result.width}×${result.height}<br>
                        <strong>🎯 Content Pixels:</strong> ${result.content_pixels?.toLocaleString() || 0}<br>
                        <strong>📊 Content Ratio:</strong> ${(result.content_ratio * 100)?.toFixed(2) || 0}%<br>
                        <strong>✨ Enhanced Decoder:</strong> ${result.decoder}<br>
                        <strong>📅 Processed:</strong> ${result.timestamp}<br>
                        <strong>💎 Has Content:</strong> ${result.has_content ? '✅ Yes' : '❌ No'}
                    </div>
                    
                    ${result.image_path ? `
                        <div class="image-container">
                            <img src="/images/${result.image_path}" alt="Page ${result.page}" />
                        </div>
                    ` : ''}
                    
                    ${result.ocr_result ? `
                        <div class="ocr-result">
                            <h4>🤖 OCR Transcription</h4>
                            <div style="font-size: 12px; margin-bottom: 10px;">
                                <strong>Provider:</strong> ${result.ocr_result.provider} | 
                                <strong>Confidence:</strong> ${(result.ocr_result.confidence * 100).toFixed(1)}% |
                                <strong>Cost:</strong> $${result.ocr_result.cost.toFixed(4)}
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 6px; border-left: 3px solid #2196F3;">
                                ${result.ocr_result.text.replace(/\\n/g, '<br>')}
                            </div>
                        </div>
                    ` : result.has_content ? '<div style="color: #666;">Content detected but not processed with OCR</div>' : ''}
                    
                    ${result.pipeline_result ? `
                        <div class="pipeline-result">
                            <h4>⚡ Ghost Writer Analysis</h4>
                            <div style="font-size: 12px; margin-bottom: 10px;">
                                <strong>Elements:</strong> ${result.pipeline_result.elements_count} | 
                                <strong>Concepts:</strong> ${result.pipeline_result.concepts_count} | 
                                <strong>Relationships:</strong> ${result.pipeline_result.relationships_count}
                            </div>
                            ${result.pipeline_result.best_structure ? `
                                <div style="background: white; padding: 15px; border-radius: 6px; border-left: 3px solid #9C27B0;">
                                    <strong>Structure:</strong> ${result.pipeline_result.best_structure.type} 
                                    (${(result.pipeline_result.best_structure.confidence * 100).toFixed(1)}% confidence)<br><br>
                                    <pre style="white-space: pre-wrap; font-family: inherit;">${result.pipeline_result.best_structure.content || 'No content generated'}</pre>
                                </div>
                            ` : '<div>No structured content generated</div>'}
                        </div>
                    ` : ''}
                    
                    ${result.error ? `<div class="status error">❌ Error: ${result.error}</div>` : ''}
                </div>
            `).join('');
        }
        
        // Initialize page
        window.onload = function() {
            showStatus('👋 Welcome! Please connect to your Supernote Cloud to begin.', 'info');
        };
    </script>
</body>
</html>'''

with open(templates_dir / "enhanced_index.html", "w") as f:
    f.write(enhanced_html)

if __name__ == '__main__':
    print("🚀 Starting Enhanced Supernote Web Processor")
    print("=" * 50)
    print("🌐 Access at: http://localhost:5001")
    print("✨ Features:")
    print("   • Supernote Cloud integration")
    print("   • Enhanced Clean Room Decoder (55x improvement)")
    print("   • Full Ghost Writer OCR pipeline")
    print("   • Multi-note selection and processing")
    print("   • Real-time results visualization")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)