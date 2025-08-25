#!/usr/bin/env python3
"""Test script to verify the fixed Supernote parsers work correctly"""

import sys
from pathlib import Path
from src.utils.supernote_parser import SupernoteParser
from src.utils.supernote_parser_enhanced import SupernoteParser as EnhancedParser

def test_parser_with_file(parser_class, name, file_path):
    """Test a parser with a given file"""
    print(f"\nTesting {name} with {file_path.name}:")
    try:
        parser = parser_class()
        pages = parser.parse_file(file_path)
        print(f"  ✓ Parsed successfully: {len(pages)} page(s) found")
        
        for i, page in enumerate(pages, 1):
            metadata = page.metadata or {}
            has_content = metadata.get('has_content', False)
            parser_type = metadata.get('parser', 'unknown')
            print(f"    Page {i}: {page.width}x{page.height}, has_content={has_content}, parser={parser_type}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    # Find test .note files
    test_files = []
    for pattern in ["*.note", "**/*.note"]:
        test_files.extend(Path(".").glob(pattern))
    
    if not test_files:
        print("No .note files found for testing")
        return 1
    
    print(f"Found {len(test_files)} .note file(s) to test")
    
    # Test each file with both parsers
    results = []
    for note_file in test_files[:3]:  # Test up to 3 files
        results.append(test_parser_with_file(SupernoteParser, "Basic Parser", note_file))
        results.append(test_parser_with_file(EnhancedParser, "Enhanced Parser", note_file))
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✓ All tests passed! Parsers are working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())