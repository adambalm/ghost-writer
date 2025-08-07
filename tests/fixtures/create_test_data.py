#!/usr/bin/env python3
"""
Generate test data for Ghost Writer testing
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_test_images():
    """Create test images with known text content"""
    fixtures_dir = Path(__file__).parent
    images_dir = fixtures_dir / "sample_images"
    images_dir.mkdir(exist_ok=True)
    
    test_texts = [
        "This is a sample handwritten note for testing OCR functionality.",
        "Ghost Writer processes handwritten notes into digital text.",
        "Machine learning models help analyze writing patterns and style.",
        "The quick brown fox jumps over the lazy dog.",
        "Testing various text lengths and complexity levels."
    ]
    
    created_files = []
    
    for i, text in enumerate(test_texts):
        # Create image with text
        img = Image.new('RGB', (600, 150), color='white')
        
        try:
            # Try to use a font (may not be available on all systems)
            draw = ImageDraw.Draw(img)
            draw.text((10, 50), text, fill='black')
        except:
            # Fallback: just create a white image with filename indicating content
            pass
        
        # Save image
        filename = f"sample_{i+1}.png"
        filepath = images_dir / filename
        img.save(filepath)
        
        created_files.append({
            "filename": filename,
            "text": text,
            "path": str(filepath),
            "expected_words": len(text.split()),
            "expected_chars": len(text)
        })
    
    # Create a ground truth file
    ground_truth_file = images_dir / "ground_truth.json"
    with open(ground_truth_file, 'w') as f:
        json.dump(created_files, f, indent=2)
    
    print(f"Created {len(created_files)} test images in {images_dir}")
    return created_files

def create_style_corpus():
    """Create style corpus samples"""
    fixtures_dir = Path(__file__).parent  
    style_dir = fixtures_dir / "style_samples"
    style_dir.mkdir(exist_ok=True)
    
    style_samples = [
        """I've been thinking about the intersection of technology and creativity lately. 
        There's something fascinating about how tools can amplify human expression rather than replace it.
        The key is finding that sweet spot where the technology serves the creative process.""",
        
        """Today's observation: when we try to automate creativity, we often miss the point entirely.
        The value isn't in the output alone, but in the process of creation itself.
        Maybe the goal should be to enhance the journey, not just optimize the destination.""",
        
        """Notes on writing: The best ideas often come when I'm not actively searching for them.
        Walking, showering, or just letting the mind wander seems to unlock thoughts that
        focused effort can't reach. There's a lesson about productivity in there somewhere.""",
        
        """Reflection: Every tool we create shapes how we think. The pencil changed writing,
        the computer changed thinking, and now AI is changing problem-solving.
        The question isn't whether these changes are good or bad, but how we adapt to them.""",
        
        """Random thought: The most powerful systems are often the simplest ones.
        Complex problems don't always need complex solutions. Sometimes the elegant approach
        is the one that removes complexity rather than adding it."""
    ]
    
    created_samples = []
    for i, sample in enumerate(style_samples):
        filename = f"style_sample_{i+1}.txt"
        filepath = style_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(sample)
        
        created_samples.append({
            "filename": filename,
            "path": str(filepath),
            "word_count": len(sample.split()),
            "char_count": len(sample)
        })
    
    # Create metadata file
    metadata_file = style_dir / "corpus_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(created_samples, f, indent=2)
    
    print(f"Created {len(created_samples)} style samples in {style_dir}")
    return created_samples

def create_test_data_json():
    """Create structured test data file"""
    fixtures_dir = Path(__file__).parent
    
    test_data = {
        "sample_notes": [
            {
                "note_id": "test_note_1",
                "source_file": "sample_1.png",
                "raw_text": "This is a sample handwritten note for testing OCR functionality.",
                "clean_text": "This is a sample handwritten note for testing OCR functionality.",
                "ocr_provider": "tesseract",
                "ocr_confidence": 0.85,
                "processing_cost": 0.0,
                "expected_keywords": ["sample", "handwritten", "note", "testing", "OCR"]
            },
            {
                "note_id": "test_note_2", 
                "source_file": "sample_2.png",
                "raw_text": "Ghost Writer processes handwritten notes into digital text.",
                "clean_text": "Ghost Writer processes handwritten notes into digital text.",
                "ocr_provider": "cloud_vision",
                "ocr_confidence": 0.92,
                "processing_cost": 0.0015,
                "expected_keywords": ["Ghost", "Writer", "processes", "handwritten", "digital"]
            },
            {
                "note_id": "test_note_3",
                "source_file": "sample_3.png", 
                "raw_text": "Machine learning models help analyze writing patterns and style.",
                "clean_text": "Machine learning models help analyze writing patterns and style.",
                "ocr_provider": "hybrid",
                "ocr_confidence": 0.88,
                "processing_cost": 0.0,
                "expected_keywords": ["machine", "learning", "analyze", "writing", "patterns"]
            }
        ],
        "test_expansions": [
            {
                "note_id": "test_note_1",
                "prompt": "Expand this into a blog post about OCR testing",
                "expected_themes": ["OCR", "testing", "automation", "handwriting"],
                "min_length": 200,
                "max_length": 1000
            }
        ],
        "test_searches": [
            {
                "query": "handwritten notes",
                "expected_results": ["test_note_1", "test_note_2"],
                "min_similarity": 0.7
            },
            {
                "query": "machine learning",
                "expected_results": ["test_note_3"],
                "min_similarity": 0.8
            }
        ],
        "performance_benchmarks": {
            "ocr_processing": {"max_duration": 30.0, "unit": "seconds"},
            "database_insert": {"max_duration": 0.1, "unit": "seconds"},
            "search_query": {"max_duration": 0.5, "unit": "seconds"},
            "embedding_generation": {"max_duration": 2.0, "unit": "seconds"}
        },
        "error_scenarios": [
            {
                "scenario": "corrupted_image",
                "input": "corrupted_file.png",
                "expected_error": "InvalidImageError"
            },
            {
                "scenario": "network_failure", 
                "provider": "cloud_vision",
                "expected_fallback": "tesseract"
            },
            {
                "scenario": "budget_exceeded",
                "daily_cost": 10.0,
                "budget_limit": 5.0,
                "expected_behavior": "fallback_to_tesseract"
            }
        ]
    }
    
    test_data_file = fixtures_dir / "test_data.json"
    with open(test_data_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Created test data file: {test_data_file}")
    return test_data

if __name__ == "__main__":
    print("Creating Ghost Writer test data...")
    
    # Create all test data
    images = create_test_images()
    styles = create_style_corpus()  
    test_data = create_test_data_json()
    
    print("\n=== Test Data Summary ===")
    print(f"Test Images: {len(images)} created")
    print(f"Style Samples: {len(styles)} created") 
    print(f"Structured Test Data: Created with {len(test_data['sample_notes'])} sample notes")
    print("\nTest data generation complete!")
    print("\nTo use in tests:")
    print("  - Images: tests/fixtures/sample_images/")
    print("  - Styles: tests/fixtures/style_samples/")
    print("  - Data: tests/fixtures/test_data.json")