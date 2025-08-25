# Ghost Writer Usage Guide

## Quick Start

### Web Interface (Recommended)

1. Start the web server:
   ```bash
   source .venv/bin/activate
   python run_enhanced_viewer.py
   ```

2. Open your browser to: http://localhost:5001

3. Login with your Supernote Cloud credentials:
   - **US Phone Numbers**: Enter digits only (e.g., 4139491742)
   - **International**: Include country code without + (e.g., 861234567890)
   - **Email**: Enter your full email address
   - **Password**: Your Supernote Cloud password

4. Select notes to process and click "Process Selected"

### Command Line Testing

Test your authentication:
```bash
source .venv/bin/activate
python verify_auth.py
```

### CLI Usage

Process local files:
```bash
source .venv/bin/activate
python -m src.cli process path/to/note.png --format markdown
```

## Project Structure

```
ghost-writer/
├── src/                    # Core application code
│   ├── cli.py             # Command-line interface
│   └── utils/             # Utility modules
│       ├── supernote_api.py           # Supernote Cloud API
│       ├── supernote_parser_enhanced.py # Enhanced decoder
│       ├── ocr_providers.py           # OCR processing
│       ├── concept_clustering.py      # Document analysis
│       └── structure_generator.py     # Output generation
├── tests/                  # Test suite
├── config/                 # Configuration files
├── templates/              # Web interface templates
├── archive/                # Old/experimental code (archived)
├── enhanced_web_viewer.py  # Web interface backend
├── run_enhanced_viewer.py  # Web interface launcher
└── verify_auth.py         # Authentication test script
```

## Features

- **Supernote Cloud Integration**: Direct login and file retrieval
- **Enhanced Decoder**: 55x improvement in image quality
- **Hybrid OCR**: Tesseract + Google Vision + GPT-4 Vision
- **Document Processing**: Structure generation and concept clustering
- **Privacy-First**: Local processing with optional cloud features

## Troubleshooting

### Login Issues

1. Verify credentials with `verify_auth.py`
2. For phone numbers, use digits only (no spaces, dashes, or parentheses)
3. Check your internet connection
4. Ensure you're using your Supernote Cloud password (not device PIN)

### Web Interface Issues

1. Check the server is running on port 5001
2. Try clearing browser cache
3. Check console for error messages
4. Restart the server if needed

### Processing Issues

1. Ensure virtual environment is activated
2. Check all dependencies are installed: `pip install -r requirements.txt`
3. Review logs in terminal for specific errors

## Configuration

Edit `config/config.yaml` to customize:
- OCR provider settings
- Processing quality modes
- Cost limits for cloud services
- Output formats and paths