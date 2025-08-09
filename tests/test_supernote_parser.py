"""
Tests for Supernote .note file parser
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.utils.supernote_parser import (
    SupernoteParser, SupernotePage, SupernoteStroke,
    convert_note_to_images, is_supernote_file
)


class TestSupernoteParser:
    """Test Supernote file parsing functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.parser = SupernoteParser()
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_parser_initialization(self):
        """Test parser initializes correctly"""
        assert self.parser.pages == []
        assert self.parser.metadata == {}
        assert self.parser.version == 0
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises error"""
        nonexistent = self.temp_dir / "missing.note"
        
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file(nonexistent)
    
    def test_parse_non_note_file(self):
        """Test parsing non-.note file raises error"""
        text_file = self.temp_dir / "test.txt"
        text_file.write_text("not a note file")
        
        with pytest.raises(ValueError, match="Not a .note file"):
            self.parser.parse_file(text_file)
    
    def test_parse_empty_note_file(self):
        """Test parsing empty .note file"""
        empty_note = self.temp_dir / "empty.note"
        empty_note.write_bytes(b"")
        
        # Should use fallback parser
        pages = self.parser.parse_file(empty_note)
        assert len(pages) == 1  # Fallback creates one page
        assert pages[0].page_id == 0
        assert pages[0].strokes == []
    
    def test_parse_fake_note_file_with_magic(self):
        """Test parsing file with NOTE magic signature"""
        fake_note = self.temp_dir / "fake.note"
        fake_note.write_bytes(b"NOTEv2.0" + b"fake_data" * 100)
        
        pages = self.parser.parse_file(fake_note)
        assert len(pages) >= 1
        # Should detect version 2
        assert self.parser.version == 2
    
    def test_parse_fallback_format(self):
        """Test fallback parsing for unknown format"""
        unknown_note = self.temp_dir / "unknown.note"
        unknown_note.write_bytes(b"UNKNOWN_FORMAT" + b"data" * 50)
        
        pages = self.parser.parse_file(unknown_note)
        assert len(pages) == 1
        
        page = pages[0]
        assert page.width == 1872  # Standard Supernote dimensions
        assert page.height == 1404
        assert page.metadata["parser"] == "fallback"
        assert page.metadata["has_content"] is True
    
    def test_render_empty_page(self):
        """Test rendering page with no strokes"""
        page = SupernotePage(
            page_id=0,
            width=1000,
            height=800,
            strokes=[]
        )
        
        image = self.parser.render_page_to_image(page)
        assert image.size == (1000, 800)
        assert image.mode == "RGB"
    
    def test_render_page_with_strokes(self):
        """Test rendering page with sample strokes"""
        # Create sample stroke
        stroke = SupernoteStroke(
            points=[(100, 100), (200, 150), (300, 200)],
            pressure=[0.5, 0.8, 0.6],
            timestamp=1234567890,
            pen_type=1,
            color=0,
            thickness=2.0
        )
        
        page = SupernotePage(
            page_id=1,
            width=800,
            height=600,
            strokes=[stroke]
        )
        
        image = self.parser.render_page_to_image(page, scale=1.0)
        assert image.size == (800, 600)
        
        # Test with scaling
        scaled_image = self.parser.render_page_to_image(page, scale=2.0)
        assert scaled_image.size == (1600, 1200)
    
    def test_render_page_to_file(self):
        """Test rendering page and saving to file"""
        page = SupernotePage(
            page_id=0,
            width=400,
            height=300,
            strokes=[]
        )
        
        output_file = self.temp_dir / "rendered.png"
        image = self.parser.render_page_to_image(page, output_file)
        
        assert output_file.exists()
        assert image.size == (400, 300)
    
    def test_extract_text_regions_empty_page(self):
        """Test extracting text regions from empty page"""
        page = SupernotePage(
            page_id=0,
            width=800,
            height=600,
            strokes=[]
        )
        
        regions = self.parser.extract_text_regions(page)
        assert regions == []
    
    def test_extract_text_regions_with_strokes(self):
        """Test extracting text regions from page with strokes"""
        strokes = [
            SupernoteStroke(
                points=[(50, 100), (150, 120)],
                pressure=[0.5, 0.6],
                timestamp=1234567890,
                pen_type=1,
                color=0,
                thickness=1.0
            ),
            SupernoteStroke(
                points=[(200, 150), (300, 170)],
                pressure=[0.7, 0.8],
                timestamp=1234567891,
                pen_type=1,
                color=0,
                thickness=1.0
            )
        ]
        
        page = SupernotePage(
            page_id=0,
            width=800,
            height=600,
            strokes=strokes
        )
        
        regions = self.parser.extract_text_regions(page)
        assert len(regions) > 0
        
        # Each region should be a tuple of (x1, y1, x2, y2)
        for region in regions:
            assert len(region) == 4
            x1, y1, x2, y2 = region
            assert x1 < x2
            assert y1 < y2
    
    def test_merge_overlapping_boxes(self):
        """Test merging overlapping bounding boxes"""
        boxes = [
            (10, 10, 100, 50),   # Box 1
            (90, 30, 180, 70),   # Box 2 (overlaps with Box 1)
            (200, 100, 300, 150) # Box 3 (separate)
        ]
        
        merged = self.parser._merge_overlapping_boxes(boxes)
        
        # Should merge first two boxes, keep third separate
        assert len(merged) == 2
        
        # Check merged box contains both original boxes
        merged_box = next(box for box in merged if box[0] <= 10)
        assert merged_box[0] <= 10  # Contains Box 1 left edge
        assert merged_box[2] >= 180 # Contains Box 2 right edge
    
    def test_merge_empty_boxes(self):
        """Test merging empty list of boxes"""
        result = self.parser._merge_overlapping_boxes([])
        assert result == []


class TestSupernoteUtilities:
    """Test Supernote utility functions"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_is_supernote_file_valid(self):
        """Test detecting valid Supernote file"""
        note_file = self.temp_dir / "test.note"
        note_file.write_bytes(b"NOTE" + b"v1.0" + b"data" * 20)
        
        assert is_supernote_file(note_file) is True
    
    def test_is_supernote_file_wrong_extension(self):
        """Test detecting file with wrong extension"""
        text_file = self.temp_dir / "test.txt"
        text_file.write_bytes(b"NOTE" + b"v1.0" + b"data" * 20)
        
        assert is_supernote_file(text_file) is False
    
    def test_is_supernote_file_no_magic(self):
        """Test detecting .note file without magic signature"""
        fake_note = self.temp_dir / "fake.note"
        fake_note.write_bytes(b"random_data" * 10)
        
        # Should still return True for .note files even without magic
        # (for compatibility with various formats)
        result = is_supernote_file(fake_note)
        assert result is False  # No recognizable signature
    
    def test_is_supernote_file_nonexistent(self):
        """Test detecting nonexistent file"""
        nonexistent = self.temp_dir / "missing.note"
        assert is_supernote_file(nonexistent) is False
    
    @patch('src.utils.supernote_parser.SupernoteParser')
    def test_convert_note_to_images(self, mock_parser_class):
        """Test converting .note file to images"""
        # Create test files
        note_file = self.temp_dir / "test.note"
        note_file.write_bytes(b"NOTE" + b"fake_data" * 100)
        
        output_dir = self.temp_dir / "output"
        
        # Mock parser
        mock_parser = Mock()
        mock_page = Mock()
        mock_page.page_id = 0
        mock_parser.parse_file.return_value = [mock_page]
        mock_parser.render_page_to_image.return_value = Mock()
        mock_parser_class.return_value = mock_parser
        
        result = convert_note_to_images(note_file, output_dir)
        
        assert len(result) == 1
        assert output_dir.exists()
        
        # Verify parser was called correctly
        mock_parser.parse_file.assert_called_once_with(note_file)
        mock_parser.render_page_to_image.assert_called_once()
    
    @patch('src.utils.supernote_parser.SupernoteParser')
    def test_convert_note_to_images_no_pages(self, mock_parser_class):
        """Test converting .note file with no pages"""
        note_file = self.temp_dir / "empty.note"
        note_file.write_bytes(b"")
        
        output_dir = self.temp_dir / "output"
        
        # Mock parser returning no pages
        mock_parser = Mock()
        mock_parser.parse_file.return_value = []
        mock_parser_class.return_value = mock_parser
        
        result = convert_note_to_images(note_file, output_dir)
        
        assert result == []
    
    @patch('src.utils.supernote_parser.SupernoteParser')
    def test_convert_note_to_images_parser_error(self, mock_parser_class):
        """Test converting .note file when parser fails"""
        note_file = self.temp_dir / "corrupt.note"
        note_file.write_bytes(b"CORRUPT_DATA")
        
        output_dir = self.temp_dir / "output"
        
        # Mock parser raising exception
        mock_parser = Mock()
        mock_parser.parse_file.side_effect = Exception("Parser failed")
        mock_parser_class.return_value = mock_parser
        
        result = convert_note_to_images(note_file, output_dir)
        
        assert result == []