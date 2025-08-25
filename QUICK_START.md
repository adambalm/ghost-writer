# 🚀 Quick Start - Test Your Supernote Integration

## Step 1: Test Connection (30 seconds)

```bash
# Activate Python environment
source .venv/bin/activate

# Run the quick test
python scripts/quick_supernote_test.py
```

**What this does:**
- Asks for your Supernote email/password
- Tests authentication with real API
- Shows your files from the cloud
- Confirms everything is working

## Step 2: Sync Your Files (1 minute)

```bash
# Use the web interface for file sync and processing
source .venv/bin/activate
python web_viewer_demo_simple.py

# Open browser to http://localhost:5000
# Login with Supernote credentials and process notes
```

## Step 3: Process Your Notes (30 seconds)

The web interface handles processing automatically with:
- Qwen2.5-VL local vision model for handwriting transcription
- Real-time results display
- Multiple format exports

Or use CLI:
```bash
# Convert a single .note file
python -m src.cli process my_notes.note --format markdown

# OR process image files
python -m src.cli process notes_image.png --format all
```

## That's It! 

Your handwritten notes are now:
- ✅ Downloaded from Supernote Cloud
- ✅ Converted to text with OCR  
- ✅ Organized with AI structure detection
- ✅ Exported as Markdown/PDF/JSON

## If Something Goes Wrong

**Connection issues:**
- Check your email/password
- Make sure you can log into cloud.supernote.com in browser

**No files found:**
- Check if you have .note files in your cloud storage
- Try syncing from your Supernote device first

**Python errors:**
- Make sure you ran `source .venv/bin/activate` first
- Install Ollama and pull Qwen2.5-VL model: `ollama pull qwen2.5vl:7b`
- Check that you're in the ghost-writer directory

---

**Ready?** Run: `source venv/bin/activate && python quick_supernote_test.py`