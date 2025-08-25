#!/bin/bash
# Simple web viewer runner that properly activates virtual environment

echo "Simple Web Viewer for Enhanced Decoder"
echo "======================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found at .venv/"
    echo "Please create virtual environment first"
    exit 1
fi

# Activate virtual environment and run web viewer
echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting web viewer at http://localhost:5002"
echo "Press Ctrl+C to stop"
python3 simple_test_viewer.py