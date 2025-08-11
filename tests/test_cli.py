"""
Tests for Ghost Writer CLI functionality
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.cli import cli, process_single_file
from src.utils.ocr_providers import OCRResult


class TestCLI:
    """Test CLI commands and functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Ghost Writer" in result.output
        assert "Transform handwritten notes" in result.output
    
    def test_init_command(self):
        """Test init command"""
        with patch('src.cli.DatabaseManager') as mock_db:
            with patch('src.cli.HybridOCR') as mock_ocr:
                mock_db.return_value = Mock()
                mock_ocr.return_value = Mock(providers={'tesseract': Mock()})
                
                result = self.runner.invoke(cli, ['init'])
                assert result.exit_code == 0
                assert "initialized successfully" in result.output
    
    def test_status_command(self):
        """Test status command"""
        with patch('src.cli.DatabaseManager') as mock_db:
            with patch('src.cli.HybridOCR') as mock_ocr:
                mock_db.return_value = Mock()
                mock_db.return_value.get_all_notes.return_value = []
                mock_ocr.return_value = Mock(providers={'tesseract': Mock()})
                
                result = self.runner.invoke(cli, ['status'])
                assert result.exit_code == 0
                assert "System Status" in result.output
    
    @patch('src.cli.HybridOCR')
    @patch('src.cli.DatabaseManager')
    @patch('src.cli.RelationshipDetector')
    @patch('src.cli.ConceptExtractor')
    @patch('src.cli.ConceptClusterer')
    @patch('src.cli.StructureGenerator')
    def test_process_image_file(self, mock_struct, mock_cluster, mock_extract, 
                               mock_relation, mock_db, mock_ocr):
        """Test processing an image file"""
        
        # Create test image file
        test_image = self.temp_dir / "test.png"
        test_image.touch()
        
        # Setup mocks
        mock_ocr_result = OCRResult(
            text="Test handwritten text",
            confidence=0.85,
            provider="tesseract",
            processing_time=2.0,
            cost=0.0
        )
        mock_ocr.return_value.extract_text.return_value = mock_ocr_result
        mock_db.return_value.store_note.return_value = "note_123"
        
        # Mock the processing pipeline
        mock_relation.return_value.detect_relationships.return_value = []
        mock_extract.return_value.extract_concepts.return_value = []
        mock_cluster.return_value.cluster_concepts.return_value = []
        mock_struct.return_value.generate_structures.return_value = []
        
        result = self.runner.invoke(cli, [
            'process', str(test_image), 
            '--output', str(self.temp_dir / "output"),
            '--format', 'markdown'
        ])
        
        assert result.exit_code == 0
        assert "Processing complete" in result.output
    
    def test_process_unsupported_file(self):
        """Test processing unsupported file type"""
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("Not an image")
        
        result = self.runner.invoke(cli, [
            'process', str(test_file)
        ])
        
        assert result.exit_code == 0
        assert "No supported files found" in result.output
    
    @patch('src.cli.convert_note_to_images')
    @patch('src.cli.HybridOCR')
    @patch('src.cli.DatabaseManager')
    def test_process_note_file(self, mock_db, mock_ocr, mock_convert):
        """Test processing a .note file"""
        
        # Create test .note file
        test_note = self.temp_dir / "test.note"
        test_note.write_bytes(b"NOTE" + b"fake_note_data")
        
        # Setup mocks
        temp_image = self.temp_dir / "temp.png"
        mock_convert.return_value = [temp_image]
        
        mock_ocr_result = OCRResult(
            text="Converted note text",
            confidence=0.90,
            provider="tesseract",
            processing_time=3.0,
            cost=0.0
        )
        mock_ocr.return_value.extract_text.return_value = mock_ocr_result
        mock_db.return_value.store_note.return_value = "note_456"
        
        with patch('src.cli.RelationshipDetector'), \
             patch('src.cli.ConceptExtractor'), \
             patch('src.cli.ConceptClusterer'), \
             patch('src.cli.StructureGenerator'):
            
            result = self.runner.invoke(cli, [
                'process', str(test_note),
                '--format', 'json'
            ])
        
        assert result.exit_code == 0
        mock_convert.assert_called_once()


class TestFileExports:
    """Test file export functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.png"
        self.test_file.touch()
        
        self.mock_ocr_result = OCRResult(
            text="Test handwritten content\nWith multiple lines",
            confidence=0.92,
            provider="gpt4_vision",
            processing_time=2.5,
            cost=0.01
        )
        
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_export_as_markdown(self):
        """Test Markdown export functionality"""
        from src.cli import export_as_markdown
        
        structures = []  # Empty structures for simple test
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        
        result = export_as_markdown(
            self.test_file, structures, output_dir, self.mock_ocr_result
        )
        
        assert result is not None
        assert result.endswith("_processed.md")
        
        # Check file was created
        output_file = output_dir / result
        assert output_file.exists()
        
        # Check content
        content = output_file.read_text()
        assert "Test handwritten content" in content
        assert "gpt4_vision" in content
        assert "92.00%" in content
    
    def test_export_as_json(self):
        """Test JSON export functionality"""
        from src.cli import export_as_json
        
        # Create mock data
        elements = []
        concepts = []
        clusters = []
        relationships = []
        structures = []
        
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        
        result = export_as_json(
            self.test_file, structures, elements, concepts, 
            clusters, relationships, output_dir, self.mock_ocr_result
        )
        
        assert result is not None
        assert result.endswith("_data.json")
        
        # Check file was created
        output_file = output_dir / result
        assert output_file.exists()
        
        # Check JSON structure
        data = json.loads(output_file.read_text())
        assert "source_file" in data
        assert "ocr_result" in data
        assert data["ocr_result"]["provider"] == "gpt4_vision"
    
    def test_export_as_pdf(self):
        """Test PDF export functionality"""
        from src.cli import export_as_pdf
        
        structures = []
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        
        result = export_as_pdf(
            self.test_file, structures, output_dir, self.mock_ocr_result
        )
        
        assert result is not None
        assert result.endswith("_processed.pdf")
        
        # Check file was created
        output_file = output_dir / result
        assert output_file.exists()
        assert output_file.stat().st_size > 0  # PDF should have content


class TestSingleFileProcessing:
    """Test single file processing pipeline"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('src.cli.HybridOCR')
    @patch('src.cli.DatabaseManager') 
    @patch('src.cli.RelationshipDetector')
    @patch('src.cli.ConceptExtractor')
    @patch('src.cli.ConceptClusterer')
    @patch('src.cli.StructureGenerator')
    def test_process_single_file_success(self, mock_struct, mock_cluster, 
                                        mock_extract, mock_relation, mock_db, mock_ocr):
        """Test successful single file processing"""
        
        test_file = self.temp_dir / "test.jpg"
        test_file.touch()
        
        # Setup mocks
        mock_ocr_result = OCRResult(
            text="Sample handwritten text",
            confidence=0.88,
            provider="tesseract",
            processing_time=1.5,
            cost=0.0
        )
        
        mock_ocr.extract_text.return_value = mock_ocr_result
        mock_db.store_note.return_value = "note_789"
        mock_relation.detect_relationships.return_value = []
        mock_extract.extract_concepts.return_value = []
        mock_cluster.cluster_concepts.return_value = []
        mock_struct.generate_structures.return_value = []
        
        result = process_single_file(
            file_path=test_file,
            ocr_provider=mock_ocr,
            relationship_detector=mock_relation,
            concept_extractor=mock_extract,
            concept_clusterer=mock_cluster,
            structure_generator=mock_struct,
            db_manager=mock_db,
            output_dir=self.temp_dir / "output",
            output_format="markdown",
            quality="balanced"
        )
        
        assert result is not None
        assert "processed.md" in result
        
        # Verify all components were called
        mock_ocr.extract_text.assert_called_once()
        mock_db.store_note.assert_called_once()
        mock_relation.detect_relationships.assert_called_once()
    
    @patch('src.cli.HybridOCR')
    def test_process_single_file_no_text(self, mock_ocr):
        """Test processing file with no extractable text"""
        
        test_file = self.temp_dir / "empty.png"
        test_file.touch()
        
        # Mock empty OCR result
        mock_ocr_result = OCRResult(
            text="",
            confidence=0.0,
            provider="tesseract", 
            processing_time=1.0,
            cost=0.0
        )
        mock_ocr.extract_text.return_value = mock_ocr_result
        
        # Create minimal mocks
        mock_db = Mock()
        mock_relation = Mock()
        mock_extract = Mock()
        mock_cluster = Mock()
        mock_struct = Mock()
        
        result = process_single_file(
            file_path=test_file,
            ocr_provider=mock_ocr,
            relationship_detector=mock_relation,
            concept_extractor=mock_extract,
            concept_clusterer=mock_cluster,
            structure_generator=mock_struct,
            db_manager=mock_db,
            output_dir=self.temp_dir / "output",
            output_format="markdown",
            quality="fast"
        )
        
        assert result is None  # Should return None for empty text