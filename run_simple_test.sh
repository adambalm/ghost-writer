#!/bin/bash
# Simple test runner that properly activates virtual environment

echo "Enhanced Clean Room Decoder Test"
echo "==============================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found at .venv/"
    echo "Please create virtual environment first"
    exit 1
fi

# Activate virtual environment and run test
echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running enhanced decoder test..."
python3 test_enhanced_decoder_simple.py

echo "Test complete"