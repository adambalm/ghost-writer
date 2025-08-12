# Supernote Integration Guide

## Overview

Ghost Writer provides comprehensive integration with Supernote devices, allowing you to automatically sync, process, and organize your handwritten notes from the cloud or local files.

## Supported Features

### ✅ Current Implementation
- **Local .note file processing**: Parse and process Supernote binary files
- **Image export**: Convert .note files to images for OCR processing
- **CLI integration**: Command-line tools for batch processing
- **File watching**: Automatic processing of new files
- **Multiple export formats**: Markdown, PDF, JSON output
- **✨ Supernote Cloud API**: Direct cloud sync with real API integration
- **Automatic sync**: Download recent files and process automatically

### 🚧 In Development
- **Multi-page support**: Better handling of notebooks with multiple pages
- **Advanced .note parsing**: Improved vector graphics extraction
- **Scheduled sync**: Cron-style automatic syncing

## Quick Start

### 1. Setup

```bash
# Install Ghost Writer
pip install -e .

# Initialize the system
ghost-writer init

# Verify Supernote support
ghost-writer status
```

### 2. Process Local .note Files

```bash
# Process a single .note file
ghost-writer process my_notes.note

# Process with all output formats
ghost-writer process notebook.note --format all --output processed/

# Batch process a folder of .note files
ghost-writer process supernote_folder/ --format markdown
```

### 3. Auto-Processing Setup

```bash
# Watch your Supernote sync folder
ghost-writer watch ~/Supernote/ --format all --interval 10
```

## File Processing Pipeline

When you process a Supernote file, Ghost Writer follows this pipeline:

1. **Parse .note file** → Extract vector graphics and metadata
2. **Render to image** → Convert vector data to high-resolution PNG
3. **OCR Processing** → Extract text using hybrid OCR pipeline
4. **Idea Organization** → Detect relationships and cluster concepts
5. **Structure Generation** → Create organized document formats
6. **Export** → Save as Markdown, PDF, or JSON

## Configuration

### Basic Configuration

Edit `config/config.yaml`:

```yaml
# Supernote-specific settings
supernote:
  enabled: true
  local_sync_dir: "~/Supernote/"
  auto_process: true
  file_types: ["note", "pdf"]

# File processing
files:
  input_extensions: [".png", ".jpg", ".jpeg", ".note"]
  watch_directories: ["~/Supernote/", "data/notes/"]
  archive_processed: true
  archive_path: "data/archive/"
```

### Cloud Sync Configuration ✅ WORKING

```yaml
supernote:
  enabled: true
  email_env: SUPERNOTE_EMAIL
  password_env: SUPERNOTE_PASSWORD
  access_token_env: SUPERNOTE_ACCESS_TOKEN  # Automatically obtained after first login
  sync_interval: 3600  # Sync every hour
  local_sync_dir: "data/supernote_sync/"
  auto_process: true
  file_types: ["note", "pdf"]
```

**Setup Steps:**
1. Copy `config/supernote_example.yaml` to your main config
2. Export `SUPERNOTE_EMAIL` and `SUPERNOTE_PASSWORD` with your credentials
3. Test connection: `python test_supernote_api.py`
4. Start syncing: `ghost-writer sync`

## Usage Examples

### Process Individual Files

```bash
# Basic processing
ghost-writer process meeting_notes.note

# With custom output directory
ghost-writer process notes.note --output ~/Documents/processed/

# Premium quality with PDF output
ghost-writer process important.note --quality premium --format pdf

# Local-only processing (no cloud OCR)
ghost-writer process private.note --local-only --format markdown
```

### Batch Processing

```bash
# Process all .note files in a directory
ghost-writer process ~/Supernote/Notes/ --format all

# Process with filtering by date (future feature)
ghost-writer process ~/Supernote/ --since 2025-01-01 --format markdown

# Archive processed files
ghost-writer process ~/Supernote/ --archive --output processed/
```

### File Watching

```bash
# Basic file watching
ghost-writer watch ~/Supernote/

# Custom intervals and output
ghost-writer watch ~/Supernote/ --interval 30 --format pdf --output auto_processed/

# Watch with specific file types
ghost-writer watch ~/Supernote/ --format all
```

### Cloud Sync ✅ WORKING

```bash
# Sync recent notes from cloud
ghost-writer sync --since 2025-01-01

# Sync to custom directory and process automatically  
ghost-writer sync --output ~/Documents/supernote/ 

# Quick sync of latest files
ghost-writer sync

# Test your cloud connection
python test_supernote_api.py
```

## Output Formats

### Markdown (.md)
```markdown
# Processed Note: meeting_notes.note

**Source**: /path/to/meeting_notes.note
**OCR Provider**: gpt4_vision  
**Confidence**: 92%
**Processing Cost**: $0.01

## Raw Text
```
Action items from meeting:
- Review Q1 budget proposal
- Schedule team retrospective
- Update project timeline
```

## Structured Content
**Structure Type**: hierarchical_outline
**Confidence**: 87%

1. Action Items
   - Review Q1 budget proposal
   - Schedule team retrospective  
   - Update project timeline
```

### PDF (.pdf)
Professional PDF output with:
- Source metadata and processing info
- Original handwritten text
- Structured, organized content
- Proper formatting and typography

### JSON (.json)
Complete processing data including:
- OCR results and confidence scores
- Detected relationships between elements
- Concept clusters and themes
- Generated document structures
- Processing metadata and costs

## Advanced Features

### Custom Processing Scripts

Create your own processing workflows:

```python
from pathlib import Path
from src.utils.supernote_parser import SupernoteParser, convert_note_to_images
from src.utils.ocr_providers import HybridOCR

def process_supernote_folder(folder_path: Path):
    """Custom processing script for Supernote files"""
    
    ocr = HybridOCR()
    
    for note_file in folder_path.glob("*.note"):
        print(f"Processing {note_file.name}...")
        
        # Convert to images
        images = convert_note_to_images(note_file, folder_path / "temp")
        
        # Process each page
        for image_path in images:
            result = ocr.extract_text(str(image_path))
            
            # Save results
            output_file = folder_path / f"{note_file.stem}_{image_path.stem}.md"
            with open(output_file, 'w') as f:
                f.write(f"# {note_file.name}\n\n{result.text}")
        
        print(f"✅ Completed {note_file.name}")

# Usage
process_supernote_folder(Path("~/Supernote/Notes"))
```

### Integration with Other Tools

#### Obsidian Integration
```bash
# Process notes directly to Obsidian vault
ghost-writer process ~/Supernote/ --output ~/ObsidianVault/Imported/ --format markdown
```

#### Notion Integration (Future)
```bash
# Sync processed notes to Notion
ghost-writer process notes.note --export notion --database "Meeting Notes"
```

## Troubleshooting

### Common Issues

**1. .note file not recognized**
```bash
# Check file format
file my_notes.note

# Force processing with debug info
ghost-writer process my_notes.note --debug
```

**2. OCR quality issues**
```bash
# Try premium OCR providers
ghost-writer process notes.note --quality premium

# Use local-only for debugging
ghost-writer process notes.note --local-only --debug
```

**3. File watching not working**
```bash
# Check permissions
ls -la ~/Supernote/

# Test with manual polling
ghost-writer watch ~/Supernote/ --interval 5 --debug
```

**4. Empty or corrupted .note files**
```bash
# Check file size and contents
ls -la *.note
hexdump -C suspicious.note | head

# Try fallback processing
ghost-writer process --force suspicious.note
```

### Debug Mode

Enable detailed logging:

```bash
# Enable debug logging
ghost-writer --debug process notes.note

# Check system status with debug info
ghost-writer --debug status

# View processing pipeline details
export GHOST_WRITER_LOG_LEVEL=DEBUG
ghost-writer process notes.note
```

## Performance Tips

### Optimization Settings

```yaml
# config.yaml optimizations
processing:
  max_retries: 2
  timeout_seconds: 45
  batch_size: 5

# OCR optimization
ocr:
  hybrid:
    quality_mode: "balanced"  # vs "premium" or "fast"
    cost_limit_per_day: 10.00
    prefer_local: true
```

### Batch Processing

```bash
# Process files in parallel (future feature)
ghost-writer process folder/ --parallel 4

# Optimize for speed
ghost-writer process folder/ --quality fast --format markdown

# Optimize for accuracy
ghost-writer process folder/ --quality premium --format all
```

## API Reference

### Python API

```python
from src.utils.supernote_parser import SupernoteParser, convert_note_to_images
from src.utils.file_watcher import FileWatcher
from pathlib import Path

# Parse a .note file
parser = SupernoteParser()
pages = parser.parse_file(Path("notes.note"))

# Convert to images
images = convert_note_to_images(Path("notes.note"), Path("output/"))

# Setup file watcher
def process_new_file(file_path):
    print(f"New file: {file_path}")

watcher = FileWatcher(Path("~/Supernote/"), process_new_file)
watcher.start()
```

## Roadmap

### Short Term (1-2 months)
- ✅ Local .note file processing
- ✅ CLI integration and file watching
- 🚧 Improved .note format support
- 🚧 Better multi-page handling

### Medium Term (3-6 months)
- 📋 Supernote Cloud API integration
- 📋 Real-time sync capabilities
- 📋 Advanced export integrations (Notion, Obsidian)
- 📋 Mobile companion app

### Long Term (6+ months)
- 📋 Multi-device support (reMarkable, etc.)
- 📋 Advanced AI features (summarization, translation)
- 📋 Collaborative note sharing
- 📋 Web interface for note management

## Contributing

We welcome contributions to improve Supernote integration:

1. **Test with real .note files** - Help us improve format support
2. **API research** - Assist with Supernote Cloud API reverse engineering
3. **Feature requests** - Tell us what workflows you need
4. **Bug reports** - Report issues with specific device models

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/adambalm/ghost-writer/issues)
- **Discussions**: [Community support and ideas](https://github.com/adambalm/ghost-writer/discussions)
- **Documentation**: [Complete documentation](../README.md)

## License

This integration is part of Ghost Writer and is released under the MIT License. See [LICENSE](../LICENSE) for details.