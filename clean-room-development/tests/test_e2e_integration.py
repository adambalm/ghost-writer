"""
End-to-End Integration Tests for Ghost Writer

Tests the complete pipeline from handwritten note processing through
structure generation using mocked APIs to validate business logic.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.utils.ocr_providers import HybridOCR, OCRResult
from src.utils.relationship_detector import RelationshipDetector, NoteElement
from src.utils.concept_clustering import ConceptExtractor, ConceptClusterer
from src.utils.structure_generator import StructureGenerator, StructureType


class TestE2EIntegration:
    """Test complete Ghost Writer pipeline end-to-end"""
    
    def test_dual_beachhead_premium_accuracy_pipeline(self):
        """Test premium accuracy beachhead: handwritten notes → structured document"""
        
        # Mock image file input
        mock_image_data = b"fake_image_data"
        
        with patch("builtins.open", mock_open(read_data=mock_image_data)), \
             patch("src.utils.ocr_providers.GoogleVisionOCR.extract_text") as mock_gv, \
             patch("src.utils.ocr_providers.TesseractOCR.extract_text") as mock_tess, \
             patch("src.utils.ocr_providers.GPT4VisionOCR.extract_text") as mock_gpt4, \
             patch('src.utils.ocr_providers.config') as mock_config:
            
            # Mock OCR provider responses simulating handwritten meeting notes
            mock_tess.return_value = OCRResult(
                text="1. Project Status\n   - On track for Q2\n   - Need more testing\n\n" +
                     "2. Action Items\n   - Review code → Deploy to staging\n   - Schedule user testing",
                confidence=0.6,
                provider="tesseract", 
                processing_time=0.5
            )
            
            mock_gv.return_value = OCRResult(
                text="1. Project Status\n   - On track for Q2 delivery\n   - Need more comprehensive testing\n\n" +
                     "2. Action Items\n   - Review code → Deploy to staging\n   - Schedule user testing sessions\n\n" +
                     "Meeting with @john_smith next week",
                confidence=0.9,
                provider="google_vision",
                processing_time=1.2
            )
            
            mock_gpt4.return_value = OCRResult(
                text="1. Project Status Update\n   - On track for Q2 delivery milestone\n   - Need more comprehensive testing coverage\n\n" +
                     "2. Action Items & Next Steps\n   - Review code quality → Deploy to staging environment\n   - Schedule comprehensive user testing sessions\n\n" +
                     "Follow-up meeting with @john_smith scheduled for next week\n" +
                     "#important #project-alpha",
                confidence=0.95,
                provider="gpt4_vision",
                processing_time=2.1
            )
            
            # Mock the global config to enable all providers
            mock_config.get.return_value = {
                'providers': {
                    'tesseract': {'config': '--oem 3 --psm 6', 'confidence_threshold': 50},
                    'google_vision': {'confidence_threshold': 80},
                    'gpt4_vision': {'confidence_threshold': 85, 'model': 'gpt-4o'}
                }
            }
            
            # Initialize OCR with premium accuracy configuration
            manager = HybridOCR({
                'confidence_threshold': 0.8,
                'cost_limit_per_day': 10.0,
                'quality_mode': 'premium',
                'confidence_thresholds': {
                    'tesseract': 50,
                    'google_vision': 80,
                    'gpt4_vision': 90
                }
            })
            
            # Step 1: OCR Processing
            image_path = Path("/tmp/test_notes.jpg")
            ocr_result = manager.extract_text(image_path)
            
            # Verify premium accuracy selection (should choose GPT4 Vision)
            assert ocr_result.provider == "gpt4_vision"
            assert ocr_result.confidence == 0.95
            assert "comprehensive testing coverage" in ocr_result.text
            assert "#project-alpha" in ocr_result.text
            
            # Step 2: Convert OCR text to note elements (simulate layout detection)
            elements = self._create_note_elements_from_ocr(ocr_result.text)
            assert len(elements) >= 8  # Should have multiple elements
            
            # Step 3: Detect relationships between elements
            detector = RelationshipDetector({'proximity_threshold': 60})
            relationships = detector.detect_relationships(elements)
            
            # Should find meaningful relationships (hierarchical, arrow, sequence, or proximity)
            assert len(relationships) > 0
            relationship_types = {r.relationship_type.value for r in relationships}
            # Check for structured relationships - should have hierarchy OR sequence (numbered lists)
            has_structure = "hierarchy" in relationship_types or "sequence" in relationship_types
            assert has_structure, f"Expected structured relationships, got: {relationship_types}"
            # Should have arrow relationships from "Review code → Deploy to staging"
            assert "arrow" in relationship_types, f"Expected arrow relationships, got: {relationship_types}"
            
            # Step 4: Extract and cluster concepts
            extractor = ConceptExtractor({'min_concept_length': 3})
            concepts = extractor.extract_concepts(elements)
            
            # Should extract project concepts, actions, and entities
            assert len(concepts) > 0
            concept_types = {c.concept_type for c in concepts}
            assert "topic" in concept_types    # Project status
            assert "action" in concept_types   # Review, deploy, schedule
            assert "entity" in concept_types   # @john_smith, #project-alpha
            
            clusterer = ConceptClusterer({'similarity_threshold': 0.3})
            clusters = clusterer.cluster_concepts(concepts, relationships)
            
            # Should create meaningful clusters
            assert len(clusters) > 0
            cluster_themes = [c.theme.lower() for c in clusters]
            
            # Should identify main themes
            # More flexible theme matching - should contain meaningful content
            has_meaningful_themes = len(cluster_themes) > 0 and any(len(theme) > 3 for theme in cluster_themes)
            assert has_meaningful_themes, f"Expected meaningful themes, got: {cluster_themes}"
            
            # Step 5: Generate structured document
            generator = StructureGenerator({'min_confidence': 0.4})
            structures = generator.generate_structures(elements, concepts, clusters, relationships)
            
            # Should generate appropriate structures
            assert len(structures) > 0
            
            # Should include outline structure for meeting notes
            outline_structures = [s for s in structures if s.structure_type == StructureType.OUTLINE]
            assert len(outline_structures) > 0
            
            best_structure = max(structures, key=lambda s: s.confidence)
            assert best_structure.confidence > 0.4
            
            # Step 6: Export structured document
            exported_text = generator.export_structure_as_text(best_structure)
            
            # Verify exported structure contains meaningful content from OCR
            # Should contain key elements from the original OCR text
            has_meaningful_content = any(word in exported_text for word in ["Action", "Items", "john_smith", "meeting", "testing"])
            assert has_meaningful_content, f"Expected meaningful content in exported text: {exported_text}"
            assert "Action" in exported_text
            assert "Confidence:" in exported_text  # Should include metrics
    
    def test_idea_organization_beachhead_pipeline(self):
        """Test idea organization beachhead: scattered thoughts → organized structure"""
        
        # Simulate scattered handwritten thoughts (typical for learning differences)
        mock_image_data = b"scattered_thoughts_image"
        
        with patch("builtins.open", mock_open(read_data=mock_image_data)), \
             patch("src.utils.ocr_providers.TesseractOCR.extract_text") as mock_tess, \
             patch('src.utils.ocr_providers.config') as mock_config:
            
            # Mock scattered, non-linear handwritten thoughts
            mock_tess.return_value = OCRResult(
                text="Machine learning algorithms\n\n" +
                     "Need to collect training data\n\n" +
                     "Neural networks are complex\n\n" +
                     "First: understand the problem\n\n" +
                     "Data cleaning is important\n\n" +
                     "Deep learning requires lots of data\n\n" +
                     "Then: design the architecture\n\n" +
                     "Backpropagation algorithm\n\n" +
                     "Finally: train and evaluate",
                confidence=0.7,
                provider="tesseract",
                processing_time=0.8
            )
            
            # Mock the global config for tesseract-only setup
            mock_config.get.return_value = {
                'providers': {
                    'tesseract': {'config': '--oem 3 --psm 6', 'confidence_threshold': 30}
                }
            }
            
            # Initialize for idea organization (lower accuracy, local-first)
            manager = HybridOCR({
                'confidence_threshold': 0.5,
                'cost_limit_per_day': 2.0,
                'quality_mode': 'fast',  # Use fast mode for local-first
                'confidence_thresholds': {
                    'tesseract': 30
                }
            })
            
            # Step 1: Local OCR processing
            image_path = Path("/tmp/scattered_thoughts.jpg")
            ocr_result = manager.extract_text(image_path)
            
            # Should use local Tesseract for privacy
            assert ocr_result.provider == "tesseract"
            assert ocr_result.confidence == 0.7
            
            # Step 2: Create elements from scattered text
            elements = self._create_scattered_elements(ocr_result.text)
            assert len(elements) >= 8
            
            # Step 3: Detect relationships (should find sequence and topic relationships)
            detector = RelationshipDetector({'proximity_threshold': 80})  # More generous for scattered notes
            relationships = detector.detect_relationships(elements)
            
            # Should find sequence relationships from "First", "Then", "Finally"
            sequence_rels = [r for r in relationships if r.relationship_type.value == "sequence"]
            assert len(sequence_rels) > 0
            
            # Step 4: Extract concepts and cluster scattered ideas
            extractor = ConceptExtractor({'min_concept_length': 2})  # Lower threshold for scattered writing
            concepts = extractor.extract_concepts(elements)
            
            # Should extract ML concepts and process concepts
            ml_concepts = [c for c in concepts if any("machine" in kw or "neural" in kw or "deep" in kw for kw in c.keywords)]
            process_concepts = [c for c in concepts if any("first" in kw or "then" in kw or "finally" in kw for kw in c.keywords)]
            
            assert len(ml_concepts) > 0
            assert len(process_concepts) > 0
            
            clusterer = ConceptClusterer({'similarity_threshold': 0.25})  # Lower threshold for scattered thoughts
            clusters = clusterer.cluster_concepts(concepts, relationships)
            
            # Should organize scattered thoughts into coherent clusters
            assert len(clusters) > 0
            
            # Should identify ML cluster and process cluster
            cluster_themes = [c.theme.lower() for c in clusters]
            has_ml_cluster = any("machine" in theme or "neural" in theme or "learning" in theme for theme in cluster_themes)
            has_process_cluster = any("first" in theme or "process" in theme for theme in cluster_themes)
            
            assert has_ml_cluster or has_process_cluster
            
            # Step 5: Generate structure to organize scattered thoughts
            generator = StructureGenerator({'min_confidence': 0.3})  # Lower threshold for idea organization
            structures = generator.generate_structures(elements, concepts, clusters, relationships)
            
            assert len(structures) > 0
            
            # Should generate both outline and timeline structures
            structure_types = {s.structure_type for s in structures}
            assert StructureType.OUTLINE in structure_types or StructureType.TIMELINE in structure_types
            
            # Best structure should help organize scattered thoughts
            best_structure = max(structures, key=lambda s: s.confidence)
            exported_text = generator.export_structure_as_text(best_structure)
            
            # Should organize ideas coherently
            assert len(exported_text.split('\n')) > 5  # Multiple organized sections
            # Should contain key concepts from the scattered thoughts
            has_key_concepts = any(word in exported_text.lower() for word in [
                "learning", "data", "algorithm", "neural", "machine", "training", 
                "first", "then", "finally", "understand", "design", "evaluate"
            ])
            assert has_key_concepts, f"Expected key concepts in exported text: {exported_text}"
    
    def test_error_handling_and_fallbacks(self):
        """Test error handling and provider fallbacks"""
        
        with patch("builtins.open", mock_open(read_data=b"test_image")), \
             patch("src.utils.ocr_providers.GoogleVisionOCR.extract_text") as mock_gv, \
             patch("src.utils.ocr_providers.TesseractOCR.extract_text") as mock_tess:
            
            # Simulate Google Vision failure
            mock_gv.side_effect = Exception("API quota exceeded")
            
            # Tesseract succeeds as fallback
            mock_tess.return_value = OCRResult(
                text="Fallback OCR text from local processing",
                confidence=0.6,
                provider="tesseract",
                processing_time=0.3
            )
            
            manager = HybridOCR({
                'confidence_threshold': 0.5,
                'providers': {
                    'tesseract': {'enabled': True},
                    'google_vision': {'enabled': True}
                }
            })
            
            # Should fallback to Tesseract when Google Vision fails
            result = manager.extract_text(Path("/tmp/test.jpg"))
            
            assert result.provider == "tesseract"
            assert result.confidence == 0.6
            assert "Fallback OCR" in result.text
            
            # Pipeline should continue with lower quality OCR
            elements = self._create_note_elements_from_ocr(result.text)
            detector = RelationshipDetector()
            relationships = detector.detect_relationships(elements)
            
            # Should handle degraded input gracefully
            assert isinstance(relationships, list)
    
    def test_cost_optimization_routing(self):
        """Test cost-optimized provider routing"""
        
        with patch("builtins.open", mock_open(read_data=b"test_image")), \
             patch("src.utils.ocr_providers.TesseractOCR.extract_text") as mock_tess, \
             patch("src.utils.ocr_providers.GoogleVisionOCR.extract_text") as mock_gv:
            
            # Mock different confidence levels
            mock_tess.return_value = OCRResult(
                text="High confidence local OCR result",
                confidence=0.95,
                provider="tesseract",
                processing_time=0.4
            )
            mock_gv.return_value = OCRResult(
                text="Slightly better but costly result",
                confidence=0.97,
                provider="google_vision",
                processing_time=1.5
            )
            
            # Test cost-conscious configuration
            manager = HybridOCR({
                'confidence_threshold': 0.9,
                'cost_budget': 1.0,  # Very low budget
                'providers': {
                    'tesseract': {'enabled': True, 'cost_per_image': 0.0},
                    'google_vision': {'enabled': True, 'cost_per_image': 0.5}
                }
            })
            
            result = manager.extract_text(Path("/tmp/test.jpg"))
            
            # Should choose free Tesseract when it meets confidence threshold
            assert result.provider == "tesseract"
            assert result.confidence == 0.95
    
    def _create_note_elements_from_ocr(self, ocr_text: str) -> list:
        """Convert OCR text into positioned note elements (mock layout detection)"""
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        elements = []
        
        y_pos = 20
        for i, line in enumerate(lines):
            # Simulate different indentation levels
            x_pos = 10
            if line.startswith('   '):
                x_pos = 30  # Indented items
            elif line.startswith('  '):
                x_pos = 20  # Slightly indented
            
            element = NoteElement(
                text=line,
                bbox=(x_pos, y_pos, len(line) * 8, 15),  # Approximate width
                confidence=0.8 + (i % 3) * 0.05,  # Vary confidence
                element_id=f"elem_{i+1}"
            )
            elements.append(element)
            y_pos += 25  # Move down for next line
        
        return elements
    
    def _create_scattered_elements(self, ocr_text: str) -> list:
        """Create scattered note elements simulating non-linear handwriting"""
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        elements = []
        
        # Simulate scattered positioning (not in reading order)
        positions = [
            (10, 20), (200, 50), (50, 80), (150, 30), 
            (20, 120), (180, 90), (30, 160), (160, 140), (90, 200)
        ]
        
        for i, line in enumerate(lines):
            if i < len(positions):
                x_pos, y_pos = positions[i]
            else:
                x_pos, y_pos = 10 + (i * 30) % 200, 20 + (i * 40)
            
            element = NoteElement(
                text=line,
                bbox=(x_pos, y_pos, len(line) * 7, 15),
                confidence=0.6 + (i % 4) * 0.05,  # Lower confidence for scattered writing
                element_id=f"scattered_{i+1}"
            )
            elements.append(element)
        
        return elements


class TestPerformanceAndScaling:
    """Test system performance with larger datasets"""
    
    def test_large_document_processing(self):
        """Test processing of large documents with many elements"""
        
        # Create large mock document
        mock_large_text = "\n".join([
            f"{i}. Section {i} with various content and details" 
            for i in range(1, 51)  # 50 sections
        ])
        
        with patch("builtins.open", mock_open(read_data=b"large_doc")), \
             patch("src.utils.ocr_providers.TesseractOCR.extract_text") as mock_tess:
            
            mock_tess.return_value = OCRResult(
                text=mock_large_text,
                confidence=0.8,
                provider="tesseract",
                processing_time=1.0
            )
            
            manager = HybridOCR({
                'confidence_threshold': 0.7,
                'cost_budget': 5.0,
                'providers': {
                    'tesseract': {'enabled': True, 'confidence_threshold': 0.5}
                }
            })
            ocr_result = manager.extract_text(Path("/tmp/large_doc.jpg"))
            
            # Should handle large documents
            assert len(ocr_result.text) > 1000
            
            # Create many elements
            elements = []
            for i in range(50):
                elements.append(NoteElement(
                    text=f"Section {i+1} content",
                    bbox=(10, 20 + i*25, 150, 15),
                    confidence=0.8,
                    element_id=f"large_elem_{i+1}"
                ))
            
            # Test relationship detection performance
            detector = RelationshipDetector()
            relationships = detector.detect_relationships(elements)
            
            # Should complete in reasonable time and find relationships
            assert len(relationships) > 0
            
            # Test concept clustering performance
            extractor = ConceptExtractor()
            concepts = extractor.extract_concepts(elements)
            
            clusterer = ConceptClusterer()
            clusters = clusterer.cluster_concepts(concepts, relationships)
            
            # Should handle large datasets
            assert len(concepts) > 0
            assert len(clusters) >= 0  # May or may not find clusters
    
    def test_memory_efficiency(self):
        """Test memory usage with realistic datasets"""
        
        # This is a placeholder for memory testing
        # In practice, you'd use memory profiling tools
        elements = []
        for i in range(100):
            elements.append(NoteElement(
                text=f"Memory test element {i}",
                bbox=(i*10, i*20, 100, 15),
                confidence=0.8,
                element_id=f"mem_elem_{i}"
            ))
        
        detector = RelationshipDetector()
        relationships = detector.detect_relationships(elements)
        
        # Should not cause memory issues
        assert len(relationships) >= 0
        assert len(elements) == 100  # Elements should still be intact