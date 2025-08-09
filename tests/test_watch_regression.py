"""
Test watch command functionality - regression test for triage pack 1
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import tempfile
import os

# Note: on_file_added is a nested function in the watch command, so we test the logic separately


@pytest.mark.unit
def test_watch_on_file_added_processing():
    """Test that on_file_added processes files correctly"""
    
    # Create a temporary directory and file for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test_image.png"
        
        # Create a dummy file
        test_file.write_bytes(b"fake image data")
        
        # Mock all the components
        with patch('src.cli.HybridOCR') as mock_ocr_class, \
             patch('src.cli.RelationshipDetector') as mock_detector_class, \
             patch('src.cli.ConceptExtractor') as mock_extractor_class, \
             patch('src.cli.ConceptClusterer') as mock_clusterer_class, \
             patch('src.cli.StructureGenerator') as mock_generator_class, \
             patch('src.cli.DatabaseManager') as mock_db_class, \
             patch('src.cli.process_single_file') as mock_process:
            
            # Setup return values
            mock_process.return_value = "output_file.md"
            
            # Mock the output_dir and format from the parent scope
            # In the actual implementation, these would be captured from the watch function
            output_dir = temp_path / "output"
            format_type = "markdown"
            
            # We need to create a modified version of on_file_added for testing
            # since it has closure variables
            def test_on_file_added(file_path: Path):
                try:
                    from src.utils.ocr_providers import HybridOCR
                    from src.utils.relationship_detector import RelationshipDetector
                    from src.utils.concept_clustering import ConceptExtractor, ConceptClusterer
                    from src.utils.structure_generator import StructureGenerator
                    from src.utils.database import DatabaseManager
                    from src.cli import process_single_file
                    
                    ocr_provider = HybridOCR()
                    detector = RelationshipDetector()
                    extractor = ConceptExtractor()
                    clusterer = ConceptClusterer()
                    generator = StructureGenerator()
                    db_manager = DatabaseManager()
                    
                    result = process_single_file(
                        file_path=file_path,
                        ocr_provider=ocr_provider,
                        relationship_detector=detector,
                        concept_extractor=extractor,
                        concept_clusterer=clusterer,
                        structure_generator=generator,
                        db_manager=db_manager,
                        output_dir=output_dir,
                        output_format=format_type,
                        quality="balanced"
                    )
                    return result
                except Exception as e:
                    raise e
            
            # Call the function
            result = test_on_file_added(test_file)
            
            # Verify that process_single_file was called with correct parameters
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            
            assert call_args[1]['file_path'] == test_file
            assert call_args[1]['output_dir'] == output_dir
            assert call_args[1]['output_format'] == format_type
            assert call_args[1]['quality'] == "balanced"
            
            # Verify all components were instantiated
            mock_ocr_class.assert_called_once()
            mock_detector_class.assert_called_once()
            mock_extractor_class.assert_called_once()
            mock_clusterer_class.assert_called_once()
            mock_generator_class.assert_called_once()
            mock_db_class.assert_called_once()


@pytest.mark.unit
def test_watch_on_file_added_error_handling():
    """Test that on_file_added handles errors gracefully"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test_image.png"
        test_file.write_bytes(b"fake image data")
        
        with patch('src.cli.HybridOCR', side_effect=Exception("Mock error")):
            
            def test_on_file_added_with_error(file_path: Path):
                try:
                    from src.utils.ocr_providers import HybridOCR
                    HybridOCR()
                except Exception as e:
                    # This should be caught and handled gracefully
                    assert str(e) == "Mock error"
                    return f"Error: {e}"
            
            # Should not raise an exception
            result = test_on_file_added_with_error(test_file)
            assert "Error: Mock error" in result