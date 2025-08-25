"""
Tests for Relationship Detection in Handwritten Notes

Tests the relationship detector with realistic sample data representing
scattered handwritten thoughts that need organization.
"""

import pytest
from unittest.mock import MagicMock
import numpy as np

from src.utils.relationship_detector import (
    RelationshipDetector, NoteElement, Relationship, RelationshipType
)


class TestRelationshipDetector:
    """Test relationship detection algorithms"""
    
    def test_arrow_relationship_detection(self):
        """Test detection of arrow-based relationships"""
        
        detector = RelationshipDetector()
        
        # Create sample elements with arrows
        elements = [
            NoteElement("Task A → Task B", (10, 20, 80, 15), 0.9, "elem1"),
            NoteElement("Task B", (100, 20, 60, 15), 0.85, "elem2"),
            NoteElement("Process starts → next step", (10, 50, 120, 15), 0.88, "elem3"),
            NoteElement("next step", (140, 50, 70, 15), 0.82, "elem4")
        ]
        
        relationships = detector._detect_arrows(elements)
        
        # Should find arrow relationships
        assert len(relationships) > 0
        arrow_rels = [r for r in relationships if r.relationship_type == RelationshipType.ARROW]
        assert len(arrow_rels) >= 2
        
        # Verify relationship structure
        for rel in arrow_rels:
            assert rel.confidence > 0.0
            assert rel.source_id in ["elem1", "elem3"]
            assert rel.evidence.get('arrow_symbol') is not None
    
    def test_proximity_relationship_detection(self):
        """Test spatial proximity-based relationships"""
        
        detector = RelationshipDetector({'proximity_threshold': 50})
        
        # Create elements with varying distances
        elements = [
            NoteElement("Close item 1", (10, 20, 60, 15), 0.9, "close1"),
            NoteElement("Close item 2", (20, 30, 60, 15), 0.85, "close2"),  # Very close
            NoteElement("Far item", (200, 20, 50, 15), 0.88, "far1")  # Far away
        ]
        
        relationships = detector._detect_proximity(elements)
        
        # Should find proximity relationship between close items
        proximity_rels = [r for r in relationships if r.relationship_type == RelationshipType.PROXIMITY]
        assert len(proximity_rels) > 0
        
        # Close items should be connected
        close_rel = next(r for r in proximity_rels 
                        if (r.source_id == "close1" and r.target_id == "close2") or
                           (r.source_id == "close2" and r.target_id == "close1"))
        assert close_rel.confidence > 0.7  # Reasonable confidence for close items
    
    def test_hierarchy_relationship_detection(self):
        """Test hierarchical structure detection"""
        
        detector = RelationshipDetector()
        
        # Create hierarchical note elements
        elements = [
            NoteElement("1. Main topic", (10, 20, 80, 15), 0.9, "main1"),
            NoteElement("   a. Subtopic A", (20, 40, 90, 15), 0.85, "sub1"),
            NoteElement("   b. Subtopic B", (20, 60, 90, 15), 0.88, "sub2"),
            NoteElement("2. Second topic", (10, 80, 90, 15), 0.82, "main2"),
            NoteElement("   • Bullet point", (20, 100, 80, 15), 0.87, "bullet1")
        ]
        
        relationships = detector._detect_hierarchy(elements)
        
        # Should find hierarchical relationships
        hierarchy_rels = [r for r in relationships if r.relationship_type == RelationshipType.HIERARCHY]
        assert len(hierarchy_rels) >= 2  # Should find main topic -> subtopic relationships
        
        # Verify parent-child relationships
        main1_children = [r for r in hierarchy_rels if r.source_id == "main1"]
        assert len(main1_children) >= 2  # Should have subtopics as children
    
    def test_sequence_relationship_detection(self):
        """Test sequence and temporal relationships"""
        
        detector = RelationshipDetector()
        
        elements = [
            NoteElement("First, analyze the problem", (10, 20, 120, 15), 0.9, "step1"),
            NoteElement("Then, design solution", (10, 40, 110, 15), 0.85, "step2"),  
            NoteElement("Finally, implement and test", (10, 60, 130, 15), 0.88, "step3"),
            NoteElement("Step 1: Research", (150, 20, 80, 15), 0.82, "research")
        ]
        
        relationships = detector._detect_sequences(elements)
        
        # Should find sequence relationships
        sequence_rels = [r for r in relationships if r.relationship_type == RelationshipType.SEQUENCE]
        assert len(sequence_rels) > 0
        
        # Verify sequence indicators are detected
        for rel in sequence_rels:
            assert rel.evidence.get('sequence_indicator') is not None
            assert rel.confidence > 0.5
    
    def test_grouping_relationship_detection(self):
        """Test visual grouping relationships"""
        
        detector = RelationshipDetector()
        
        elements = [
            NoteElement("[Important points]", (10, 20, 100, 15), 0.9, "group1"),
            NoteElement("Point A inside brackets", (20, 40, 120, 15), 0.85, "pointA"),
            NoteElement('"Quoted section"', (10, 80, 90, 15), 0.88, "quote1"),
            NoteElement("Text in quotes", (20, 100, 80, 15), 0.82, "quoted_text")
        ]
        
        relationships = detector._detect_grouping(elements)
        
        # Should find grouping relationships  
        grouping_rels = [r for r in relationships if r.relationship_type == RelationshipType.GROUPING]
        assert len(grouping_rels) > 0
        
        # Verify grouping patterns are detected
        for rel in grouping_rels:
            assert rel.evidence.get('pattern') is not None
    
    def test_complete_relationship_detection_pipeline(self):
        """Test complete relationship detection on realistic note data"""
        
        detector = RelationshipDetector({
            'proximity_threshold': 60
        })
        
        # Simulate handwritten meeting notes with various relationship types
        elements = [
            # Main agenda items (hierarchy)
            NoteElement("1. Project Update", (10, 20, 90, 15), 0.9, "agenda1"),
            NoteElement("   - Status: On track", (25, 40, 100, 15), 0.85, "status1"),
            NoteElement("   - Next: Deploy → Testing", (25, 60, 140, 15), 0.88, "next1"),
            
            # Connected ideas (arrows and proximity)
            NoteElement("Testing", (170, 60, 50, 15), 0.82, "testing"),
            NoteElement("Bug fixes needed first", (170, 80, 110, 15), 0.87, "bugfix"),
            
            # Action items (sequence)
            NoteElement("TODO: First review code", (10, 120, 110, 15), 0.91, "todo1"),
            NoteElement("Then schedule deployment", (10, 140, 120, 15), 0.89, "todo2"),
            
            # Grouped notes  
            NoteElement("[Key Decisions]", (200, 20, 90, 15), 0.88, "decisions"),
            NoteElement("Decision 1: Use new framework", (210, 40, 130, 15), 0.85, "dec1")
        ]
        
        # Run complete detection pipeline
        relationships = detector.detect_relationships(elements)
        
        # Should find multiple relationship types
        assert len(relationships) > 0
        
        relationship_types = {r.relationship_type for r in relationships}
        expected_types = {
            RelationshipType.HIERARCHY, 
            RelationshipType.ARROW,
            RelationshipType.PROXIMITY,
            RelationshipType.SEQUENCE
        }
        
        # Should detect most expected relationship types
        assert len(relationship_types & expected_types) >= 3
        
        # Verify relationships are sorted by confidence
        confidences = [r.confidence for r in relationships]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_relationship_clustering(self):
        """Test clustering of related elements"""
        
        detector = RelationshipDetector()
        
        elements = [
            NoteElement("Machine Learning", (10, 20, 80, 15), 0.9, "ml1"),
            NoteElement("Neural Networks", (100, 20, 90, 15), 0.85, "nn1"), 
            NoteElement("Deep Learning", (10, 40, 80, 15), 0.88, "dl1"),
            NoteElement("Cooking Recipe", (200, 20, 80, 15), 0.82, "cook1"),
            NoteElement("Ingredients", (200, 40, 70, 15), 0.87, "ingr1")
        ]
        
        relationships = [
            Relationship("ml1", "nn1", RelationshipType.PROXIMITY, 0.8),
            Relationship("ml1", "dl1", RelationshipType.PROXIMITY, 0.9), 
            Relationship("nn1", "dl1", RelationshipType.SIMILARITY, 0.85),
            Relationship("cook1", "ingr1", RelationshipType.HIERARCHY, 0.7)
        ]
        
        clusters = detector.find_clusters(elements, relationships)
        
        # Should find coherent clusters
        assert len(clusters) >= 2
        
        # ML-related cluster should exist
        ml_cluster = None
        cooking_cluster = None
        
        for cluster in clusters:
            if "ml1" in cluster:
                ml_cluster = cluster
            if "cook1" in cluster:
                cooking_cluster = cluster
        
        assert ml_cluster is not None
        assert len(ml_cluster) >= 3  # Should include ML, NN, DL
        assert cooking_cluster is not None
        assert len(cooking_cluster) >= 2  # Should include cooking, ingredients


class TestRelationshipTypes:
    """Test relationship type classification and scoring"""
    
    def test_arrow_direction_detection(self):
        """Test arrow direction affects relationship scoring"""
        
        detector = RelationshipDetector()
        
        # Right-pointing arrow with target to the right (good match)
        source_right = NoteElement("Start →", (10, 20, 50, 15), 0.9, "src1")  
        target_right = NoteElement("End", (70, 20, 40, 15), 0.85, "tgt1")
        
        rel_right = detector._create_arrow_relationship(
            source_right, target_right, 
            detector.arrow_patterns[0]  # Right arrow pattern
        )
        
        # Left-pointing arrow with target to the right (bad spatial match)
        source_left = NoteElement("Start ←", (10, 40, 50, 15), 0.9, "src2")  # Arrow points left
        target_left = NoteElement("End", (70, 40, 40, 15), 0.85, "tgt2")     # But target is to the right  
        
        # Find a left arrow pattern
        left_pattern = None
        for pattern in detector.arrow_patterns:
            if pattern.search("←"):
                left_pattern = pattern
                break
        
        rel_left = detector._create_arrow_relationship(
            source_left, target_left,
            left_pattern  # Left arrow pattern 
        )
        
        # Good spatial match should have higher confidence
        assert rel_right.confidence > rel_left.confidence
    
    def test_hierarchy_level_calculation(self):
        """Test hierarchy level detection accuracy"""
        
        detector = RelationshipDetector()
        
        test_cases = [
            ("1. Main point", 1),
            ("  a. Sub point", 2),  # 2 spaces + letter = level 2 
            ("      • Detail", 2),  # 6 spaces + bullet = max(1, 2) = 2
            ("No indentation", 0),
            ("  - Bullet", 1),      # 2 spaces + bullet = max(1, 1) = 1
            ("        Deep indent", 3)  # 8+ spaces = level 3
        ]
        
        for text, expected_level in test_cases:
            element = NoteElement(text, (10, 20, 80, 15), 0.9, "test")
            level = detector._determine_hierarchy_level(element)
            assert level == expected_level, f"'{text}' should be level {expected_level}, got {level}"
    
    def test_proximity_distance_calculation(self):
        """Test spatial distance calculations"""
        
        detector = RelationshipDetector()
        
        # Test known distances
        bbox1 = (0, 0, 10, 10)    # Center at (5, 5)
        bbox2 = (20, 0, 10, 10)   # Center at (25, 5)
        
        distance = detector._calculate_distance(bbox1, bbox2)
        expected_distance = 20.0  # 25 - 5 = 20
        
        assert abs(distance - expected_distance) < 0.1
        
        # Test diagonal distance
        bbox3 = (0, 0, 10, 10)    # Center at (5, 5) 
        bbox4 = (30, 40, 10, 10)  # Center at (35, 45)
        
        diagonal_distance = detector._calculate_distance(bbox3, bbox4)
        expected_diagonal = np.sqrt(30**2 + 40**2)  # Pythagorean theorem
        
        assert abs(diagonal_distance - expected_diagonal) < 0.1


class TestRelationshipDeduplication:
    """Test relationship deduplication and quality filtering"""
    
    def test_duplicate_relationship_removal(self):
        """Test removal of duplicate relationships"""
        
        detector = RelationshipDetector()
        
        # Create duplicate relationships
        relationships = [
            Relationship("A", "B", RelationshipType.PROXIMITY, 0.8),
            Relationship("A", "B", RelationshipType.PROXIMITY, 0.6),  # Duplicate, lower confidence
            Relationship("B", "C", RelationshipType.ARROW, 0.9),
            Relationship("A", "B", RelationshipType.ARROW, 0.7),      # Different type, should keep
        ]
        
        deduplicated = detector._deduplicate_relationships(relationships)
        
        # Should keep highest confidence of each type
        assert len(deduplicated) == 3  # Remove one duplicate proximity
        
        # Check that highest confidence proximity was kept
        proximity_rels = [r for r in deduplicated 
                         if r.relationship_type == RelationshipType.PROXIMITY]
        assert len(proximity_rels) == 1
        assert proximity_rels[0].confidence == 0.8
    
    def test_relationship_graph_generation(self):
        """Test conversion of relationships to graph structure"""
        
        detector = RelationshipDetector()
        
        relationships = [
            Relationship("A", "B", RelationshipType.ARROW, 0.8),
            Relationship("B", "C", RelationshipType.PROXIMITY, 0.7),
            Relationship("A", "C", RelationshipType.HIERARCHY, 0.9),
            Relationship("D", "E", RelationshipType.SEQUENCE, 0.6)
        ]
        
        graph = detector.get_relationship_graph(relationships)
        
        # Verify graph structure
        assert "A" in graph
        assert "B" in graph["A"]
        assert "C" in graph["A"] 
        assert "C" in graph["B"]
        assert "E" in graph["D"]
        
        # Isolated nodes should not be in graph if they're not sources
        assert len(graph["A"]) == 2  # Points to B and C