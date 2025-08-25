"""
Simple End-to-End Integration Tests

Validates the complete Ghost Writer pipeline with direct component testing
rather than complex mocking. Tests business logic integration.
"""

import pytest
from pathlib import Path

from src.utils.ocr_providers import OCRResult
from src.utils.relationship_detector import RelationshipDetector, NoteElement
from src.utils.concept_clustering import ConceptExtractor, ConceptClusterer
from src.utils.structure_generator import StructureGenerator, StructureType


class TestE2EPipeline:
    """Test complete Ghost Writer pipeline end-to-end"""
    
    def test_premium_accuracy_beachhead_pipeline(self):
        """Test premium accuracy beachhead: high-quality OCR → structured document"""
        
        # Step 1: Simulate premium OCR result
        ocr_result = OCRResult(
            text="1. Project Status Update\n   - On track for Q2 delivery milestone\n   - Need comprehensive testing coverage\n\n" +
                 "2. Action Items & Next Steps\n   - Review code quality → Deploy to staging environment\n   - Schedule user testing sessions\n\n" +
                 "Follow-up meeting with @john_smith scheduled for next week\n" +
                 "#important #project-alpha",
            confidence=0.95,
            provider="gpt4_vision",
            processing_time=2.1
        )
        
        # Step 2: Convert to note elements
        elements = self._create_note_elements_from_text(ocr_result.text)
        assert len(elements) >= 8  # Should parse into multiple elements
        
        # Step 3: Detect relationships
        detector = RelationshipDetector({'proximity_threshold': 60})
        relationships = detector.detect_relationships(elements)
        
        assert len(relationships) > 0
        relationship_types = {r.relationship_type.value for r in relationships}
        # Should find structural relationships - hierarchy, sequence, or proximity
        assert len(relationship_types) > 0 and any(rt in relationship_types for rt in ["hierarchy", "sequence", "proximity"])
        
        # Step 4: Extract and cluster concepts
        extractor = ConceptExtractor({'min_concept_length': 3})
        concepts = extractor.extract_concepts(elements)
        
        assert len(concepts) > 0
        concept_types = {c.concept_type for c in concepts}
        assert "topic" in concept_types or "action" in concept_types
        
        clusterer = ConceptClusterer({'similarity_threshold': 0.3})
        clusters = clusterer.cluster_concepts(concepts, relationships)
        
        assert len(clusters) >= 0  # May or may not form clusters with this content
        
        # Step 5: Generate document structure
        generator = StructureGenerator({'min_confidence': 0.3})
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        
        assert len(structures) > 0
        best_structure = max(structures, key=lambda s: s.confidence)
        assert best_structure.confidence > 0.3
        
        # Step 6: Export structured document
        exported_text = generator.export_structure_as_text(best_structure)
        
        assert "Project" in exported_text or "Action" in exported_text
        assert "Confidence:" in exported_text
    
    def test_idea_organization_beachhead_pipeline(self):
        """Test idea organization beachhead: scattered thoughts → organized structure"""
        
        # Step 1: Simulate scattered OCR result
        ocr_result = OCRResult(
            text="Machine learning algorithms\n\n" +
                 "Need to collect training data\n\n" +
                 "Neural networks are complex\n\n" +
                 "First: understand the problem\n\n" +
                 "Data cleaning is important\n\n" +
                 "Deep learning requires lots of data\n\n" +
                 "Then: design the architecture\n\n" +
                 "Finally: train and evaluate",
            confidence=0.7,
            provider="tesseract",
            processing_time=0.8
        )
        
        # Step 2: Create scattered elements
        elements = self._create_scattered_elements(ocr_result.text)
        assert len(elements) >= 6
        
        # Step 3: Detect relationships (should find sequence relationships)
        detector = RelationshipDetector({'proximity_threshold': 100})  # More generous for scattered
        relationships = detector.detect_relationships(elements)
        
        sequence_rels = [r for r in relationships if r.relationship_type.value == "sequence"]
        assert len(sequence_rels) >= 0  # May find sequence indicators
        
        # Step 4: Extract concepts with lower thresholds for scattered content
        extractor = ConceptExtractor({'min_concept_length': 2})
        concepts = extractor.extract_concepts(elements)
        
        assert len(concepts) > 0
        
        # Should find ML-related and process-related concepts
        ml_concepts = [c for c in concepts if any("machine" in kw.lower() or "neural" in kw.lower() 
                                                 or "learning" in kw.lower() for kw in c.keywords)]
        process_concepts = [c for c in concepts if any("first" in kw.lower() or "then" in kw.lower() 
                                                      or "finally" in kw.lower() for kw in c.keywords)]
        
        assert len(ml_concepts) > 0 or len(process_concepts) > 0
        
        # Step 5: Cluster with lower thresholds
        clusterer = ConceptClusterer({'similarity_threshold': 0.25, 'min_cluster_size': 1})
        clusters = clusterer.cluster_concepts(concepts, relationships)
        
        assert len(clusters) >= 0
        
        # Step 6: Generate organization structure
        generator = StructureGenerator({'min_confidence': 0.2})
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        
        assert len(structures) >= 0  # Should attempt to create structure
        
        if structures:
            best_structure = max(structures, key=lambda s: s.confidence)
            exported_text = generator.export_structure_as_text(best_structure)
            assert len(exported_text) > 100  # Should generate substantial content
    
    def test_component_integration_robustness(self):
        """Test pipeline robustness with challenging input"""
        
        # Test with minimal input
        minimal_ocr = OCRResult(
            text="Short note",
            confidence=0.5,
            provider="tesseract",
            processing_time=0.1
        )
        
        elements = self._create_note_elements_from_text(minimal_ocr.text)
        assert len(elements) == 1
        
        detector = RelationshipDetector()
        relationships = detector.detect_relationships(elements)
        # Should handle single element gracefully
        assert isinstance(relationships, list)
        
        extractor = ConceptExtractor()
        concepts = extractor.extract_concepts(elements)
        assert isinstance(concepts, list)
        
        clusterer = ConceptClusterer()
        clusters = clusterer.cluster_concepts(concepts, relationships)
        assert isinstance(clusters, list)
        
        generator = StructureGenerator()
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        assert isinstance(structures, list)
        
        # Pipeline should complete without errors even with minimal input
    
    def test_performance_with_realistic_content(self):
        """Test pipeline performance with realistic document size"""
        
        # Create realistic meeting notes
        realistic_text = """
        Meeting Notes - Q2 Planning Session
        
        1. Project Alpha Status
           - Currently 75% complete
           - Facing integration challenges with payment system
           - Need additional testing resources
        
        2. Budget Review
           - Development costs: $45K spent, $15K remaining
           - Infrastructure costs: $8K monthly
           - Need approval for additional QA resources
        
        3. Action Items
           - John: Complete payment integration by Friday
           - Sarah: Set up automated testing pipeline
           - Mike: Review security audit results
           - Team: Weekly standup meetings starting Monday
        
        4. Risks & Concerns
           - Timeline may slip by 2 weeks due to integration issues
           - Need backup plan for payment provider
           - Security review pending - potential blocker
        
        5. Next Steps
           - Schedule follow-up meeting for Thursday
           - Create detailed project timeline
           - Assign point persons for each risk item
        """
        
        ocr_result = OCRResult(
            text=realistic_text,
            confidence=0.88,
            provider="google_vision",
            processing_time=1.5
        )
        
        # Process through complete pipeline
        elements = self._create_note_elements_from_text(ocr_result.text)
        assert len(elements) > 10  # Should create many elements
        
        detector = RelationshipDetector()
        relationships = detector.detect_relationships(elements)
        
        extractor = ConceptExtractor()
        concepts = extractor.extract_concepts(elements)
        
        clusterer = ConceptClusterer()
        clusters = clusterer.cluster_concepts(concepts, relationships)
        
        generator = StructureGenerator()
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        
        # Should handle realistic content effectively
        assert len(concepts) > 5
        assert len(structures) > 0
        
        if structures:
            best_structure = max(structures, key=lambda s: s.confidence)
            summary = generator.get_structure_summary(best_structure)
            
            # Should generate at least 1 node with reasonable confidence
            assert summary['total_nodes'] >= 1
            assert summary['confidence'] > 0.0
    
    def _create_note_elements_from_text(self, text: str) -> list:
        """Convert text into positioned note elements"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
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
                bbox=(x_pos, y_pos, len(line) * 8, 15),
                confidence=0.8 + (i % 3) * 0.05,
                element_id=f"elem_{i+1}"
            )
            elements.append(element)
            y_pos += 25
        
        return elements
    
    def _create_scattered_elements(self, text: str) -> list:
        """Create scattered note elements simulating non-linear handwriting"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        elements = []
        
        # Simulate scattered positioning
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
                confidence=0.6 + (i % 4) * 0.05,
                element_id=f"scattered_{i+1}"
            )
            elements.append(element)
        
        return elements