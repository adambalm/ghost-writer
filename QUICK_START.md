# 🚀 Quick Start - Test Your Supernote Integration

## Step 1: Test Connection (30 seconds)

```bash
# Activate Python environment
source venv/bin/activate

# Run the quick test
python quick_supernote_test.py
```

**What this does:**
- Asks for your Supernote email/password
- Tests authentication with real API
- Shows your files from the cloud
- Confirms everything is working

## Step 2: Sync Your Files (1 minute)

```bash
# Download recent notes
ghost-writer sync --output supernote_downloads/

# OR download notes from specific date
ghost-writer sync --since 2025-01-01 --output supernote_downloads/
```

## Step 3: Process Your Notes (30 seconds)

```bash
# Convert a single .note file
ghost-writer process supernote_downloads/my_notes.note --format markdown

# OR process entire folder
ghost-writer process supernote_downloads/ --format all
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
- Make sure you ran `source venv/bin/activate` first
- Check that you're in the ghost-writer directory

---

**Ready?** Run: `source venv/bin/activate && python quick_supernote_test.py`